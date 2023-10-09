#!/usr/bin/env python3

from flask import Flask, request

app = Flask(__name__)

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

