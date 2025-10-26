from flask import Flask, render_template, request, jsonify
import mysql.connector
import pandas as pd

app = Flask(__name__)

# --- Database Configuration ---
db_config = {
    'host': 'mysql-20a16630-khushalgarg390-4681.c.aivencloud.com',
    'user': 'avnadmin',
    'password': 'AVNS_rz2ljygN',
    'database': 'defaultdb',
    'port': 11980
}

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/teacher_dashboard')
def teacher_dashboard():
    teacher_name = "Teacher ABC"  # Example, can fetch from session
    return render_template('teacher_dashboard.html', teacher_name=teacher_name)

# --- API to get student data ---
@app.route('/api/get_student_data/<roll_no>')
def get_student_data(roll_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM students WHERE roll_no=%s", (roll_no,))
        student = cursor.fetchone()
        if not student:
            return jsonify({'error': 'Student not found'})
        
        # Attendance
        cursor.execute("SELECT * FROM attendance WHERE student_roll=%s", (roll_no,))
        attendance = cursor.fetchall()

        # Results
        cursor.execute("SELECT * FROM results WHERE student_roll=%s", (roll_no,))
        results = cursor.fetchall()

        return jsonify({
            'student': student,
            'attendance': attendance,
            'results': results
        })
    finally:
        cursor.close()
        conn.close()

# --- Add single student manually ---
@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.json
    roll_no = data.get('roll_no')
    student_name = data.get('student_name')
    father_name = data.get('father_name')
    email = data.get('email')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO students (roll_no, student_name, father_name, email) VALUES (%s, %s, %s, %s)",
                       (roll_no, student_name, father_name, email))
        conn.commit()
        return jsonify({'message': 'Student added successfully'})
    except mysql.connector.Error as e:
        return jsonify({'error': str(e)})
    finally:
        cursor.close()
        conn.close()

# --- Upload Excel for bulk students ---
@app.route('/upload_students', methods=['POST'])
def upload_students():
    file = request.files['file']
    df = pd.read_excel(file)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for _, row in df.iterrows():
            cursor.execute(
                "INSERT INTO students (roll_no, student_name, father_name, email) VALUES (%s,%s,%s,%s)",
                (row['roll_no'], row['student_name'], row['father_name'], row['email'])
            )
        conn.commit()
        return jsonify({'message': 'Students uploaded successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        cursor.close()
        conn.close()

# --- Upload Attendance ---
@app.route('/upload_attendance', methods=['POST'])
def upload_attendance():
    file = request.files['file']
    df = pd.read_excel(file)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for _, row in df.iterrows():
            cursor.execute(
                "INSERT INTO attendance (student_roll, date, status) VALUES (%s,%s,%s)",
                (row['student_roll'], row['date'], row['status'])
            )
        conn.commit()
        return jsonify({'message': 'Attendance uploaded successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        cursor.close()
        conn.close()

# --- Upload Results ---
@app.route('/upload_results', methods=['POST'])
def upload_results():
    file = request.files['file']
    df = pd.read_excel(file)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for _, row in df.iterrows():
            cursor.execute(
                "INSERT INTO results (student_roll, subject, marks) VALUES (%s,%s,%s)",
                (row['student_roll'], row['subject'], row['marks'])
            )
        conn.commit()
        return jsonify({'message': 'Results uploaded successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)

