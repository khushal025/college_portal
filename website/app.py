from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
import os, pandas as pd, mysql.connector
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get("SESSION_SECRET","Khushal@8755")

# ---------- DB ----------
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            database=os.environ.get("DB_NAME"),
            port=int(os.environ.get("DB_PORT",3306)),
            ssl_disabled=False
        )
    except Exception as e:
        print(f"[DB] error: {e}")
        return None

# ---------- Upload ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"csv","xlsx","xls"}
app.config["UPLOAD_FOLDER"]=UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS

def load_table_from_excel(path):
    ext = path.rsplit(".",1)[-1].lower()
    return pd.read_csv(path) if ext=="csv" else pd.read_excel(path)

# ---------- Pages ----------
@app.route("/teacher_dashboard")
def teacher_dashboard():
    if session.get("user_type")!="teacher": return redirect("/teacher_login")
    return render_template("teacher_dashboard.html", teacher_name=session.get("teacher_name",""), teacher_email=session.get("teacher_email",""))

@app.route("/teacher_login")
def teacher_login_page(): return render_template("teacher_login.html")

# ---------- Auth ----------
@app.route("/api/teacher_login", methods=["POST"])
def api_teacher_login():
    try:
        data = request.get_json(force=True)
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        if not email or not password: return jsonify({"success":False,"message":"Email and password required"})
        conn = get_db_connection()
        if not conn: return jsonify({"success":False,"message":"DB failed"})
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM teachers WHERE email=%s AND password=%s",(email,password))
        t = cur.fetchone()
        cur.close(); conn.close()
        if not t: return jsonify({"success":False,"message":"Invalid credentials"})
        session.clear()
        session.update({"user_type":"teacher","teacher_email":t["email"],"teacher_name":t.get("teacher_name",t.get("name",""))})
        return jsonify({"success":True})
    except Exception as e:
        print(f"[teacher_login] {e}")
        return jsonify({"success":False,"message":"Login failed"})

# ---------- Student Data ----------
@app.route("/api/get_student_data/<roll_no>")
def api_get_student_data(roll_no):
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"success":False})
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM students WHERE roll_no=%s",(roll_no,))
        student = cur.fetchone()
        cur.execute("SELECT * FROM results WHERE roll_no=%s",(roll_no,))
        results = cur.fetchone()
        cur.execute("SELECT * FROM attendance WHERE roll_no=%s",(roll_no,))
        attendance = cur.fetchone()
        cur.close(); conn.close()
        if not student: return jsonify({"success":False})
        return jsonify({"success":True,"data":{"student":student,"results":results,"attendance":attendance}})
    except Exception as e:
        print(f"[get_student_data] {e}")
        return jsonify({"success":False})

# ---------- Excel Upload ----------
@app.route("/api/upload_excel", methods=["POST"])
def api_upload_excel():
    try:
        if 'file' not in request.files: return jsonify({"success":False,"message":"No file part"})
        file = request.files['file']
        if file.filename=="" or not allowed_file(file.filename): return jsonify({"success":False,"message":"Invalid file"})
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        df = load_table_from_excel(path)
        table_name = request.form.get("table_name")
        if not table_name: return jsonify({"success":False,"message":"Missing table_name"})
        conn = get_db_connection()
        if not conn: return jsonify({"success":False,"message":"DB connection failed"})
        cur = conn.cursor()
        cols = ",".join(df.columns)
        vals = ",".join(["%s"]*len(df.columns))
        for row in df.itertuples(index=False,name=None):
            cur.execute(f"INSERT INTO {table_name} ({cols}) VALUES ({vals})", row)
        conn.commit(); cur.close(); conn.close()
        return jsonify({"success":True,"message":"Uploaded successfully"})
    except Exception as e:
        print(f"[upload_excel] {e}")
        return jsonify({"success":False,"message":"Upload failed"})

# ---------- Run ----------
if __name__=="__main__":
    app.run(debug=True)
