from flask import Flask, render_template, request, redirect, session, jsonify
from tinydb import TinyDB, Query
import uuid

app=Flask(__name__)
app.secret_key="skrivnost67"

User = Query()

db=TinyDB("db.json")
users= db.table("users")

from flask import Flask, render_template, request, redirect, session
from tinydb import TinyDB, Query


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
    
    # Preveri, če je uporabnik že v bazi
    user_data = users.search(Query().username == username)
    if not user_data:
        return redirect("/login")

    user_data = user_data[0]
    
    # Shrani novo objavo (POST)
    if request.method == "POST":
        title = request.form["title"]
        note = request.form["note"]

        # Generiraj edinstven ID za objavo
        new_note = {
            "id": str(uuid.uuid4()),  # Ustvari unikaten ID
            "title": title, 
            "note": note
        }
        
        # Posodobi ali ustvari novo objavo
        if "notes" in user_data:
            user_data["notes"].append(new_note)
        else:
            user_data["notes"] = [new_note]

        users.update({"notes": user_data["notes"]}, doc_ids=[user_data.doc_id])

    # Prikaži seznam vseh objav
    notes = user_data.get("notes", [])
    return render_template("dashboard.html", user=username, notes=notes)


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


app.run(debug=True)