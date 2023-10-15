import json
import os

import psycopg2
import pika

directory = os.path.dirname(__file__)
ADD_TO_NEW_ARTIFACTS_FILEPATH = os.path.join(directory, '../sql/add_to_new_artifacts')

class NewArtifactChecker:
    channel = None
    pool = None
    conn_user = None
    conn_pass = None
    conn_host = None
    conn_port = None
    conn_db = None
    def __init__(self):
        self.conn_user = os.getenv('CONNECTION_USER')
        self.conn_pass = os.getenv('CONNECTION_PASS')
        self.conn_host = os.getenv('CONNECTION_HOST')
        self.conn_port = os.getenv('CONNECTION_PORT')
        self.conn_db = os.getenv('CONNECTION_DB')
        self.pool = psycopg2.pool.SimpleConnectionPool(
            1, 2, user=self.conn_user, password=self.conn_pass,
            host=self.conn_host, port=self.conn_port, database=self.conn_db)

    def callback(self, ch, method, properties, body):
        body = json.loads(body)
        conn = self.pool.getconn()
        cur = conn.cursor()
        file = open(ADD_TO_NEW_ARTIFACTS_FILEPATH).read()
        cur.execute(file, (body['museum_id'], body['museum_artifact_id'], False))
        conn.commit()
        cur.close()
        self.pool.putconn(conn)

    def start_listener(self):
        pika_conn = pika.BlockingConnection(pika.ConnectionParameters(host=os.getenv('PIKA_HOST')))
        self.channel = pika_conn.channel()
        self.channel.queue_declare(queue='artifacts')
        self.channel.basic_consume(queue='artifacts', on_message_callback=self.callback, auto_ack=True)
        self.channel.start_consuming()

    def stop_listener(self):
        self.channel.stop_consuming()