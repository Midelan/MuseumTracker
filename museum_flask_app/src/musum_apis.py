#!/usr/bin/env python3
import json
import os

import psycopg2
import psycopg2.pool
import requests
import pika

from datetime import datetime

harvard_api_address = 'https://api.harvardartmuseums.org'
harvard_galleries_endpoint = '/gallery'
harvard_objects_endpoint = '/object'
harvard_size_100 = '&size=100'

directory = os.path.dirname(__file__)
ADD_TO_ARTIFACTS_FILEPATH = os.path.join(directory, '../sql/add_artifact_to_table')

class APIController:
    pool = None
    conn_user = None
    conn_pass = None
    conn_host = None
    conn_port = None
    conn_db = None
    harvard_api_key = None
    channel = None
    def __init__(self):
        pass

    def start(self, datetime_input = None):
        self.conn_user = os.getenv('CONNECTION_USER')
        self.conn_pass = os.getenv('CONNECTION_PASS')
        self.conn_host = os.getenv('CONNECTION_HOST')
        self.conn_port = os.getenv('CONNECTION_PORT')
        self.conn_db = os.getenv('CONNECTION_DB')
        self.harvard_api_key = os.getenv('HARVARD_API_KEY')
        self.pool = psycopg2.pool.SimpleConnectionPool(
            1, 2, user=self.conn_user, password=self.conn_pass,
            host=self.conn_host, port=self.conn_port, database=self.conn_db)
        if(datetime_input == None):
            query_run_time = datetime.now()
        else:
            query_run_time = datetime_input
        pika_conn = pika.BlockingConnection(pika.ConnectionParameters(os.getenv('PIKA_HOST')))
        self.channel = pika_conn.channel()
        self.channel.queue_declare(queue='artifacts')
        self.harvard_api_controller(query_run_time)
        conn = self.pool.getconn()
        cur = conn.cursor()
        cur.execute('DELETE FROM artifacts WHERE date_queried != %s', (query_run_time,))
        conn.commit()
        cur.close()
        self.pool.putconn(conn)



    def harvard_api_controller(self, query_run_time, url = None):
        if url is not None:
            galleries_url = url
        else:
            galleries_url = harvard_api_address + harvard_galleries_endpoint + self.harvard_api_key + harvard_size_100
        objects_url = harvard_api_address + harvard_objects_endpoint + self.harvard_api_key + harvard_size_100

        try:
            galleries_response = requests.get(galleries_url).json()
        except:
            print('Failed to get galleries due to API outage, will retry tomorrow')
            return

        galleries = galleries_response['records']
        for record in galleries:
            self.get_harvard_objects(query_run_time, record['name'], objects_url + '&gallery=' + record['gallerynumber'])
        if('next' in galleries_response['info']):
            self.harvard_api_controller(query_run_time, galleries_response['info']['next'])


    def get_harvard_objects(self, query_run_time, gallery_id, objects_url):
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
                conn = self.pool.getconn()
                cur = conn.cursor()
                cur.execute(file, (gallery_id, title, image_url, 1, museum_artifact_id, query_run_time))
                new_artifact_id = cur.fetchone()[0]
                conn.commit()
                cur.close()
                self.pool.putconn(conn)
            except:
                try:
                    self.pool.putconn(conn)
                    cur.close()
                except:
                    pass
            self.publish_to_queue(museum_artifact_id, 1, query_run_time)
            print('Added artifact ID ' + str(new_artifact_id))
        if('next' in objects_response['info']):
            self.get_harvard_objects(query_run_time, gallery_id, objects_response['info']['next'])

    def publish_to_queue(self, museum_artifact_id, museum_id, query_run_time):
        timestamp = query_run_time.strftime("%Y-%m-%d %H:%M:%S")
        self.channel.basic_publish(exchange='', routing_key='artifacts',
           body=json.dumps({
               "museum_artifact_id": museum_artifact_id,
               "museum_id": museum_id,
               "query_run_time": timestamp
           }))
