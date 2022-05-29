
import zlib
from werkzeug.utils import secure_filename
from flask import Response
import mysql.connector as mysql
import cv2
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import face_recognition
from PIL import Image
from base64 import b64encode, b64decode
import re
from helpers import apology, login_required

# Configure application
app = Flask(__name__)
# configure flask-socketio

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
users=[]

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
@app.route("/")
@login_required
def home():
    return redirect("/home")


@app.route("/home")
@login_required
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Assign inputs to variables
        input_username = request.form.get("username")
        input_password = request.form.get("password")

        # Ensure username was submitted
        if not input_username:
            return render_template("login.html", messager=1)



        # Ensure password was submitted
        elif not input_password:
            return render_template("login.html", messager=2)

        # Query database for username
        for user in users:
            if input_username == user["name"]:
                username = user

        # Ensure username exists and password is correct
        if len(str(username["name"])) != 1 or not check_password_hash(username["hash"], input_password):
            return render_template("login.html", messager=3)

        # Remember which user has logged in
        session["user_id"] = username["name"]
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/success")
def success():

    return render_template("success.html")
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Assign inputs to variables
        input_username = request.form.get("username")
        input_password = request.form.get("password")
        input_confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not input_username:
            return render_template("register.html", messager=1)

        # Ensure password was submitted
        elif not input_password:
            return render_template("register.html", messager=2)

        # Ensure passwsord confirmation was submitted
        elif not input_confirmation:
            return render_template("register.html", messager=4)

        elif not input_password == input_confirmation:
            return render_template("register.html", messager=3)

        # Query database for username

        for user in users:
            if user["name"] == input_username:
                if len(user["name"]) == 1:
                    return render_template("register.html", messager=5)
        # Ensure username is not already taken

        # Query database to insert new user
        else:

            new_user = {"name": input_username,
                        "password": generate_password_hash(input_password, method="pbkdf2:sha256",
                                                           salt_length=8)}
            users.append(new_user)
            if new_user:
                # Keep newly registered user logged in
                session["user_id"] = new_user["name"]

            # Flash info for the user
            flash(f"Registered as {input_username}")

            # Redirect user to homepage
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/facereg", methods=["GET", "POST"])
def facereg():
    session.clear()
    if request.method == "POST":

        encoded_image = (request.form.get("pic") + "==").encode('utf-8')
        username = request.form.get("name")



        id_ = username
        compressed_data = zlib.compress(encoded_image, 9)

        uncompressed_data = zlib.decompress(compressed_data)

        decoded_data = b64decode(uncompressed_data)

        new_image_handle = open('./static/face/unknown-' + str(id_) + '.jpg', 'wb')

        new_image_handle.write(decoded_data)
        new_image_handle.close()
        try:
            image_of_user = face_recognition.load_image_file(
                './static/face/' + str(id_) + '.jpg')
        except:
            return render_template("camera.html", message=5)

        image_of_user = cv2.cvtColor(image_of_user, cv2.COLOR_BGR2RGB)
        user_face_encoding = face_recognition.face_encodings(image_of_user)[0]

        unknown_image = face_recognition.load_image_file(
            './static/face/unknown-' + str(id_) + '.jpg')
        try:

            unknown_image = cv2.cvtColor(unknown_image, cv2.COLOR_BGR2RGB)
            unknown_face_encoding = face_recognition.face_encodings(unknown_image)[0]
        except:
            return render_template("camera.html", message=2)

        #  compare faces
        results = face_recognition.compare_faces(
            [user_face_encoding], unknown_face_encoding)
        print(results)

        if results[0]:

            for user in users:
                if user["name"] == id_:
                    session["user_id"] = user["name"]
            return redirect("/success")
        else:
            return render_template("camera.html", message=3)


    else:
        return render_template("camera.html")


@app.route("/facesetup", methods=["GET", "POST"])
def facesetup():
    if request.method == "POST":

        encoded_image = (request.form.get("pic") + "==").encode('utf-8')

        for user in users:
            if user["name"] == session["user_id"]:
                id_ = user["name"]

        # id_ = db.execute("SELECT id FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["id"]
        compressed_data = zlib.compress(encoded_image, 9)

        uncompressed_data = zlib.decompress(compressed_data)
        decoded_data = b64decode(uncompressed_data)

        new_image_handle = open('./static/face/' + str(id_) + '.jpg', 'wb')

        new_image_handle.write(decoded_data)
        new_image_handle.close()
        image_of_user = face_recognition.load_image_file(
            './static/face/' + str(id_) + '.jpg')
        try:
            user_face_encoding = face_recognition.face_encodings(image_of_user)[0]
        except:
            return render_template("face.html", message=1)
        return redirect("/home")

    else:
        return render_template("face.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("error.html", e=e)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
    app.run()
