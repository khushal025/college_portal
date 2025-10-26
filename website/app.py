from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "secret_key"

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Khushal@8755'
app.config['MYSQL_DB'] = 'backend'

mysql = MySQL(app)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------------- Teacher Login ----------------
@app.route('/teacher_login', methods=['GET','POST'])
def teacher_login():
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM teachers WHERE email=%s AND password=%s",(email,password))
        teacher = cur.fetchone()
        if teacher:
            session['teacher_id'] = teacher[0]
            session['teacher_name'] = teacher[1]
            return redirect('/teacher_dashboard')
        else:
            return "Invalid credentials"
    return render_template('teacher_login.html')

# ---------------- Teacher Dashboard ----------------
@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        return redirect('/teacher_login')
    return render_template('teacher_dashboard.html', teacher_name=session['teacher_name'])

# ---------------- Get Student Data API ----------------
@app.route('/api/get_student_data/<roll_no>')
def get_student_data(roll_no):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM students WHERE roll_no=%s", (roll_no,))
    student = cur.fetchone()
    if not student:
        return jsonify({'error':'Student not found'})
    
    cur.execute("SELECT * FROM attendance WHERE roll_no=%s", (roll_no,))
    attendance = cur.fetchone()
    cur.execute("SELECT * FROM results WHERE roll_no=%s", (roll_no,))
    results = cur.fetchone()
    
    return jsonify({
        'student': list(student),
        'attendance': dict(zip([desc[0] for desc in cur.description], attendance)) if attendance else {},
        'results': dict(zip([desc[0] for desc in cur.description], results)) if results else {}
    })

# ---------------- Upload Excel Routes ----------------
def upload_file(table_type):
    if 'teacher_id' not in session:
        return jsonify({'message':'Unauthorized'}), 401
    file = request.files.get('file')
    if not file:
        return jsonify({'message':'No file selected'}), 400
    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filename)
    try:
        df = pd.read_excel(filename)
        cur = mysql.connection.cursor()
        for _, row in df.iterrows():
            roll_no = row['roll_no']
            cur.execute(f"SELECT * FROM {table_type} WHERE roll_no=%s", (roll_no,))
            exists = cur.fetchone()
            if exists:
                # update
                cols = ', '.join([f"{col}=%s" for col in df.columns if col != 'roll_no'])
                values = [row[col] for col in df.columns if col != 'roll_no']
                values.append(roll_no)
                cur.execute(f"UPDATE {table_type} SET {cols} WHERE roll_no=%s", values)
            else:
                # insert
                cols = ', '.join(df.columns)
                placeholders = ','.join(['%s']*len(df.columns))
                values = tuple(row[col] for col in df.columns)
                cur.execute(f"INSERT INTO {table_type} ({cols}) VALUES ({placeholders})", values)
        mysql.connection.commit()
        return jsonify({'message': f"{table_type} updated successfully!"})
    except Exception as e:
        return jsonify({'message': f"Error: {str(e)}"})

@app.route('/upload_attendance', methods=['POST'])
def upload_attendance():
    return upload_file('attendance')

@app.route('/upload_results', methods=['POST'])
def upload_results():
    return upload_file('results')

@app.route('/upload_students', methods=['POST'])
def upload_students():
    return upload_file('students')

# ---------------- Manual Add Student ----------------
@app.route('/add_student', methods=['POST'])
def add_student():
    if 'teacher_id' not in session:
        return jsonify({'message':'Unauthorized'}), 401
    data = request.get_json()
    cur = mysql.connection.cursor()
    try:
        cur.execute("INSERT INTO students (roll_no, student_name, father_name, email) VALUES (%s,%s,%s,%s)",
                    (data['roll_no'], data['student_name'], data['father_name'], data['email']))
        mysql.connection.commit()
        return jsonify({'message':'Student added successfully!'})
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'})

# ---------------- Logout ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/teacher_login')

if __name__ == "__main__":
    app.run(debug=True)

