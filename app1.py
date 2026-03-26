from flask import Flask, render_template, request, redirect, session, jsonify
from tinydb import TinyDB, Query

app=Flask(__name__)
app.secret_key="skrivnost67"

User = Query()

db=TinyDB("db.json")
users= db.table("users")

#homepage
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
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
            return redirect("/dashboard")

        return "Napačen login"

    else:
        return render_template("login.html")

@app.route("/dashboard", methods=["POST", "GET"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]
    #shranjevanje podatkov
    if request.method == "POST":
        text = request.form["note"]

        users.update(
            {"note": text},
            User.username == username
        )

    # 👇 VEDNO preberi iz baze
    user_data = users.get(User.username == username)
    note = user_data.get("note", "")

    return render_template("dashboard.html", user=username, note=note)


app.run(debug=True)