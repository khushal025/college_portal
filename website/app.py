from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
import os
import pandas as pd
import mysql.connector
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get("SESSION_SECRET", "Khushal@8755")

# ---------- Database ----------
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            database=os.environ.get("DB_NAME"),
            port=int(os.environ.get("DB_PORT", 3306)),
            ssl_disabled=False
        )
        return conn
    except Exception as e:
        print(f"[DB] error: {e}")
        return None

# ---------- Uploads ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- Health ----------
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

# ---------- Pages ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/student_login")
def student_login_page():
    return render_template("student_login.html")

@app.route("/teacher_login")
def teacher_login_page():
    return render_template("teacher_login.html")

@app.route("/student_dashboard")
def student_dashboard():
    if "student_id" not in session or session.get("user_type") != "student":
        return redirect("/student_login")
    roll_no = session["student_id"]
    conn = get_db_connection()
    if not conn:
        return "Database connection failed!"
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM students WHERE roll_no=%s", (roll_no,))
        student = cur.fetchone()
        cur.execute("SELECT * FROM results WHERE roll_no=%s", (roll_no,))
        results = cur.fetchone()
        cur.execute("SELECT * FROM attendance WHERE roll_no=%s", (roll_no,))
        attendance = cur.fetchone()
    finally:
        cur.close()
        conn.close()
    if not student:
        return redirect("/student_login")
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

# ---------- Auth APIs ----------
@app.route("/api/student_login", methods=["POST"])
def api_student_login():
    try:
        data = request.get_json(force=True)
        roll_no = (data.get("roll_no") or "").strip()
        password = data.get("password") or ""
        if not roll_no or not password:
            return jsonify({"success": False, "message": "Roll number and password required"})
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database connection failed"})
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM students WHERE roll_no=%s AND password=%s", (roll_no, password))
            row = cur.fetchone()
        finally:
            cur.close()
            conn.close()
        if row:
            session.clear()
            session["user_type"] = "student"
            session["student_id"] = row["roll_no"]
            session["student_name"] = row.get("student_name", "")
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Invalid credentials"})
    except Exception as e:
        print(f"[student_login] {e}")
        return jsonify({"success": False, "message": "Login failed"})

@app.route("/api/teacher_login", methods=["POST"])
def api_teacher_login():
    try:
        data = request.get_json(force=True)
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        if not email or not password:
            return jsonify({"success": False, "message": "Email and password required"})
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database connection failed"})
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM teachers WHERE email=%s AND password=%s", (email, password))
            t = cur.fetchone()
        finally:
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
    except Exception as e:
        print(f"[teacher_login] {e}")
        return jsonify({"success": False, "message": "Login failed"})

# ---------- Data APIs ----------
@app.route("/api/get_student_data/<roll_no>")
def get_student_data(roll_no):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database connection failed"})
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM students WHERE roll_no=%s", (roll_no,))
        student = cur.fetchone()
        cur.execute("SELECT * FROM results WHERE roll_no=%s", (roll_no,))
        results = cur.fetchone()
        cur.execute("SELECT * FROM attendance WHERE roll_no=%s", (roll_no,))
        attendance = cur.fetchone()
        cur.close()
        conn.close()
        if student:
            return jsonify({"success": True, "data": {"student": student, "results": results, "attendance": attendance}})
        else:
            return jsonify({"success": False, "message": "Student not found"})
    except Exception as e:
        print(f"[get_student_data] {e}")
        return jsonify({"success": False, "message": "Failed to fetch data"})

@app.route("/update_student_profile", methods=["POST"])
def update_student_profile():
    try:
        data = request.get_json(force=True)
        roll_no = data.get("roll_no")
        if not roll_no:
            return jsonify({"success": False, "message": "Roll number required"})
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database connection failed"})
        cur = conn.cursor()
        q = """
        UPDATE students SET student_name=%s, father_name=%s, course=%s, semester=%s, email=%s
        WHERE roll_no=%s
        """
        cur.execute(q, (data.get("student_name"), data.get("father_name"), data.get("course"),
                        data.get("semester"), data.get("email"), roll_no))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        print(f"[update_student_profile] {e}")
        return jsonify({"success": False, "message": "Update failed"})

@app.route("/update_student_attendance", methods=["POST"])
def update_student_attendance():
    try:
        data = request.get_json(force=True)
        roll_no = data.get("roll_no")
        if not roll_no:
            return jsonify({"success": False, "message": "Roll number required"})
        fields = ["OOPUI","cloud_comp","bi","foai","se","java_script_lab","total_attendance"]
        vals = [data.get(f, 0) for f in fields]
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database connection failed"})
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM attendance WHERE roll_no=%s", (roll_no,))
        exists = cur.fetchone()
        if exists:
            q = """
            UPDATE attendance SET OOPUI=%s, cloud_comp=%s, bi=%s, foai=%s, se=%s, 
                java_script_lab=%s, total_attendance=%s
            WHERE roll_no=%s
            """
            cur.execute(q, (*vals, roll_no))
        else:
            q = """
            INSERT INTO attendance (roll_no, OOPUI, cloud_comp, bi, foai, se, java_script_lab, total_attendance)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """
            cur.execute(q, (roll_no, *vals))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        print(f"[update_student_attendance] {e}")
        return jsonify({"success": False, "message": "Update failed"})

