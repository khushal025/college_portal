from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Upload folder config
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ✅ Safe database connection with error handling
try:
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),   # changed from DB_PASS → DB_PASSWORD
        database=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT", 3306)
    )
    cursor = db.cursor(dictionary=True)
    print("✅ Database connected successfully!")
except mysql.connector.Error as e:
    print(f"❌ Database connection failed: {e}")
    db = None
    cursor = None

# Helper: allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ====== ROUTES ======

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/teacher')
def teacher_dashboard():
    if not cursor:
        return "Database not connected!"
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    return render_template('teacher.html', students=students)

@app.route('/student', methods=['GET', 'POST'])
def student_login():
    if not cursor:
        return "Database not connected!"
    if request.method == 'POST':
        roll_no = request.form.get('roll_no')
        cursor.execute("SELECT * FROM students WHERE roll_no=%s", (roll_no,))
        student = cursor.fetchone()
        if student:
            return render_template('student_dashboard.html', student=student)
        else:
            flash("Invalid Roll Number", "danger")
            return redirect(url_for('student_login'))
    return render_template('student_login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                if filename.endswith(('xlsx', 'xls')):
                    df = pd.read_excel(filepath)
                else:
                    df = pd.read_csv(filepath)

                for _, row in df.iterrows():
                    cursor.execute("""
                        INSERT INTO students (roll_no, name, marks)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE name=%s, marks=%s
                    """, (row['roll_no'], row['name'], row['marks'], row['name'], row['marks']))
                db.commit()
                flash('File uploaded and DB updated successfully!', 'success')
            except Exception as e:
                flash(f'Error processing file: {e}', 'danger')
            return redirect(url_for('upload_file'))

    return render_template('upload.html')

# ✅ Render-compatible run command
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
