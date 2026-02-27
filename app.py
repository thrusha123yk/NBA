from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from collections import Counter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

app = Flask(__name__)

# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            usn TEXT NOT NULL,
            event_type TEXT NOT NULL,
            level TEXT NOT NULL,
            year INTEGER NOT NULL,
            prize TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- HOME ----------------

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/student')
def student():
    return render_template('student_menu.html')

@app.route('/teacher')
def teacher():
    return render_template('teacher_menu.html')

# ---------------- ADD ----------------

@app.route('/add', methods=['GET','POST'])
def add():
    conn = get_db()

    if request.method == 'POST':
        conn.execute('''
            INSERT INTO achievements
            (name, usn, event_type, level, year, prize)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            request.form['name'],
            request.form['usn'],
            request.form['event_type'],
            request.form['level'],
            int(request.form['year']),
            request.form['prize']
        ))
        conn.commit()
        conn.close()
        return redirect('/')

    conn.close()
    return render_template('add.html')

# ---------------- STUDENT VIEW ----------------

@app.route('/student/view', methods=['GET','POST'])
def student_view():
    data = None
    total = 0
    event_count = None

    if request.method == 'POST':
        usn = request.form['usn']
        conn = get_db()
        data = conn.execute(
            "SELECT * FROM achievements WHERE usn=?",
            (usn,)
        ).fetchall()
        conn.close()

        total = len(data)
        events = [row['event_type'] for row in data]
        event_count = Counter(events)

    return render_template('student_view.html',
                           data=data,
                           total=total,
                           event_count=event_count)

# ---------------- STUDENT REPORT ----------------

@app.route('/student/report', methods=['GET','POST'])
def student_report():
    summary = None

    if request.method == 'POST':
        usn = request.form['usn']
        conn = get_db()
        data = conn.execute(
            "SELECT * FROM achievements WHERE usn=?",
            (usn,)
        ).fetchall()
        conn.close()

        total = len(data)
        events = [row['event_type'] for row in data]
        event_count = Counter(events)

        parts = [f"{v} {k}(s)" for k,v in event_count.items()]
        summary = f"The student participated in {total} professional activities including " + ", ".join(parts) + "."

    return render_template('student_report.html', summary=summary)

# ---------------- TEACHER DASHBOARD ----------------

@app.route('/dashboard')
def dashboard():
    year = request.args.get('year')
    event = request.args.get('event')

    conn = get_db()
    query = "SELECT * FROM achievements WHERE 1=1"
    params = []

    if year:
        query += " AND year=?"
        params.append(year)

    if event:
        query += " AND event_type=?"
        params.append(event)

    data = conn.execute(query, params).fetchall()
    conn.close()

    events = [row['event_type'] for row in data]
    event_count = Counter(events)

    return render_template('dashboard.html',
                           data=data,
                           event_count=event_count)

# ---------------- DELETE ----------------

@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM achievements WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# ---------------- EDIT ----------------

@app.route('/edit/<int:id>', methods=['GET','POST'])
def edit(id):
    conn = get_db()

    if request.method == 'POST':
        conn.execute('''
            UPDATE achievements
            SET name=?, usn=?, event_type=?, level=?, year=?, prize=?
            WHERE id=?
        ''', (
            request.form['name'],
            request.form['usn'],
            request.form['event_type'],
            request.form['level'],
            int(request.form['year']),
            request.form['prize'],
            id
        ))
        conn.commit()
        conn.close()
        return redirect('/dashboard')

    data = conn.execute("SELECT * FROM achievements WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template('add.html', edit_data=data)

# ---------------- NBA PDF ----------------

@app.route('/teacher/report')
def teacher_report():
    conn = get_db()
    data = conn.execute("SELECT event_type FROM achievements").fetchall()
    conn.close()

    events = [row['event_type'] for row in data]
    event_count = Counter(events)
    total = len(events)

    parts = [f"{v} {k}(s)" for k,v in event_count.items()]
    summary = f"In this academic year, students participated in {total} professional activities including " + ", ".join(parts) + "."

    pdf = SimpleDocTemplate("nba_report.pdf")
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("NBA Criterion 4 Report", styles['Heading1']))
    elements.append(Spacer(1,0.5*inch))
    elements.append(Paragraph(summary, styles['Normal']))

    pdf.build(elements)

    return send_file("nba_report.pdf", as_attachment=True)

# ---------------- RUN ----------------

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)