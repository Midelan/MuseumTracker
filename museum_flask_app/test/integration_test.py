import os
import unittest

import psycopg2
import pytest
import testing.postgresql
from sqlalchemy import create_engine
from unittest import mock

from museum_flask_app.src.musum_apis import APIController
from museum_flask_app.src.database_setup import MigrationManager

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
        os.environ["HARVARD_API_KEY"] = 'fake_api_key'
        migrator = MigrationManager()
        migrator.migration_manager()
        api_controller = APIController()
        api_controller.start()

        validation_cursor = TestIntegation.db.cursor()
        validation_cursor.execute('SELECT * FROM artifacts')
        results = validation_cursor.fetchall()
        TestIntegation.pg.stop()

        expected = [
            (1, 100000, 1, 'Mocked Gallery 1', 'Mocked Vase', 'mockedvaseurl', None, None),
            (2, 100001, 1, 'Mocked Gallery 1', 'Mocked Painting', 'mockedpaintingurl', None, None),
            (3, 100002, 1, 'Mocked Gallery 1', 'Mocked Beads', 'mockedbeadsurl', None, None),
            (4, 100003, 1, 'Mocked Gallery 2', 'Mocked Sculpture', 'mockedsculptureurl', None, None),
            (5, 100004, 1, 'Mocked Gallery 3', 'Mocked Sketch', 'mockedsketchurl', None, None)
        ]
        assert(results == expected)