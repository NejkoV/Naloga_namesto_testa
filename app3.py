from flask import Flask, render_template, request, redirect, session, jsonify
from tinydb import TinyDB, Query
from werkzeug.utils import secure_filename
import os, uuid


app = Flask(__name__, template_folder='Templates3')  # Določi mapo za predloge
app.secret_key = "guner27"  # Nastavite vašo sejo (to je potrebno za prijavo uporabnika)


db = TinyDB("db.omrežje")
users = db.table("users")
User = Query()

#homepage
@app.route("/")
def home():
    if "user" in session:
        return redirect("/omrezje")
    return redirect("/login")



@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username=request.form["username"]
        password=request.form["password"]

        if users.search(User.username == username):
            return "Uporabnik že obstaja"
        
        users.insert({"username": username, "password": password, "note": ""})
        return redirect("/login")

    else:
        return render_template("register.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username=request.form["username"]
        password=request.form["password"]

        user = users.get(User.username == username)
        #print(user)

        if user and user["password"]== password:
            session["user"]= username
            return redirect("/app")

        return "Napačen login"

    else:
        return render_template("login.html")

@app.route("/app", methods=["POST", "GET"])
def login():