# ---------- Bulk Uploads ----------
def load_table_from_excel(path):
    ext = path.rsplit(".", 1)[-1].lower()
    if ext == "csv":
        return pd.read_csv(path)
    return pd.read_excel(path)

@app.route("/upload_attendance", methods=["POST"])
def upload_attendance():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file selected"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"success": False, "message": "No file selected"}), 400
    if not allowed_file(f.filename):
        return jsonify({"success": False, "message": "Invalid file type (csv/xlsx/xls)"}), 400
    path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(f.filename))
    f.save(path)
    try:
        df = load_table_from_excel(path)
        df.columns = [str(c).strip().lower() for c in df.columns]
        required = {"roll_no","oopui","cloud_comp","bi","foai","se","java_script_lab","total_attendance"}
        missing = required - set(df.columns)
        if missing:
            return jsonify({"success": False, "message": f"Missing columns: {sorted(missing)}"}), 400
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "DB connect failed"}), 500
        cur = conn.cursor()
        ins = upd = skip = 0
        for _, row in df.iterrows():
            roll = str(row["roll_no"]).strip()
            if not roll:
                skip += 1
                continue
            cur.execute("SELECT 1 FROM attendance WHERE roll_no=%s", (roll,))
            exists = cur.fetchone()
            values = (
                row.get("oopui", 0), row.get("cloud_comp", 0), row.get("bi", 0),
                row.get("foai", 0), row.get("se", 0), row.get("java_script_lab", 0),
                row.get("total_attendance", 0)
            )
            if exists:
                cur.execute("""UPDATE attendance SET OOPUI=%s, cloud_comp=%s, bi=%s, foai=%s, se=%s,
                               java_script_lab=%s, total_attendance=%s WHERE roll_no=%s""",
                            (*values, roll))
                upd += 1
            else:
                cur.execute("""INSERT INTO attendance (roll_no, OOPUI, cloud_comp, bi, foai, se,
                               java_script_lab, total_attendance) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (roll, *values))
                ins += 1
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "summary": {"inserted": ins, "updated": upd, "skipped": skip}})
    except Exception as e:
        return jsonify({"success": False, "message": f"Upload failed: {e}"}), 500
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except:
            pass

@app.route("/upload_results", methods=["POST"])
def upload_results():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file selected"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"success": False, "message": "No file selected"}), 400
    if not allowed_file(f.filename):
        return jsonify({"success": False, "message": "Invalid file type (csv/xlsx/xls)"}), 400
    path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(f.filename))
    f.save(path)
    try:
        df = load_table_from_excel(path)
        df.columns = [str(c).strip().lower() for c in df.columns]
        if "science_and_society" not in df.columns:
            df["science_and_society"] = 0
        must_have = {"roll_no", "oopui","cloud_comp","bi","foai","se","java_script_lab","sgpa"}
        missing = must_have - set(df.columns)
        if missing:
            return jsonify({"success": False, "message": f"Missing columns: {sorted(missing)}"}), 400
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "DB connect failed"}), 500
        cur = conn.cursor()
        ins = upd = skip = 0
        for _, row in df.iterrows():
            roll = str(row["roll_no"]).strip()
            if not roll:
                skip += 1
                continue
            cur.execute("SELECT 1 FROM results WHERE roll_no=%s", (roll,))
            exists = cur.fetchone()
            values = (
                row.get("oopui", 0), row.get("cloud_comp", 0), row.get("bi", 0),
                row.get("foai", 0), row.get("se", 0), row.get("java_script_lab", 0),
                row.get("science_and_society", 0), row.get("sgpa", 0)
            )
            if exists:
                cur.execute("""UPDATE results SET OOPUI=%s, cloud_comp=%s, bi=%s, foai=%s, se=%s,
                               java_script_lab=%s, science_and_society=%s, sgpa=%s WHERE roll_no=%s""",
                            (*values, roll))
                upd += 1
            else:
                cur.execute("""INSERT INTO results (roll_no, OOPUI, cloud_comp, bi, foai, se, 
                               java_script_lab, science_and_society, sgpa)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (roll, *values))
                ins += 1
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "summary": {"inserted": ins, "updated": upd, "skipped": skip}})
    except Exception as e:
        return jsonify({"success": False, "message": f"Upload failed: {e}"}), 500
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except:
            pass

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    # For local dev only; Render uses gunicorn start command
    app.run(debug=True, host="0.0.0.0", port=5000)

