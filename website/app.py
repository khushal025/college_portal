# website/app.py
import os
import tempfile
from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
import pandas as pd
import mysql.connector
from werkzeug.utils import secure_filename

# ----------------- APP INIT -----------------
app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get("SESSION_SECRET", "Khushal@8755")

# ----------------- SSL CA CERT -----------------
AIVEN_CA_CERT = os.environ.get("AIVEN_CA_CERT", """-----BEGIN CERTIFICATE-----
MIIEUDCCArigAwIBAgIUYSzQ/dH3YAI9zWfkGY7LV3z5IhIwDQYJKoZIhvcNAQEM
BQAwQDE+MDwGA1UEAww1NTNlMjA5NmQtMzFjMC00OGZhLWE2ZTMtODQxN2VkMGUz
MmIyIEdFTiAxIFByb2plY3QgQ0EwHhcNMjUwOTE5MjAzNTQ5WhcNMzUwOTE3MjAz
NTQ5WjBAMT4wPAYDVQQDDDU1M2UyMDk2ZC0zMWMwLTQ4ZmEtYTZlMy04NDE3ZWQw
ZTMyYjIgR0VOIDEgUHJvamVjdCBDQTCCAaIwDQYJKoZIhvcNAQEBBQADggGPADCC
AYoCggGBALyp05sSb9PvDnd9G+oXYCVQznt/ZqqfP60tNuWxZBFjlU84aQkf6Vpf
38/qLQQnjkU2e5y0AwqFntvxzucYEC24SA6fccPEwFy1BlwEBbKqDm2RNwj0l5H1
Fvupy/7gV1EHSXgyU8wpxhw6/sSF7BnY2kD4931MgwT5aB34Xn0zz7wi7MY6zA1d
1WBEfedO1DwtrW69/wkNXSMEnZyita8PgBKOX/EjQw1qyBjw5Ql68kiDg6FlDSzD
nqxom3vv2mybhWlI2wfWPVCxuz1DyktmCJFRiL+XckrifGgQuPYSqR821T5FzLkU
AIWWFTdI+YgQvLKC+7ru8fyVo65yMZ9g3YoF/an01zaPNSbqTLZRrcgQC2LAxFAP
5dDq6bhb2YZ3GcstSqKADqD+qhKwm56Ux9Tv5CtEmYYNz2fPYzsZWuDkSYBdvKKj
BSx4QAZCBm/XADMWDfGd7Tz5wPArHYBMCNLCoohmnPh8fiU9+5EtGw873iOwSVRp
lCd/4kiA4QIDAQABo0IwQDAdBgNVHQ4EFgQUjf4h3ZZt3wASErN5dfpsRAJRS7sw
EgYDVR0TAQH/BAgwBgEB/wIBADALBgNVHQ8EBAMCAQYwDQYJKoZIhvcNAQEMBQAD
ggGBAAEnKgcioXLA8b55NujrM3hrGLN57S78F1pxCZfXJ+qjZHgg2qkN0hVsxJgw
kPeV6GLCIRS7mOgZY25WH9/+JLAWe1FW8SXYOtOZbLb4Okfu1AbiPiYH2N6EjZKZ
b437P424GNzLXW1BJPwUwb7SW6yMtnOOM8sH+J/eCkR3wTiddOeGDNytPhJkNxI9
zLnIz7hz3YmDXdUoQynWH+90FJnCga+FnH5MolhVVQ8fE4rwsUsAu/PxdPUjULK9
E6uMjyygViYr65uF/tI3j/YBnVmS2G2X6NJMXb5jBuN+8Y/l6TriQJ5sFbIdmzxB
nM76nkOwveMwJPOac/koqFfI5Ttaojz26Ca5Wd+EEPNakyaN1cDN3SKKEuL5AzhG
P/n38MG5kbDK8OUxbqLITAZSL5D81RgR0ugmNZfeDbLtjd13AJPVF5PfUzvCjuJO
fRnRXUiPjsFAjFTf6JC5sppkktz+W68IXa/IADt+P1qnWC2u0KrujA7ENG6aTIT8
EQFF+w==
-----END CERTIFICATE-----""")

