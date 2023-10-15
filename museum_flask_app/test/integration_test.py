import os
import time
import unittest
from datetime import datetime

import psycopg2
import pytest
import pika
import threading
import testing.postgresql
from sqlalchemy import create_engine
from unittest import mock

from museum_flask_app.src.musum_apis import APIController
from museum_flask_app.src.database_setup import MigrationManager
from museum_flask_app.src.new_artifact_check import NewArtifactChecker

artifacts_added = []

class TestIntegation:
    pg = testing.postgresql.Postgresql()
    create_engine(pg.url())
    db = psycopg2.connect(**pg.dsn())

    def mock_pool(minconn, maxconn, user, password, host, port, database):
        class MockPool:

            def __init__(self):
                pass

            def getconn(self):
                return TestIntegation.db

            def putconn(self, connection):
                pass

        return MockPool()

    def mock_requests(url):

        class MockResponse:

            def __init__(self):
                pass

            def json(self):
                if('/gallery' in url):
                    return {
                        'info': {
                            'next': '/nextgalleryurl'
                        },
                        'records': [
                            {'name': 'Mocked Gallery 1', 'gallerynumber': '1000'},
                            {'name': 'Mocked Gallery 2', 'gallerynumber': '1001'}
                        ]}
                elif('/nextgalleryurl' in url):
                    return {
                        'info': {},
                        'records': [
                            {'name': 'Mocked Gallery 3', 'gallerynumber': '1002'}
                        ]}
                elif('1000' in url):
                    return {
                        'info': {
                            'next': '/nextobjecturl'
                        },
                        'records': [
                            {'title': 'Mocked Vase', 'objectid': 100000, 'url': 'mockedvaseurl'},
                            {'title': 'Mocked Painting', 'objectid': 100001, 'url': 'mockedpaintingurl'}
                        ]}
                elif('/nextobjecturl' in url):
                    return {
                        'info': {},
                        'records': [
                            {'title': 'Mocked Beads', 'objectid': 100002, 'url': 'mockedbeadsurl'}
                        ]}
                elif('1001' in url):
                    return {
                        'info': {},
                        'records': [
                            {'title': 'Mocked Sculpture', 'objectid': 100003, 'url': 'mockedsculptureurl'}
                        ]}
                elif('1002' in url):
                    return {
                        'info': {},
                        'records': [
                            {'title': 'Mocked Sketch', 'objectid': 100004, 'url': 'mockedsketchurl'}
                        ]}
                else:
                    raise Exception('Test Connection Failure Exception')

        return MockResponse()

    def mock_connection(self, sslmode):
        connection = TestIntegation.db
        return connection

    @mock.patch('museum_flask_app.src.database_setup.psycopg2.connect', side_effect=mock_connection)
    @mock.patch('museum_flask_app.src.musum_apis.psycopg2.pool.SimpleConnectionPool', side_effect=mock_pool)
    @mock.patch('museum_flask_app.src.musum_apis.requests.get', side_effect=mock_requests)
    def test_integration(self, requests_mocker, pool_mocker, connection_mocker):
        test_run_time = datetime.now()
        os.environ["HARVARD_API_KEY"] = 'fake_api_key'
        migrator = MigrationManager()
        migrator.migration_manager()
        validation_cursor = TestIntegation.db.cursor()
        validation_cursor.execute('INSERT INTO users VALUES (\'testuser\', \'testpassword\')')
        validation_cursor.execute('INSERT INTO users VALUES (\'testuser2\', \'testpassword2\')')
        validation_cursor.execute(
            '''INSERT INTO artifacts (museum_artifact_id, museum_id, gallery_id, title, image_url, date_queried)
            VALUES (100100, 1, \'outdatedGallery\', \'outdatedArtifact\', \'outdatedArtifactURL\', %s)''',
            (test_run_time,))
        validation_cursor.execute('INSERT INTO new_artifacts VALUES (\'testuser2\', 1, \'100000\', True)')
        TestIntegation.db.commit()
        validation_cursor.execute('SELECT * FROM artifacts')
        start_results = validation_cursor.fetchall()
        print('Initial Table')
        print(start_results)
        api_controller = APIController()
        test_second_run_time = datetime.now()
        api_controller.start(test_second_run_time)

        validation_cursor.execute('SELECT * FROM artifacts')
        results = validation_cursor.fetchall()
        checker = NewArtifactChecker()
        thread = threading.Thread(target=checker.start_listener)
        thread.start()

        pika_conn = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = pika_conn.channel()
        queue_full = True
        time.sleep(1)
        while queue_full:
            queue = channel.queue_declare(queue='artifacts', passive=True)
            if(queue.method.message_count == 0):
                queue_full = False

        validation_cursor.execute('SELECT * FROM artifacts')
        new_results = validation_cursor.fetchall()
        print('Final Table')
        print(new_results)
        validation_cursor.execute('SELECT * FROM new_artifacts')
        junction_results = validation_cursor.fetchall()
        print('Junction Table')
        print(junction_results)
        TestIntegation.pg.stop()

        expected = [
            (2, 100000, 1, 'Mocked Gallery 1', 'Mocked Vase', 'mockedvaseurl', test_second_run_time, None),
            (3, 100001, 1, 'Mocked Gallery 1', 'Mocked Painting', 'mockedpaintingurl', test_second_run_time, None),
            (4, 100002, 1, 'Mocked Gallery 1', 'Mocked Beads', 'mockedbeadsurl', test_second_run_time, None),
            (5, 100003, 1, 'Mocked Gallery 2', 'Mocked Sculpture', 'mockedsculptureurl', test_second_run_time, None),
            (6, 100004, 1, 'Mocked Gallery 3', 'Mocked Sketch', 'mockedsketchurl', test_second_run_time, None)
        ]
        assert(results == expected)

        checker.stop_listener()