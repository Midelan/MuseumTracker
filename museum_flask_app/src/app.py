#!/usr/bin/env python3

from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def main():
    return '''
    <form action="/echo_user_input" method="POST">
        <select name="Museum">
            <option value="Harvard Museum of Art">Harvard Museum of Art</option>
            <option value="National Gallery of Art">National Gallery of Art</option>
            <option value="Smithsonian">Smithsonian</option>
        </select>
        <input type="submit" value="Submit!">
    </form>
    <form action="/authentication" method="POST">
        <input type="submit" value="Login/Register" name="auth_action"/>
    </form>
     '''

@app.route("/echo_user_input", methods=["POST"])
def echo_input():
    input_text = request.form.get("Museum", "")
    return "Sorry, data for the " + input_text + " is not yet available"

@app.route("/authentication", methods=["POST"])
def auth():
    return '''
    Sorry, Authentication is not yet implemented.
    <form action="/" method="POST">
        <input type="submit" value="Back to Home" name="home_action"/>
    </form>
     '''

