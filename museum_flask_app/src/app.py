#!/usr/bin/env python3
import os
from datetime import datetime

import psycopg2
import flask_login
import flask
import threading
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from prometheus_flask_exporter import PrometheusMetrics

from .new_artifact_check import NewArtifactChecker
from .database_setup import MigrationManager
from .museum_apis import APIController

app = Flask(__name__)
metrics = PrometheusMetrics(app)
app.secret_key = 'random-generated-secret-key'

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

directory = os.path.dirname(__file__)
GET_ALL_ARTIFACTS_FILEPATH = os.path.join(directory, '../sql/get_all_artifacts')
GET_NEW_ARTIFACTS_FILEPATH = os.path.join(directory, '../sql/get_new_artifacts')
RESET_NEW_ARTIFACTS_FILEPATH = os.path.join(directory, '../sql/reset_new_artifacts')
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
    job = scheduler.add_job(api_controller.start, trigger='cron', hour='15', minute='01', misfire_grace_time=60*60)
    scheduler.print_jobs()
    scheduler.start()

checker = NewArtifactChecker()
thread = threading.Thread(target=checker.start_listener)
thread.start()


@app.route("/")
def main():
    return '''
    <form action="/get-data" method="POST">
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
    <form action="/login" method="GET">
        <input type="submit" value="Login" name="login_action"/>
    </form>
        <form action="/register" method="POST">
        <input type="submit" value="Register" name="registration_action"/>
    </form>
     '''


@app.route("/get-data", methods=["POST"])
@flask_login.login_required
def get_artifacts():
    museum_name = flask.request.form.get("Museum", "")
    mode = flask.request.form.get("Mode", "")
    if(mode == "All"):
        museum_id = museum_dict[museum_name]
        file = open(GET_ALL_ARTIFACTS_FILEPATH).read()
        conn_string = os.getenv('CONNECTION_STRING')
        conn = psycopg2.connect(conn_string, sslmode='require')
        cur = conn.cursor()
        cur.execute(file, (museum_id,))
        data = cur.fetchall()
        return '''
        <form action="/">
            <input type="submit" value="Back to Home" name="home_action"/>
        </form>
        List of All Artifacts
        ''' + render_template('table.html', data=data)
    else:
        museum_id = museum_dict[museum_name]
        file = open(GET_NEW_ARTIFACTS_FILEPATH).read()
        conn_string = os.getenv('CONNECTION_STRING')
        conn = psycopg2.connect(conn_string, sslmode='require')
        cur = conn.cursor()
        cur.execute(file, (museum_id, flask_login.current_user.id))
        data = cur.fetchall()
        file = open(RESET_NEW_ARTIFACTS_FILEPATH).read()
        cur.execute(file, (museum_id, flask_login.current_user.id))
        conn.commit()
        cur.close()
        return '''
        <form action="/">
            <input type="submit" value="Back to Home" name="home_action"/>
        </form>
        List of New Artifacts
         ''' + render_template('table.html', data=data)


@app.route("/register", methods=["POST"])
def registration():
    return '''
    <form action="/add_account" method="POST">
        <input type='text' name='username' id='username' placeholder='username'/>
        <input type='password' name='password' id='password' placeholder='password'/>
        <input type="submit" value="Register">
    </form>
    <form action="/">
        <input type="submit" value="Back to Home" name="home_action"/>
    </form>
    Please do not reuse any real passwords, hashing/obscurement is not yet implemented
    '''


@app.route("/add_account", methods=["POST"])
def account_add():
    user_id = flask.request.form.get("username", "")
    password = flask.request.form.get("password", "")
    conn_string = os.getenv('CONNECTION_STRING')
    conn = psycopg2.connect(conn_string, sslmode='require')
    cur = conn.cursor()
    print(user_id, password, conn_string)
    try:
        cur.execute('INSERT INTO users (user_id, password) VALUES(\''+user_id+'\', \''+password+'\');')
        conn.commit()
        cur.close()
    except:
        return '''
        Failed to register account, please return to home
        <form action="/">
            <input type="submit" value="Back to Home" name="home_action"/>
        </form>
        '''
    return '''
    Successfully registered account, please return to home
    <form action="/">
        <input type="submit" value="Back to Home" name="home_action"/>
    </form>
    '''


@login_manager.user_loader
def user_loader(email):
    conn_string = os.getenv('CONNECTION_STRING')
    conn = psycopg2.connect(conn_string, sslmode='require')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users where user_id = \''+email+'\'')
    response = cur.fetchall()
    cur.close()
    if(len(response) == 0):
        return
    user = User()
    user.id = response[0][0]
    return user


@login_manager.request_loader
def request_loader(request):
    user_id = request.form.get('user_id')
    conn_string = os.getenv('CONNECTION_STRING')
    conn = psycopg2.connect(conn_string, sslmode='require')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users where user_id = \''+user_id+'\'')
    response = cur.fetchall()
    cur.close()
    if(len(response) == 0):
        return
    user = User()
    user.id = response[0][0]
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
               <form action='login' method='POST'>
                <input type='text' name='user_id' id='user_id' placeholder='user_id'/>
                <input type='password' name='password' id='password' placeholder='password'/>
                <input type='submit' name='submit'/>
               </form>
               '''

    user_id = flask.request.form['user_id']
    conn_string = os.getenv('CONNECTION_STRING')
    conn = psycopg2.connect(conn_string, sslmode='require')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users where user_id = \''+user_id+'\'')
    response = cur.fetchall()
    cur.close()
    if user_id == response[0][0] and flask.request.form['password'] == response[0][1]:
        user = User()
        user.id = user_id
        flask_login.login_user(user)
        print(flask_login.current_user.id)
        return flask.redirect(flask.url_for('protected'))

    return '''
    Incorrect Login Credentials
    <form action="/">
        <input type="submit" value="Back to Home" name="home_action"/>
    </form>
    <form action="/login" method="GET">
        <input type="submit" value="Retry Login" name="login_action"/>
    </form>
    '''


@app.route('/protected')
@flask_login.login_required
def protected():
    return '''
    Logged in as: '''+ flask_login.current_user.id +'''
    <form action="/">
        <input type="submit" value="Back to Home" name="home_action"/>
    </form>
    '''

@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return '''
    Logged out
    <form action="/">
        <input type="submit" value="Back to Home" name="home_action"/>
    </form>
    '''


@app.route("/health")
def health():
    return {'message': 'Healthy'}


class User(flask_login.UserMixin):
    pass