temp_ca_file = tempfile.NamedTemporaryFile(delete=False)
temp_ca_file.write(AIVEN_CA_CERT.encode("utf-8"))
temp_ca_file.flush()
SSL_CA_PATH = temp_ca_file.name

# ----------------- DATABASE CONNECTION -----------------
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "mysql-20a16630-khushalgarg390-4681.c.aivencloud.com"),
            user=os.environ.get("DB_USER", "avnadmin"),
            password=os.environ.get("DB_PASS", "AVNS_rz2ljygN3FXbvS08LOo"),
            database=os.environ.get("DB_NAME", "defaultdb"),
            port=int(os.environ.get("DB_PORT", 11980)),
            ssl_ca=SSL_CA_PATH
        )
        return conn
    except Exception as e:
        print(f"[DB] Connection error: {e}")
        return None

# ----------------- UPLOAD CONFIG -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def load_excel(path):
    ext = path.rsplit(".", 1)[-1].lower()
    if ext == "csv":
        return pd.read_csv(path)
    return pd.read_excel(path)

# ----------------- HEALTH CHECK -----------------
@app.route("/ping")
def ping():
    return "OK"

@app.route("/ping_db")
def ping_db():
    conn = get_db_connection()
    if not conn:
        return "DB connection failed", 500
    cur = conn.cursor()
    cur.execute("SELECT 1")
    cur.fetchone()
    cur.close()
    conn.close()
    return "DB OK"

# ----------------- INDEX -----------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------- STUDENT/TEACHER PAGES & DASHBOARD & LOGOUT ----------
@app.route("/student_login")
def student_login_page():
    return render_template("student_login.html")

@app.route("/teacher_login")
def teacher_login_page():
    return render_template("teacher_login.html")

@app.route("/student_dashboard")
def student_dashboard():
    if session.get("user_type") != "student":
        return redirect("/student_login")
    roll_no = session.get("student_id")
    conn = get_db_connection()
    if not conn:
        return "DB connection failed"
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM students WHERE roll_no=%s", (roll_no,))
    student = cur.fetchone()
    cur.execute("SELECT * FROM results WHERE roll_no=%s", (roll_no,))
    results = cur.fetchone()
    cur.execute("SELECT * FROM attendance WHERE roll_no=%s", (roll_no,))
    attendance = cur.fetchone()
    cur.close()
    conn.close()
    return render_template("student_dashboard.html", student=student, results=results, attendance=attendance)

@app.route("/teacher_dashboard")
def teacher_dashboard():
    if session.get("user_type") != "teacher":
        return redirect("/teacher_login")
    return render_template(
        "teacher_dashboard.html",
        teacher_name=session.get("teacher_name", ""),
        teacher_email=session.get("teacher_email", "")
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- LOGIN APIs ----------
@app.route("/api/student_login", methods=["POST"])
def api_student_login():
    data = request.get_json(force=True)
    roll_no = (data.get("roll_no") or "").strip()
    password = data.get("password") or ""
    if not roll_no or not password:
        return jsonify({"success": False, "message": "Roll number and password required"})
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "DB connection failed"})
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM students WHERE roll_no=%s AND password=%s", (roll_no, password))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        session.clear()
        session["user_type"] = "student"
        session["student_id"] = row["roll_no"]
        session["student_name"] = row.get("student_name", "")
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid credentials"})

@app.route("/api/teacher_login", methods=["POST"])
def api_teacher_login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"success": False, "message": "Email and password required"})
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "DB connection failed"})
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM teachers WHERE email=%s AND password=%s", (email, password))
    t = cur.fetchone()
    cur.close()
    conn.close()
    if not t:
        return jsonify({"success": False, "message": "Invalid email or password"})
    session.clear()
    session["user_type"] = "teacher"
    session["teacher_email"] = t["email"]
    session["teacher_name"] = t.get("teacher_name") or t.get("name") or ""
    session["teacher_id"] = t.get("teacher_id") or t.get("id")
    return jsonify({"success": True})

# ---------- RUN APP ----------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
