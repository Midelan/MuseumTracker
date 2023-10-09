#!/usr/bin/env python3
import os

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://museum_tracker_user:KT2g6hyg3bONXMXx8JpP4LegTf9sGett@dpg-cki3dca12bvs739krt4g-a.oregon-postgres.render.com/museum_tracker'


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
        return '''
        Sorry, full data for the ''' + museum_name + ''' is not yet available
        <form action="/">
            <input type="submit" value="Back to Home" name="home_action"/>
        </form>
         '''
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
def auth():
    return '''
    This page is only for dev testing the cloud platform functionality.
    Current Test ''' + os.getenv('testEnvVar') + '''
    <form action="/">
        <input type="submit" value="Back to Home" name="home_action"/>
    </form>
     '''