# app.py
import os
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "defaultsecret")

# MySQL connection setup with SSL
try:
    db = mysql.connector.connect(
        host=os.environ.get("DB_HOST", "mysql-20a16630-khushalgarg390-4681.c.aivencloud.com"),
        port=int(os.environ.get("DB_PORT", 11980)),
        user=os.environ.get("DB_USER", "avnadmin"),
        password=os.environ.get("DB_PASS", "AVNS_rz2ljygN3FXbvS08LOo"),
        database=os.environ.get("DB_NAME", "defaultdb"),
        ssl_ca="website/certs/aiven-ca.crt"   # Make sure cert file path correct hai
    )
    cursor = db.cursor(dictionary=True)
    print("✅ Database connected successfully!")
except Error as e:
    print(f"❌ Database connection failed: {e}")
    cursor = None

# ----------------- API ROUTES -----------------

@app.route("/api/student_login", methods=["POST"])
def student_login():
    if cursor is None:
        return jsonify({"status": "fail", "message": "DB not connected"}), 500

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    cursor.execute(
        "SELECT * FROM students WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cursor.fetchone()
    if user:
        return jsonify({"status": "success", "user": user})
    return jsonify({"status": "fail"}), 401


@app.route("/api/teacher_login", methods=["POST"])
def teacher_login():
    if cursor is None:
        return jsonify({"status": "fail", "message": "DB not connected"}), 500

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    cursor.execute(
        "SELECT * FROM teachers WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cursor.fetchone()
    if user:
        return jsonify({"status": "success", "user": user})
    return jsonify({"status": "fail"}), 401


# ----------------- RUN FLASK -----------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
