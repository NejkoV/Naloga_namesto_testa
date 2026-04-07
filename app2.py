from flask import Flask, render_template, request, redirect, session, jsonify
from tinydb import TinyDB, Query
from werkzeug.utils import secure_filename
import os


app = Flask(__name__, template_folder='Templates2')  # Določi mapo za predloge
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Pot do mape za slike
app.secret_key = "guner22"  # Nastavite vašo sejo (to je potrebno za prijavo uporabnika)

db = TinyDB("db.omrežje")
users = db.table("users")
User = Query()

#homepage
@app.route("/")
def home():
    if "user" in session:
        return redirect("/omrezje")
    return redirect("/login")



User = Query()

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
            return redirect("/omrezje")

        return "Napačen login"

    else:
        return render_template("login.html")


@app.route("/omrezje", methods=["POST", "GET"])
def homePage():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    # Preveri, ali je uporabnik še v bazi
    user_data = users.search(User.username == username)
    if not user_data:
        session.pop("user", None)
        return redirect("/login")

    # Obdelava podatkov, če pride POST
    if request.method == "POST":
        text = request.form.get("note", "")  # Pridobi besedilo, privzeto prazen niz
        file = request.files.get("image")

        filename = None
        if file and allowed_file(file.filename):  # Preveri, ali je datoteka slika
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)  # Shrani datoteko

        # Preveri, ali uporabnik že ima objavo
        # Če ima objavo, jo posodobi, sicer ustvari novo objavo
        posts = user_data[0].get("posts", [])
        if posts:  # Posodobi obstoječo objavo
            posts[0]["note"] = text
            posts[0]["image"] = filename if filename else None
        else:  # Če objava še ne obstaja, ustvari novo
            posts.append({
                "note": text,
                "image": filename if filename else None
            })

        # Posodobi bazo z novo objavo
        users.update({
            "posts": posts  # Posodobi obstoječo objavo
        }, doc_ids=[user_data[0].doc_id])

    # Pridobi obstoječo objavo (če obstaja)
    posts = user_data[0].get("posts", [])
    note = posts[0]["note"] if posts else ""

    return render_template("omrezje.html", user=username, note=note, user_data=user_data[0])

@app.route("/users", methods=["GET"])
def get_users():
    users_list = users.all()
    usernames = [u["username"] for u in users_list]
    return jsonify(usernames)

@app.route("/user/<username>", methods=["GET"])
def get_user(username):
    user_data = users.search(User.username == username)

    if not user_data:
        return render_template("404.html", message="Uporabnik ni najden")

    # Prikaz vseh objav uporabnika
    posts = user_data[0].get("posts", [])
    return render_template("razgled.html", user=username, user_data=user_data[0], posts=posts)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.run(debug=True)

