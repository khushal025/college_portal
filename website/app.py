# app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ---------- DATABASE CONFIGURATION WITH SSL ----------
cert_path = os.path.join(os.getcwd(), "cert.pem")  # certificate file path
with open(cert_path, "w") as f:
    f.write("""-----BEGIN CERTIFICATE-----
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

try:
    db = mysql.connector.connect(
        host="mysql-20a16630-khushalgarg390-4681.c.aivencloud.com",
        user="avnadmin",
        password="AVNS_rz2ljygN",
        database="defaultdb",
        port=11980,
        ssl_ca=cert_path
    )
    cursor = db.cursor(dictionary=True)
    print("Connected to MySQL with SSL ✅")
except mysql.connector.Error as e:
    print("MySQL SSL Connection Error:", e)

# ---------- ROUTES ----------

@app.route('/')
def home():
    return render_template('index.html')

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

@app.route('/teacher_dashboard')
def teacher_dashboard():
    teacher_name = request.args.get('teacher_name', 'Teacher')
    return render_template('teacher_dashboard.html', teacher_name=teacher_name)

@app.route('/api/get_student_data/<roll_no>')
def get_student_data(roll_no):
    cursor.execute("SELECT * FROM students WHERE roll_no=%s", (roll_no,))
    student = cursor.fetchone()
    if not student:
        return jsonify({"error": "Student not found"})
    cursor.execute("SELECT * FROM attendance WHERE roll_no=%s", (roll_no,))
    attendance = cursor.fetchall()
    cursor.execute("SELECT * FROM results WHERE roll_no=%s", (roll_no,))
    results = cursor.fetchall()
    return jsonify({"student": list(student.values()), "attendance": attendance, "results": results})

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

@app.route('/upload_<file_type>', methods=['POST'])
def upload_file(file_type):
    file = request.files.get('file')
    if not file:
        return jsonify({"message": "No file uploaded"}), 400
    save_path = os.path.join('uploads', file.filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(save_path)
    return jsonify({"message": f"{file_type.capitalize()} uploaded successfully"})

# ---------- RUN SERVER ----------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
