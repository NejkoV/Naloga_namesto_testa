from flask import Flask, render_template, request, redirect, session, jsonify
from flask_mail import Mail, Message
from tinydb import TinyDB, Query
import uuid
import random
import string
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash


# Ustvari Flask aplikacijo
app = Flask(__name__)
app.secret_key = "skrivnost67"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'nejkodh@gmail.com'  # Tvoj Gmail naslov
app.config['MAIL_PASSWORD'] = 'your_app_password'  # Uporabi App Password
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'

mail = Mail(app)

# Ustvari bazo TinyDB
db = TinyDB("db.json")
users = db.table("users")

# Preostale poti in funkcionalnosti
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        email = request.form["email"]  # Pridobi email iz obrazca

        # Preveri, če uporabnik že obstaja
        if users.search(Query().username == username):
            return "Uporabnik že obstaja"
        
        # Shrani uporabnika v bazo skupaj z emailom
        users.insert({"username": username, "password": password, "email": email, "note": ""})

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Poišči uporabnika v bazi
        user = users.get(Query().username == username)

        if user and check_password_hash(user["password"], password):
            session["user"] = username
            return redirect("/dashboard")

        return "Napačen login"

    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]
    query = request.args.get("q", "")

    user_data = users.get(Query().username == username)
    if not user_data:
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        note = request.form["note"]

        new_note = {
            "id": str(uuid.uuid4()),
            "title": title,
            "note": note
        }

        notes = user_data.get("notes", [])
        notes.append(new_note)

        users.update({"notes": notes}, doc_ids=[user_data.doc_id])

    notes = user_data.get("notes", [])

    if query:
        notes = [
            n for n in notes
            if query.lower() in n["title"].lower()
        ]

    return render_template(
        "dashboard.html",
        user=username,
        notes=notes,
        query=query
    )


@app.route("/edit_note/<note_id>", methods=["GET", "POST"])
def edit_note(note_id):
    if "user" not in session:
        return redirect("/login")

    username = session["user"]
    user_data = users.search(Query().username == username)

    if not user_data:
        return redirect("/login")
    
    user_data = user_data[0]
    notes = user_data.get("notes", [])

    # Poišči noto z določenim ID-jem
    note_to_edit = next((note for note in notes if note["id"] == note_id), None)
    
    if note_to_edit is None:
        return redirect("/dashboard")  # Če ni najdene objave z ID-jem, preusmeri

    # Če je metoda POST, posodobi objavo
    if request.method == "POST":
        new_title = request.form["title"]  # Pridobi naslov iz obrazca
        new_note = request.form["note"]    # Pridobi besedilo iz obrazca

        # Posodobi objavo
        note_to_edit["title"] = new_title
        note_to_edit["note"] = new_note

        # Posodobi objavo v bazi
        users.update({"notes": notes}, doc_ids=[user_data.doc_id])

        return redirect("/dashboard")

    # Če je GET metoda, prikaži formo z obstoječo objavo
    return render_template("edit_note.html", note=note_to_edit)


@app.route("/delete_note/<note_id>", methods=["POST"])
def delete_note(note_id):
    if "user" not in session:
        return redirect("/login")
    
    username = session["user"]
    user_data = users.search(Query().username == username)
    
    if not user_data:
        return redirect("/login")
    
    user_data = user_data[0]
    
    # Poišči in odstrani objavo z določenim ID-jem
    notes = user_data.get("notes", [])
    notes = [note for note in notes if note["id"] != note_id]
    
    # Posodobi uporabnika z novim seznamom objav
    users.update({"notes": notes}, doc_ids=[user_data.doc_id])
    
    return redirect("/dashboard")


# Funkcija za generiranje naključnega tokena (povezava za ponastavitev)
def generate_reset_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))  # Naključen 32-znamenkasti token

@app.route("/forgot_password", methods=["POST", "GET"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        
        # Preveri, ali uporabnik obstaja z tem emailom
        user = users.get(Query().email == email)  # Uporabi Query() namesto User()
        
        if user:
            # Generiraj edinstven ponastavitveni token
            reset_token = generate_reset_token()

            # Shrani token v bazo
            users.update({"reset_token": reset_token}, doc_ids=[user.doc_id])

            # Pošlji povezavo za ponastavitev gesla uporabniku
            reset_url = f"http://localhost:5000/reset_password/{reset_token}"

            msg = Message(
            "Ponastavitev gesla",
            sender=app.config['MAIL_USERNAME'],  # tvoj Gmail
            recipients=[email]
            )   

            msg.body = f"Klikni na naslednjo povezavo, da ponastaviš svoje geslo: {reset_url}"

            mail.send(msg)



            return "Povezava za ponastavitev gesla je bila poslana na tvojo e-pošto."

        return "Email ni povezan z nobenim uporabnikom."

    return render_template("forgot_password.html")

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user_data = users.search(User.reset_token == token)  # Poiščemo uporabnika s tem tokenom

    if not user_data or datetime.now() > user_data[0]["token_expiry"]:
        return "Povezava za ponastavitev gesla ni več veljavna."

    if request.method == "POST":
        new_password = request.form["new_password"]
        # Posodobite geslo uporabnika
        users.update({"password": new_password, "reset_token": None, "token_expiry": None}, doc_ids=[user_data[0].doc_id])
        return redirect("/login")

    return render_template("reset_password.html")

@app.route("/logout")
def logout():
    session.pop("user", None)  # Izbriši uporabniško sejo
    return redirect("/login")  # Preusmeri na login stran


@app.route("/notes")
def notes():
    query = request.args.get("q", "")

    user = users.get(Query().id == "1")  # prilagodi login sistem

    notes = user["notes"]

    if query:
        notes = [
            note for note in notes
            if query.lower() in note["title"].lower()
        ]

    return render_template("notes.html", notes=notes, query=query)


app.run(debug=True)