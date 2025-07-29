from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # change this in production


# ---------- Initialize Database ----------
def init_db():
    with sqlite3.connect('students.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            roll TEXT,
            class TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT,
            date TEXT,
            status TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT,
            grade TEXT
        )''')
        # Create default admin user if not exists
        c.execute("SELECT * FROM users WHERE username='admin'")
        if not c.fetchone():
            hashed_pw = generate_password_hash('admin123')
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', hashed_pw))

init_db()


# ---------- Routes ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        conn = sqlite3.connect('students.db')
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (user,))
        result = c.fetchone()
        if result and check_password_hash(result[0], pw):
            session['user'] = user
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    students = c.fetchall()
    return render_template('index.html', students=students)


@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        roll = request.form['roll']
        student_class = request.form['class']
        with sqlite3.connect('students.db') as conn:
            conn.execute("INSERT INTO students (name, roll, class) VALUES (?, ?, ?)", (name, roll, student_class))
        return redirect(url_for('index'))

    return render_template('add_student.html')


@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    students = c.fetchall()

    if request.method == 'POST':
        subject = request.form['subject']
        date = request.form['date']
        for student in students:
            status = request.form.get(f'status_{student[0]}')
            conn.execute("INSERT INTO attendance (student_id, subject, date, status) VALUES (?, ?, ?, ?)",
                         (student[0], subject, date, status))
        conn.commit()
        return redirect(url_for('index'))

    return render_template('attendance.html', students=students)


@app.route('/grades', methods=['GET', 'POST'])
def grades():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    students = c.fetchall()

    if request.method == 'POST':
        subject = request.form['subject']
        for student in students:
            grade = request.form.get(f'grade_{student[0]}')
            conn.execute("INSERT INTO grades (student_id, subject, grade) VALUES (?, ?, ?)",
                         (student[0], subject, grade))
        conn.commit()
        return redirect(url_for('index'))

    return render_template('grades.html', students=students)


@app.route('/student/<int:student_id>')
def student_info(student_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    c.execute("SELECT * FROM students WHERE id=?", (student_id,))
    student = c.fetchone()

    c.execute("SELECT * FROM attendance WHERE student_id=?", (student_id,))
    attendance = c.fetchall()

    c.execute("SELECT * FROM grades WHERE student_id=?", (student_id,))
    grades = c.fetchall()

    return render_template('student_info.html', student=student, attendance=attendance, grades=grades)


if __name__ == '__main__':
    app.run(debug=True)
