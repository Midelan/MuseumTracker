#!/usr/bin/env python3

import os
import psycopg2

directory = os.path.dirname(__file__)
MIGRATION_FILEPATH = os.path.join(directory, '../migrations')
INITIAL_MIGRATION = '00_migration_setup'

conn_string = os.getenv('CONNECTION_STRING')
conn = psycopg2.connect(conn_string, sslmode='require')
cur = conn.cursor()
def migration_manager():
    migrations = sorted(os.listdir(MIGRATION_FILEPATH))
    for migration in migrations:
        file = open(os.path.join(MIGRATION_FILEPATH, migration)).read()
        if(migration == INITIAL_MIGRATION):
            cur.execute(file)
            conn.commit()
            print('Ran initial database migration setup')
        else:
            print('Checking status of migration ' + migration)
            cur.execute('''SELECT * FROM migrations WHERE migration_name = \''''+migration+'''\';''')
            migration_run = cur.fetchall()
            if(len(migration_run) != 0):
                print('Migration '+migration+' already exists on database')
            else:
                cur.execute(file)
                conn.commit()
                print('Migration '+migration+' run on database')
    cur.execute('''SELECT * FROM migrations;''')
    migration_list = cur.fetchall()
    print('Current Migrations:')
    print('--------------------------')
    for migration in migration_list:
        print(migration)
    print('--------------------------')
    cur.close()