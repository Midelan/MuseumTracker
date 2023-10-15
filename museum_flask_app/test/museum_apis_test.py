import os
import unittest
from unittest import mock
from datetime import datetime

import pytest

from museum_flask_app.src.museum_apis import APIController


class TestMuseumAPIs:

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

    def mock_pool(minconn, maxconn, user, password, host, port, database):
        class MockCursor:
            def __init__(self):
                pass

            def execute(self, file, params):
                pass

            def close(self):
                pass

        class MockConnection:
            def __init__(self):
                pass

            def cursor(self):
                return MockCursor()

            def commit(self):
                return

        class MockPool:

            def __init__(self):
                pass

            def getconn(self):
                return MockConnection()

            def putconn(self, connection):
                pass

        return MockPool()

    def mock_channel(self):
        class MockChannel:

            def __init__(self):
                pass

            def queue_declare(self, queue):
                pass

        class MockConnection:

            def __init__(self):
                pass

            def channel(self):
                return MockChannel()

        return MockConnection()


    def mock_harvard_objects(run_time, gallery, url):
        return

    def mock_publish_to_queue(museum_artifact_id, museum_id, query_run_time):
        return

    @mock.patch('museum_flask_app.src.musum_apis.requests.get', side_effect=mock_requests)
    @mock.patch('museum_flask_app.src.musum_apis.APIController.get_harvard_objects', side_effect=mock_harvard_objects)
    @mock.patch('museum_flask_app.src.musum_apis.psycopg2.pool.SimpleConnectionPool', side_effect=mock_pool)
    @mock.patch('museum_flask_app.src.musum_apis.pika.BlockingConnection', side_effect=mock_channel)
    def test_gallery(self, mock_channel, mock_connection_pool, mock_harvard_objects, mock_requests):
        os.environ["HARVARD_API_KEY"] = 'fake_api_key'
        os.environ["PIKA_HOST"] = 'fake_host'
        api_controller = APIController()
        api_controller.start()
        assert(mock_harvard_objects.call_count == 3)
        assert(mock_requests.call_count == 2)

    @mock.patch('museum_flask_app.src.musum_apis.APIController.publish_to_queue', side_effect=mock_publish_to_queue)
    @mock.patch('museum_flask_app.src.musum_apis.requests.get', side_effect=mock_requests)
    @mock.patch('museum_flask_app.src.musum_apis.psycopg2.pool.SimpleConnectionPool', side_effect=mock_pool)
    @mock.patch('museum_flask_app.src.musum_apis.pika.BlockingConnection', side_effect=mock_channel)
    def test_objects(self, mock_channel, mock_connection_pool, mock_requests, mock_publish):
        os.environ["HARVARD_API_KEY"] = 'fake_api_key'
        os.environ["PIKA_HOST"] = 'fake_host'
        time = datetime(2014, 5, 12, 23, 30, 12, 134)
        api_controller = APIController()
        api_controller.get_harvard_objects(time, 1, '1000')
        assert(mock_requests.call_count == 2)