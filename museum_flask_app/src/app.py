#!/usr/bin/env python3

from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def main():
    return '''
    <select name="cars">
        <option value="Harvard">Harvard Museum of Art</option>
        <option value="NationalGallery">National Gallery of Art</option>
        <option value="Smithsonian">Smithsonian</option>
    </select>
    <form action="/echo_user_input" method="POST">
        <input name="user_input">
        <input type="submit" value="Submit!">
    </form>
    <form action="/authentication" method="POST">
        <input type="submit" value="Login/Register" name="auth_action"/>
    </form>
     '''

@app.route("/echo_user_input", methods=["POST"])
def echo_input():
    input_text = request.form.get("user_input", "")
    return "You entered: " + input_text

@app.route("/authentication", methods=["POST"])
def echo_input():
    return '''
    Sorry, Authentication is not yet implemented.
    <form action="/" method="POST">
        <input type="submit" value="Back to Home" name="home_action"/>
    </form>
     '''

