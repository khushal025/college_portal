from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pymysql
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "secret123"

# MySQL connection (PyMySQL)
conn = pymysql.connect(
    host="YOUR_DB_HOST",
    user="YOUR_DB_USER",
    password="YOUR_DB_PASSWORD",
    db="backend",
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------- Routes -----------------

@app.route('/')
def index():
    return redirect('/teacher_login')

# ---------- Teacher Login ----------
@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM teachers WHERE email=%s AND password=%s", (email, password))
            teacher = cursor.fetchone()
            if teacher:
                session['teacher'] = teacher['name']
                return redirect('/teacher_dashboard')
            else:
                return "Invalid Credentials"
    return render_template('teacher_login.html')

# ---------- Teacher Dashboard ----------
@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'teacher' not in session:
        return redirect('/teacher_login')
    return render_template('teacher_dashboard.html', teacher=session['teacher'])

# ---------- API: Get Student Data ----------
@app.route('/api/get_student_data/<roll_no>')
def get_student_data(roll_no):
    with conn.cursor() as cursor:
        # Students table
        cursor.execute("SELECT * FROM students WHERE roll_no=%s", (roll_no,))
        student = cursor.fetchone()
        if not student:
            return jsonify({"error": "Student not found"})

        # Attendance
        cursor.execute("SELECT * FROM attendance WHERE roll_no=%s", (roll_no,))
        attendance = cursor.fetchone()

        # Results
        cursor.execute("SELECT * FROM results WHERE roll_no=%s", (roll_no,))
        results = cursor.fetchone()

    return jsonify({"student": list(student.values()),
                    "attendance": attendance,
                    "results": results})

# ---------- Upload Attendance ----------
@app.route('/upload_attendance', methods=['POST'])
def upload_attendance():
    if 'file' not in request.files:
        return jsonify({"message": "No file uploaded"})
    file = request.files['file']
    if file.filename == "":
        return jsonify({"message": "No file selected"})

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    df = pd.read_excel(filepath)
    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO attendance (roll_no, student_name, father_name, OOPUI, cloud_comp, bi, foai, se, java_script_lab, oopu_script_lab, science_and_society, total_attendance)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE 
                    student_name=VALUES(student_name),
                    father_name=VALUES(father_name),
                    OOPUI=VALUES(OOPUI),
                    cloud_comp=VALUES(cloud_comp),
                    bi=VALUES(bi),
                    foai=VALUES(foai),
                    se=VALUES(se),
                    java_script_lab=VALUES(java_script_lab),
                    oopu_script_lab=VALUES(oopu_script_lab),
                    science_and_society=VALUES(science_and_society),
                    total_attendance=VALUES(total_attendance)
            """, tuple(row))
        conn.commit()
    return jsonify({"message": "Attendance uploaded successfully"})

# ---------- Upload Results ----------
@app.route('/upload_results', methods=['POST'])
def upload_results():
    if 'file' not in request.files:
        return jsonify({"message": "No file uploaded"})
    file = request.files['file']
    if file.filename == "":
        return jsonify({"message": "No file selected"})

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    df = pd.read_excel(filepath)
    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO results (roll_no, student_name, father_name, OOPUI, cloud_comp, bi, foai, se, java_script_lab, oopu_script_lab, science_and_society, sgpa)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                    student_name=VALUES(student_name),
                    father_name=VALUES(father_name),
                    OOPUI=VALUES(OOPUI),
                    cloud_comp=VALUES(cloud_comp),
                    bi=VALUES(bi),
                    foai=VALUES(foai),
                    se=VALUES(se),
                    java_script_lab=VALUES(java_script_lab),
                    oopu_script_lab=VALUES(oopu_script_lab),
                    science_and_society=VALUES(science_and_society),
                    sgpa=VALUES(sgpa)
            """, tuple(row))
        conn.commit()
    return jsonify({"message": "Results uploaded successfully"})

# ---------- Upload Students ----------
@app.route('/upload_students', methods=['POST'])
def upload_students():
    if 'file' not in request.files:
        return jsonify({"message": "No file uploaded"})
    file = request.files['file']
    if file.filename == "":
        return jsonify({"message": "No file selected"})

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    df = pd.read_excel(filepath)
    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO students (roll_no, student_name, father_name, course, semester, email, password, profile_photo)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                    student_name=VALUES(student_name),
                    father_name=VALUES(father_name),
                    course=VALUES(course),
                    semester=VALUES(semester),
                    email=VALUES(email),
                    password=VALUES(password),
                    profile_photo=VALUES(profile_photo)
            """, tuple(row))
        conn.commit()
    return jsonify({"message": "Students uploaded successfully"})

# ---------- Logout ----------
@app.route('/logout')
def logout():
    session.pop('teacher', None)
    return redirect('/teacher_login')

# ---------- Run App ----------
if __name__ == "__main__":
    app.run(debug=True)
