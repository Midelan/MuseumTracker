#!/usr/bin/env python3
import json
import os

import psycopg2
import psycopg2.pool
import requests

from datetime import datetime

harvard_api_address = 'https://api.harvardartmuseums.org'
harvard_galleries_endpoint = '/gallery'
harvard_objects_endpoint = '/object'
harvard_api_key = os.getenv('HARVARD_API_KEY')
harvard_size_100 = '&size=100'

directory = os.path.dirname(__file__)
ADD_TO_ARTIFACTS_FILEPATH = os.path.join(directory, '../sql/add_artifact_to_table')

conn_user = os.getenv('CONNECTION_USER')
conn_pass = os.getenv('CONNECTION_PASS')
conn_host = os.getenv('CONNECTION_HOST')
conn_port = os.getenv('CONNECTION_PORT')
conn_db = os.getenv('CONNECTION_DB')
pool = psycopg2.pool.SimpleConnectionPool(
    1, 2, user=conn_user, password=conn_pass,
    host=conn_host, port=conn_port, database=conn_db)

def api_controller():
    query_run_time = datetime.now()
    harvard_api_controller(query_run_time)


def harvard_api_controller(query_run_time, url = None):
    if url is not None:
        galleries_url = url
    else:
        galleries_url = harvard_api_address + harvard_galleries_endpoint + harvard_api_key + harvard_size_100
    objects_url = harvard_api_address + harvard_objects_endpoint + harvard_api_key + harvard_size_100

    try:
        galleries_response = requests.get(galleries_url).json()
    except:
        print('Failed to get galleries due to API outage, will retry tomorrow')
        return

    galleries = galleries_response['records']
    for record in galleries:
        get_harvard_objects(query_run_time, record['name'], objects_url + '&gallery=' + record['gallerynumber'])
    if('next' in galleries_response['info']):
        harvard_api_controller(query_run_time, galleries_response['info']['next'])


def get_harvard_objects(query_run_time, gallery_id, objects_url):
    file = open(ADD_TO_ARTIFACTS_FILEPATH).read()

    try:
        objects_response = requests.get(objects_url).json()
    except:
        print('Failed to get artifacts in gallery '+gallery_id+', skipping, will retry tomorrow')
        return

    objects = objects_response['records']
    for record in objects:
        title = record['title']
        museum_artifact_id = record['objectid']
        new_artifact_id = 'Failed to add'
        image_url = record['url']
        try:
            conn = pool.getconn()
            cur = conn.cursor()
            cur.execute(file, (gallery_id, title, image_url, 1, museum_artifact_id))
            new_artifact_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            pool.putconn(conn)
        except:
            try:
                pool.putconn(conn)
                cur.close()
            except:
                pass
        print('Added artifact ID ' + str(new_artifact_id))
    if('next' in objects_response['info']):
        get_harvard_objects(query_run_time, gallery_id, objects_response['info']['next'])
