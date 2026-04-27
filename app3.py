from flask import Flask, render_template, request, redirect, jsonify
import sqlite3, requests
import os


app = Flask(__name__, template_folder="templates3", static_folder="static3")

# -------- DATABASE --------
def get_db():
    os.makedirs("db", exist_ok=True)
    conn = sqlite3.connect("db/workouts.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        duration TEXT,
        details TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -------- HOME --------
@app.route("/")
def home():
    return render_template("home.html")

# -------- ADD --------
@app.route("/add", methods=["POST"])
def add():
    title = request.form["title"]
    duration = request.form["duration"]
    details = request.form["details"]

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO workouts (title, duration, details) VALUES (?, ?, ?)",
              (title, duration, details))
    conn.commit()
    conn.close()

    return redirect("/")


# -------- DELETE --------
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM workouts WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/")

# -------- EDIT --------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        duration = request.form["duration"]
        details = request.form["details"]

        c.execute("""
            UPDATE workouts
            SET title=?, duration=?, details=?
            WHERE id=?
        """, (title, duration, details, id))

        conn.commit()
        conn.close()

        return redirect("/workouts")

    c.execute("SELECT * FROM workouts WHERE id=?", (id,))
    workout = c.fetchone()

    conn.close()

    return render_template("edit.html", workout=workout)


@app.route("/joke")
def joke():
    try:
        res = requests.get("https://api.chucknorris.io/jokes/random")
        data = res.json()

        return jsonify({
            "joke": data["value"]
        })

    except:
        return jsonify({
            "joke": "Chuck Norris je trenutno premočan za API."
        })

@app.route("/workouts")
def workouts():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM workouts ORDER BY id DESC")
    workouts = c.fetchall()

    conn.close()

    return render_template("workouts.html", workouts=workouts)


@app.route("/exercise_info")
def exercise_info():
    city = request.args.get("q")
    date = request.args.get("date")

    if not city:
        return jsonify({"info": "no query"})

    try:
        geo = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={city}",
            timeout=5
        ).json()

        if not geo.get("results"):
            return jsonify({"info": "Mesto ni najdeno"})

        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]

        weather = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "weathercode"
                ],
                "timezone": "auto",
                "forecast_days": 7
            },
            timeout=5
        ).json()
        print(weather)

        if "daily" not in weather:
            return jsonify({"info": "API error - no daily data"})

        daily = weather.get("daily", {})

        if not daily or "time" not in daily:
            return jsonify({"info": "No daily time data"})

        if not daily:
            return jsonify({"info": "Ni podatkov"})

        # poišči index za datum
        if date and "time" in daily:
            if date in daily["time"]:
                i = daily["time"].index(date)
            else:
                # fallback → vzemi zadnji dan v napovedi
                i = len(daily["time"]) - 1
        else:
            i = 0

        return jsonify({
            "name": city,
            "date": daily["time"][i],
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "weathercode": daily["weathercode"][i],
            "weather_desc": weather_emoji(daily["weathercode"][i])
        })

    except Exception:
        return jsonify({"info": "API error"})


@app.route("/exercise")
def exercise_page():
    return render_template("exercise.html")

@app.route("/workout/<int:id>")
def workout_detail(id):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM workouts WHERE id=?", (id,))
    workout = c.fetchone()

    conn.close()

    if not workout:
        return "Workout not found"

    return render_template("workout_detail.html", workout=workout)

def weather_emoji(code):
    if code == 0:
        return "☀️ jasno"
    elif code in [1, 2, 3]:
        return "⛅ delno oblačno"
    elif code in [45, 48]:
        return "🌫️ megla"
    elif code in [51, 53, 55, 61, 63, 65]:
        return "🌧️ dež"
    elif code in [71, 73, 75]:
        return "❄️ sneg"
    elif code in [80, 81, 82]:
        return "🌦️ plohe"
    elif code in [95, 96, 99]:
        return "⛈️ nevihta"
    else:
        return "🌍 neznano vreme"

app.run(debug=True)