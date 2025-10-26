# app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)

# ---------- DATABASE CONFIGURATION ----------
db = mysql.connector.connect(
    host="mysql-20a16630-khushalgarg390-4681.c.aivencloud.com",
    user="avnadmin",
    password="AVNS_rz2ljygN",
    database="defaultdb",
    port=11980
)
cursor = db.cursor(dictionary=True)

# ---------- ROUTES ----------

@app.route('/')
def home():
    return render_template('index.html')  # Login page

# ------------- TEACHER LOGIN -------------
@app.route('/api/teacher_login', methods=['POST'])
def teacher_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    cursor.execute("SELECT * FROM teachers WHERE username=%s AND password=%s", (username, password))
    teacher = cursor.fetchone()
    if teacher:
        return jsonify({"success": True, "message": "Login successful", "teacher_name": teacher['name']})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

# ------------- STUDENT LOGIN -------------
@app.route('/api/student_login', methods=['POST'])
def student_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    cursor.execute("SELECT * FROM students WHERE roll_no=%s AND password=%s", (username, password))
    student = cursor.fetchone()
    if student:
        return jsonify({"success": True, "message": "Login successful", "student_name": student['student_name']})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

# ------------- TEACHER DASHBOARD -------------
@app.route('/teacher_dashboard')
def teacher_dashboard():
    teacher_name = request.args.get('teacher_name', 'Teacher')
    return render_template('teacher_dashboard.html', teacher_name=teacher_name)

# ------------- GET STUDENT DATA -------------
@app.route('/api/get_student_data/<roll_no>')
def get_student_data(roll_no):
    cursor.execute("SELECT * FROM students WHERE roll_no=%s", (roll_no,))
    student = cursor.fetchone()
    if not student:
        return jsonify({"error": "Student not found"})

    # Attendance
    cursor.execute("SELECT * FROM attendance WHERE roll_no=%s", (roll_no,))
    attendance = cursor.fetchall()

    # Results
    cursor.execute("SELECT * FROM results WHERE roll_no=%s", (roll_no,))
    results = cursor.fetchall()

    return jsonify({"student": list(student.values()), "attendance": attendance, "results": results})

# ------------- ADD STUDENT (MANUAL) -------------
@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.json
    roll_no = data.get('roll_no')
    student_name = data.get('student_name')
    father_name = data.get('father_name')
    email = data.get('email')

    cursor.execute("INSERT INTO students (roll_no, student_name, father_name, email) VALUES (%s,%s,%s,%s)",
                   (roll_no, student_name, father_name, email))
    db.commit()
    return jsonify({"message": f"Student {student_name} added successfully"})

# ------------- UPLOAD FILES -------------
@app.route('/upload_<file_type>', methods=['POST'])
def upload_file(file_type):
    file = request.files.get('file')
    if not file:
        return jsonify({"message": "No file uploaded"}), 400

    save_path = os.path.join('uploads', file.filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(save_path)

    # TODO: Parse Excel and insert into DB if needed
    return jsonify({"message": f"{file_type.capitalize()} uploaded successfully"})

# ------------- RUN SERVER -------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
