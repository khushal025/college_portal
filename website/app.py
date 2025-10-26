# website/app.py
import os
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
import tempfile

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "defaultsecret")

# ----------------- INLINE CA CERTIFICATE -----------------
# Tumhara Aiven CA certificate content yaha paste karo
AIVEN_CA_CERT = """-----BEGIN CERTIFICATE-----
MIID... (yaha tumhara full ca certificate content paste karo) ...
-----END CERTIFICATE-----"""

# Temporary file me certificate write karke ssl_ca use karenge
temp_ca_file = tempfile.NamedTemporaryFile(delete=False)
temp_ca_file.write(AIVEN_CA_CERT.encode('utf-8'))
temp_ca_file.flush()
temp_ca_file_path = temp_ca_file.name

# ----------------- DATABASE CONNECTION -----------------
try:
    db = mysql.connector.connect(
        host=os.environ.get("DB_HOST", "mysql-20a16630-khushalgarg390-4681.c.aivencloud.com"),
        port=int(os.environ.get("DB_PORT", 11980)),
        user=os.environ.get("DB_USER", "avnadmin"),
        password=os.environ.get("DB_PASS", "AVNS_rz2ljygN3FXbvS08LOo"),
        database=os.environ.get("DB_NAME", "defaultdb"),
        ssl_ca=temp_ca_file_path
    )
    cursor = db.cursor(dictionary=True)
    print("✅ Database connected successfully!")
except Error as e:
    print(f"❌ Database connection failed: {e}")
    cursor = None

# ----------------- HOMEPAGE ROUTE -----------------
@app.route("/", methods=["GET"])
def home():
    return "Welcome to the Portal!", 200

# ----------------- STUDENT LOGIN API -----------------
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

# ----------------- TEACHER LOGIN API -----------------
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
