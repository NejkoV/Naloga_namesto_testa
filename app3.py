from flask import Flask, render_template, request, redirect, jsonify
import sqlite3, requests
import os
from urllib.parse import quote



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
        return jsonify({"error": "no query"}), 400

    try:
        geo = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city},
            timeout=5
        ).json()

        if not geo.get("results"):
            return jsonify({"error": "City not found"}), 404

        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]

        weather = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,weathercode",
                "timezone": "auto",
                "forecast_days": 7
            },
            timeout=5
        ).json()

        daily = weather.get("daily")

        times = [t.split("T")[0] for t in daily.get("time", [])]

        temps_max = daily.get("temperature_2m_max", [])
        temps_min = daily.get("temperature_2m_min", [])
        codes = daily.get("weathercode", [])

        date = (date or "").split("T")[0]

        if not times:
            return jsonify({"error": "No time data"}), 500

        if date in times:
            i = times.index(date)
        else:
            i = len(times) - 1

        return jsonify({
            "name": city,
            "date": times[i],
            "temp_max": temps_max[i],
            "temp_min": temps_min[i],
            "weathercode": codes[i],
            "weather_desc": weather_emoji(codes[i])
        })

    except requests.RequestException as e:
        return jsonify({"error": "API/network error", "details": str(e)}), 500


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