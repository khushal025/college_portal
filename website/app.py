from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_mysqldb import MySQL
import pandas as pd

app = Flask(__name__)

# ---------- MySQL Configuration ----------
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'           # apka MySQL user
app.config['MYSQL_PASSWORD'] = ''           # apka MySQL password
app.config['MYSQL_DB'] = 'backend'

mysql = MySQL(app)

# ---------- Teacher Login ----------
@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM teachers WHERE email=%s AND password=%s", (email, password))
        teacher = cursor.fetchone()
        if teacher:
            return redirect(url_for('teacher_dashboard', teacher_id=teacher[0]))
        else:
            return "Invalid credentials"
    return render_template('teacher_login.html')

# ---------- Teacher Dashboard ----------
@app.route('/teacher_dashboard/<int:teacher_id>')
def teacher_dashboard(teacher_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT name FROM teachers WHERE id=%s", (teacher_id,))
    teacher = cursor.fetchone()
    return render_template('teacher_dashboard.html', teacher=teacher[0], teacher_id=teacher_id)

# ---------- Student Search (Read-Only) ----------
@app.route('/api/get_student_data/<roll_no>')
def get_student_data(roll_no):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT roll_no, student_name, father_name, course, semester, email, profile_photo FROM students WHERE roll_no=%s", (roll_no,))
    student = cursor.fetchone()
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    cursor.execute("SELECT * FROM attendance WHERE roll_no=%s", (roll_no,))
    attendance = cursor.fetchone()

    cursor.execute("SELECT * FROM results WHERE roll_no=%s", (roll_no,))
    results = cursor.fetchone()

    return jsonify({
        'student': student,
        'attendance': attendance,
        'results': results
    })

# ---------- Excel Upload Helper ----------
def update_table_from_excel(file, table_name):
    df = pd.read_excel(file)
    cursor = mysql.connection.cursor()

    for _, row in df.iterrows():
        cols = ','.join(df.columns)
        placeholders = ','.join(['%s']*len(df.columns))
        update_str = ','.join([f"{col}=VALUES({col})" for col in df.columns])
        query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_str}"
        cursor.execute(query, tuple(row))
    
    mysql.connection.commit()
    cursor.close()

# ---------- Upload Routes ----------
@app.route('/upload_attendance', methods=['POST'])
def upload_attendance():
    file = request.files['file']
    update_table_from_excel(file, 'attendance')
    return jsonify({'success': True, 'message': 'Attendance updated successfully'})

@app.route('/upload_results', methods=['POST'])
def upload_results():
    file = request.files['file']
    update_table_from_excel(file, 'results')
    return jsonify({'success': True, 'message': 'Results updated successfully'})

@app.route('/upload_students', methods=['POST'])
def upload_students():
    file = request.files['file']
    update_table_from_excel(file, 'students')
    return jsonify({'success': True, 'message': 'Students added/updated successfully'})

# ---------- Run Flask App ----------
if __name__ == '__main__':
    app.run(debug=True)

