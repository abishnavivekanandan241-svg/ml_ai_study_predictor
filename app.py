import os
from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import get_db, init_db

import pandas as pd
import numpy as np
import shap
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

# ------------------- INIT -------------------
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = "secret123"

init_db()

# ------------------- ML MODEL -------------------
data = pd.read_csv("student_data.csv")

# Feature Engineering
data["study_efficiency"] = data["studytime"] / (data["absences"] + 1)
data["risk"] = data["failures"] * data["absences"]

X = data[["studytime", "absences", "failures", "study_efficiency", "risk"]]
y = data["G3"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

explainer = shap.TreeExplainer(model)

# ------------------- AUTH -------------------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users(username,password) VALUES (?,?)",
                (username, password)
            )
            db.commit()
        except:
            return "User already exists"

        return redirect('/login')

    return render_template('signup.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session['user'] = username
            return redirect('/')

        return "Invalid credentials"

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ------------------- HOME -------------------
@app.route('/')
def home():
    if "user" not in session:
        return redirect('/login')
    return render_template('index.html')


# ------------------- HISTORY -------------------
@app.route('/history')
def history():
    if "user" not in session:
        return redirect('/login')

    db = get_db()
    rows = db.execute(
        "SELECT study, absences, failures, prediction FROM history WHERE username=? ORDER BY id DESC",
        (session['user'],)
    ).fetchall()

    return render_template("history.html", rows=rows)


# ------------------- PREDICT -------------------
@app.route('/predict', methods=['POST'])
def predict():
    data_in = request.json

    study = float(data_in['study'])
    absences = float(data_in['absences'])
    failures = float(data_in['failures'])

    # Features
    features = [
        study,
        absences,
        failures,
        study/(absences+1),
        failures*absences
    ]

    # Prediction
    pred = model.predict([features])[0]

    # Confidence
    preds = [tree.predict([features])[0] for tree in model.estimators_]
    std = np.std(preds)

    if std < 1:
        conf_label = "High"
    elif std < 3:
        conf_label = "Medium"
    else:
        conf_label = "Low"

    # SHAP
    input_df = pd.DataFrame(
        [features],
        columns=["studytime", "absences", "failures", "study_efficiency", "risk"]
    )

    shap_vals = explainer.shap_values(input_df)[0]

    total = np.sum(np.abs(shap_vals))
    shap_norm = (shap_vals / total).tolist() if total != 0 else [0]*5

    # Graph curve
    x_range = np.linspace(0, 10, 100)
    y_curve = model.predict([
        [x, absences, failures, x/(absences+1), failures*absences]
        for x in x_range
    ])

    # Label
    good = np.percentile(y, 75)
    avg = np.percentile(y, 50)

    if pred >= good:
        label = "Good"
        color = "#10b981"
    elif pred >= avg:
        label = "Average"
        color = "#facc15"
    else:
        label = "Poor"
        color = "#ef4444"

    # SAVE TO DB
    if "user" in session:
        db = get_db()
        db.execute(
            "INSERT INTO history(username, study, absences, failures, prediction) VALUES (?,?,?,?,?)",
            (session['user'], study, absences, failures, float(pred))
        )
        db.commit()

    return jsonify({
        "prediction": float(pred),
        "label": label,
        "color": color,
        "x": x_range.tolist(),
        "y": y_curve.tolist(),
        "user_x": study,
        "user_y": pred,
        "contributions": shap_norm,
        "confidence": conf_label
    })


# ------------------- CHATBOT -------------------
@app.route('/chat', methods=['POST'])
def chat():
    import re

    msg = request.json.get("message", "").lower()

    # ---------------- SESSION MEMORY ----------------
    if "chat_history" not in session:
        session["chat_history"] = []

    session["chat_history"].append(msg)

    # ---------------- EXTRACT NUMBERS ----------------
    numbers = re.findall(r'\d+', msg)
    hours = int(numbers[0]) if numbers else None

    # ---------------- CONTEXT ----------------
    last_msgs = " ".join(session["chat_history"][-3:])

    # ---------------- RESPONSE ENGINE ----------------

    # STUDY PLAN GENERATOR
    if "plan" in msg or "schedule" in msg:
        if hours:
            reply = (
                f"🧠 Personalized Study Plan for {hours} hours:\n\n"
                f"📌 1 hour → New learning\n"
                f"📌 {max(hours-2,1)} hours → Practice\n"
                f"📌 1 hour → Revision\n\n"
                "👉 Repeat daily for best results 🚀"
            )
        else:
            reply = (
                "🗓️ Tell me how many hours you can study daily.\n"
                "Example: 'I can study 4 hours'\n"
                "👉 I'll create a plan for you!"
            )

    # LOW STUDY HOURS DETECTION
    elif hours and hours < 2:
        reply = (
            f"⚠️ {hours} hours is too low.\n\n"
            "👉 Try increasing to at least 3–4 hours.\n"
            "Even 30 mins extra daily makes a big difference 📈"
        )

    # HIGH STUDY HOURS
    elif hours and hours >= 6:
        reply = (
            f"🔥 {hours} hours is great!\n\n"
            "👉 Make sure you:\n"
            "- Take breaks\n"
            "- Avoid burnout\n"
            "- Focus on quality study\n"
        )

    # MOTIVATION (CONTEXT AWARE)
    elif "tired" in msg or "lazy" in msg or "no mood" in msg:
        reply = (
            "💡 You don't need motivation.\n"
            "You need action.\n\n"
            "👉 Start with just 10 minutes.\n"
            "Once you start, momentum will follow 🚀"
        )

    # EXAM MODE
    elif "exam" in msg or "test" in msg:
        reply = (
            "📝 Exam Strategy:\n"
            "- Revise important topics\n"
            "- Solve past papers\n"
            "- Focus weak areas\n"
            "- Sleep well before exam\n\n"
            "🔥 Smart work beats hard work."
        )

    # IMPROVEMENT BASED ON HISTORY
    elif "improve" in msg or "marks" in msg:
        if "fail" in last_msgs:
            reply = (
                "📉 I see you mentioned failure earlier.\n\n"
                "👉 Focus on:\n"
                "- Weak subjects\n"
                "- Practice daily\n"
                "- Ask doubts quickly\n\n"
                "🔥 You can bounce back!"
            )
        else:
            reply = (
                "📈 To improve marks:\n"
                "- Study consistently\n"
                "- Revise daily\n"
                "- Practice more questions\n\n"
                "👉 Small progress = Big results"
            )

    # FOCUS
    elif "focus" in msg or "concentration" in msg:
        reply = (
            "🎯 Focus Tips:\n"
            "- Remove phone distractions\n"
            "- Use Pomodoro (25 min)\n"
            "- Study in clean space\n"
            "- Take short breaks\n\n"
            "🧠 Focus is trainable!"
        )

    # GREETING
    elif "hello" in msg or "hi" in msg:
        reply = (
            "Hey 👋 I'm your AI Mentor.\n\n"
            "I can:\n"
            "✔ Create study plans\n"
            "✔ Boost motivation\n"
            "✔ Improve your marks\n\n"
            "👉 Try: 'Make a 4 hour study plan'"
        )

    # DEFAULT INTELLIGENT RESPONSE
    else:
        reply = (
            "🤖 I'm here to help you improve.\n\n"
            "You can ask:\n"
            "- Study plan\n"
            "- Focus tips\n"
            "- Exam prep\n"
            "- Motivation\n\n"
            "👉 Example: 'I can study 3 hours, give me a plan'"
        )

    return jsonify({"reply": reply})

# ------------------- RUN -------------------
if __name__ == "__main__":
    app.run(debug=True)