from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import os
import pymysql
pymysql.install_as_MySQLdb()
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = "supersecretkey"

# MySQL config
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'avnadmin'
app.config['MYSQL_PASSWORD'] = 'AVNS_rz2ljygN'
app.config['MYSQL_DB'] = 'backend'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# -------------------
# LOGIN ROUTES
# -------------------
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/teacher_login', methods=['POST'])
def teacher_login():
    email = request.form['email']
    password = request.form['password']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM teachers WHERE email=%s AND password=%s", (email, password))
    teacher = cur.fetchone()
    if teacher:
        session['teacher_id'] = teacher['id']
        session['teacher_name'] = teacher['name']
        return redirect(url_for('teacher_dashboard'))
    else:
        flash("Invalid credentials", "danger")
        return redirect(url_for('index'))

# -------------------
# TEACHER DASHBOARD
# -------------------
@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        return redirect(url_for('index'))
    return render_template('teacher_dashboard.html', teacher_name=session['teacher_name'])

# -------------------
# SEARCH STUDENT (READ-ONLY)
# -------------------
@app.route('/search_student', methods=['GET', 'POST'])
def search_student():
    if 'teacher_id' not in session:
        return redirect(url_for('index'))
    student = None
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM students WHERE roll_no=%s", (roll_no,))
        student = cur.fetchone()
    return render_template('search_student.html', student=student)

# -------------------
# UPLOAD ATTENDANCE / RESULTS
# -------------------
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'teacher_id' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash("No file selected", "danger")
            return redirect(request.url)
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        try:
            df = pd.read_excel(filename)
            table_type = request.form['type']  # 'attendance' or 'results'
            cur = mysql.connection.cursor()
            for _, row in df.iterrows():
                roll_no = row['roll_no']
                cur.execute(f"SELECT * FROM {table_type} WHERE roll_no=%s", (roll_no,))
                exists = cur.fetchone()
                if exists:
                    # Update existing record
                    cols = ', '.join([f"{col}=%s" for col in df.columns if col != 'roll_no'])
                    values = [row[col] for col in df.columns if col != 'roll_no']
                    values.append(roll_no)
                    cur.execute(f"UPDATE {table_type} SET {cols} WHERE roll_no=%s", values)
                else:
                    # Insert new record
                    cols = ', '.join(df.columns)
                    vals = tuple(row[col] for col in df.columns)
                    placeholders = ','.join(['%s']*len(df.columns))
                    cur.execute(f"INSERT INTO {table_type} ({cols}) VALUES ({placeholders})", vals)
            mysql.connection.commit()
            flash(f"{table_type.capitalize()} updated successfully!", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('teacher_dashboard'))
    return render_template('upload.html')

# -------------------
# ADD NEW STUDENT
# -------------------
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'teacher_id' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        name = request.form['student_name']
        father_name = request.form['father_name']
        course = request.form['course']
        semester = request.form['semester']
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO students (roll_no, student_name, father_name, course, semester, email, password) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (roll_no, name, father_name, course, semester, email, password))
            mysql.connection.commit()
            flash("Student added successfully!", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('teacher_dashboard'))
    return render_template('add_student.html')

# -------------------
# LOGOUT
# -------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# -------------------
# RUN
# -------------------
if __name__ == '__main__':
    app.run(debug=True)
