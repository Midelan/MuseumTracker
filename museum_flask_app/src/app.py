#!/usr/bin/env python3
import os
from datetime import datetime

import psycopg2
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor

from .database_setup import MigrationManager
from .musum_apis import APIController

app = Flask(__name__)

directory = os.path.dirname(__file__)
GET_ALL_ARTIFACTS_FILEPATH = os.path.join(directory, '../sql/get_all_artifacts')
museum_dict = {
    "Harvard Museum of Art": 1,
    "National Gallery of Art": 2,
    "Smithsonian": 3
}

with app.app_context():
    migrator = MigrationManager()
    migrator.migration_manager()

    executors = {
        'default': {'type': 'threadpool', 'max_workers': 2},
        'processpool': ProcessPoolExecutor(max_workers=2)
    }
    scheduler = BackgroundScheduler(executors=executors)
    print(scheduler.get_jobs())
    print(datetime.now())
    api_controller = APIController()
    job = scheduler.add_job(api_controller.start, trigger='cron', hour='13', minute='20', misfire_grace_time=60*60)
    scheduler.print_jobs()
    scheduler.start()


@app.route("/")
def main():
    return '''
    <form action="/echo_user_input" method="POST">
        Select Museum
        <br>
        <select name="Museum">
            <option value="Harvard Museum of Art">Harvard Museum of Art</option>
            <option value="National Gallery of Art">National Gallery of Art</option>
            <option value="Smithsonian">Smithsonian</option>
        </select>
        <br>
        Select Mode
        <br>
        <select name="Mode">
            <option value="New">Get New Records</option>
            <option value="All">Get All Records</option>
        </select>
        <br>
        <input type="submit" value="Submit!">
    </form>
    <form action="/authentication" method="POST">
        <input type="submit" value="Login/Register" name="auth_action"/>
    </form>
    <form action="/testing" method="POST">
        <input type="submit" value="Testing" name="test_action"/>
    </form>
     '''


@app.route("/echo_user_input", methods=["POST"])
def echo_input():
    museum_name = request.form.get("Museum", "")
    mode = request.form.get("Mode", "")
    if(mode == "All"):
        museum_id = museum_dict[museum_name]
        print(museum_id)
        file = open(GET_ALL_ARTIFACTS_FILEPATH).read()
        conn_string = os.getenv('CONNECTION_STRING')
        conn = psycopg2.connect(conn_string, sslmode='require')
        cur = conn.cursor()
        cur.execute(file, (museum_id,))
        data = cur.fetchall()
        return '''
        <form action="/">
            <input type="submit" value="Back to Home" name="home_action"/>
        </form>''' + render_template('table.html', data=data)
    else:
        return '''
        Sorry, new data for the ''' + museum_name + ''' is not yet available
        <form action="/">
            <input type="submit" value="Back to Home" name="home_action"/>
        </form>
         '''


@app.route("/authentication", methods=["POST"])
def auth():
    return '''
    Sorry, Authentication is not yet implemented.
    <form action="/">
        <input type="submit" value="Back to Home" name="home_action"/>
    </form>
     '''


@app.route("/testing", methods=["POST"])
def testing():
    return '''
    This page is only for dev testing the cloud platform functionality.
    Current Test ''' + os.getenv('testEnvVar') + '''
    <form action="/">
        <input type="submit" value="Back to Home" name="home_action"/>
    </form>
     '''