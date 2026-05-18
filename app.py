from http.client import responses
from random import random
import re

from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import mysql.connector
import bcrypt

app = Flask(__name__)
app.secret_key = "super_secret_key_2026"

# 🔹 DATABASE CONNECTION
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root@123",
    database="college_db"
)

cursor = db.cursor(dictionary=True)


# 🔹 HOME PAGE
@app.route('/')
def home():
    return render_template("register.html")


# 🔹 SET LANGUAGE (AJAX)
@app.route("/set_language", methods=["POST"])
def set_language():
    lang = request.json.get("language")
    session["language"] = lang
    return jsonify({"status": "success"})


# 🔹 REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user:
            return render_template("register.html", error="Email already registered ❌. Please use a different email or login.")
        # Hash password
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        db.commit()

        session["user"] = email
        session["name"] = name
        session["language"] = "english"

        return redirect('/login')

    return render_template("register.html",error=None)


# 🔹 LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        cursor.execute("SELECT name, password FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user:
        
            stored_password = user['password']

            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                session["user"] = email
                session["name"] = user['name']
                session["language"] = "english"
                return redirect("/chat")
            else:
                return render_template("login.html", error="Invalid Password ❌")
        else:
            return render_template("login.html", error="User not found ❌")

    return render_template("login.html",error=None)


# 🔹 CHAT PAGE
@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("chat.html", name=session["name"])


# 🔹 CHATBOT LOGIC (PROFESSIONAL VERSION)
import re

@app.route('/get', methods=['POST'])
def chatbot():

    data = request.get_json() or {}
    user_input = data.get("message", "").lower().strip()
    lang = session.get("language", "english")

    print("\n===== NEW REQUEST =====")
    print("User Input:", user_input)
    print("Language:", lang)

    cursor.execute("SELECT * FROM faq")
    rows = cursor.fetchall()

    best_match = None
    max_score = 0

    for row in rows:

        if not row.get('keyword'):
            continue

        # 🔥 Split keywords (supports comma + space)
        db_keywords = re.split(r'[,\s]+', str(row['keyword']).lower())

        score = 0

        for key in db_keywords:
            key = key.strip()

            # 🔥 Matching logic
            if key and key in user_input:
                score += 1

        print(f"Checking: {row['question']} | Score: {score}")

        # 🔥 Choose best match
        if score > max_score:
            max_score = score
            best_match = row

    # ✅ RETURN BEST MATCH
    if best_match and max_score > 0:

        print("✅ BEST MATCH FOUND:", best_match['question'])

        if lang == "telugu" and best_match.get("answer_telugu"):
            return jsonify({"reply": best_match["answer_telugu"]})

        elif lang == "hindi" and best_match.get("answer_hindi"):
            return jsonify({"reply": best_match["answer_hindi"]})

        else:
            return jsonify({"reply": best_match.get("answer_en", "No answer available")})

    print("❌ NO MATCH FOUND")
    


    # 🌐 Default responses
    if lang == "telugu":
        return jsonify({"reply": "క్షమించండి, మీ ప్రశ్న అర్థం కాలేదు"})
    elif lang == "hindi":
        return jsonify({"reply": "माफ कीजिए, मैं आपका प्रश्न समझ नहीं पाया"})
    else:
        return jsonify({"reply": "Sorry, I didn't understand your question"})

# 🔹 LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# 🔹 FORGOT PASSWORD PAGE
@app.route('/forgot')
def forgot_page():
    return render_template("forgot_password.html")


# 🔹 RESET PASSWORD
@app.route('/forgot_password', methods=['POST'])
def forgot_password():

    email = request.form['email']
    new_password = request.form.get('new_password')

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if user:
        hashed_password = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        cursor.execute(
            "UPDATE users SET password=%s WHERE email=%s",
            (hashed_password, email)
        )
        db.commit()

         # 🔥 SUCCESS MESSAGE (SAME PAGE)
        return render_template(
            "forgot_password.html",
            success="✅ Password updated successfully! Please login."
        )

    else:
        # 🔥 ERROR MESSAGE (SAME PAGE)
        return render_template(
            "forgot_password.html",
            error="❌ Email not found"
        )

       

# 🔹 RUN APP
if __name__ == '__main__':
    print("✅ Server Started...")
    app.run(debug=True)