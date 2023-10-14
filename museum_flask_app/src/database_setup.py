#!/usr/bin/env python3

import os
import psycopg2

directory = os.path.dirname(__file__)
MIGRATION_FILEPATH = os.path.join(directory, '../migrations')
INITIAL_MIGRATION = '00_migration_setup'

class MigrationManager:
    conn_string = None
    conn = None
    cur = None
    def __init__(self):
        self.conn_string = os.getenv('CONNECTION_STRING')
        self.conn = psycopg2.connect(self.conn_string, sslmode='require')
        self.cur = self.conn.cursor()

    def migration_manager(self):
        migrations = sorted(os.listdir(MIGRATION_FILEPATH))
        for migration in migrations:
            file = open(os.path.join(MIGRATION_FILEPATH, migration)).read()
            if(migration == INITIAL_MIGRATION):
                self.cur.execute(file)
                self.conn.commit()
                print('Ran initial database migration setup')
            else:
                print('Checking status of migration ' + migration)
                self.cur.execute('''SELECT * FROM migrations WHERE migration_name = \''''+migration+'''\';''')
                migration_run = self.cur.fetchall()
                if(len(migration_run) != 0):
                    print('Migration '+migration+' already exists on database')
                else:
                    self.cur.execute(file)
                    self.conn.commit()
                    print('Migration '+migration+' run on database')
        self.cur.execute('''SELECT * FROM migrations;''')
        migration_list = self.cur.fetchall()
        print('Current Migrations:')
        print('--------------------------')
        for migration in migration_list:
            print(migration)
        print('--------------------------')
        self.cur.close()