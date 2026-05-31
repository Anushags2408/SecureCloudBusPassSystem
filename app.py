from flask import Flask, render_template, request, redirect, session
import sqlite3
import qrcode
import os

from encryption import encrypt_data

app = Flask(__name__)
app.secret_key = "secret123"


# -----------------------------
# DATABASE INITIALIZATION
# -----------------------------
def init_db():

    conn = sqlite3.connect("database.db")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS bookings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        source TEXT,
        destination TEXT,
        fare INTEGER
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS security_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attack TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# -----------------------------
# HOME PAGE
# -----------------------------
@app.route('/')
def home():
    return render_template('index.html')


# -----------------------------
# REGISTER
# -----------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']

        password = encrypt_data(
            request.form['password']
        ).decode()

        dangerous_words = [
            "'",
            "--",
            "DROP",
            "SELECT",
            "UNION"
        ]

        for word in dangerous_words:

            if word.lower() in username.lower():

                conn = sqlite3.connect("database.db")

                conn.execute(
                    "INSERT INTO security_logs(attack) VALUES(?)",
                    (username,)
                )

                conn.commit()
                conn.close()

                return "Possible SQL Injection Detected"

        conn = sqlite3.connect("database.db")

        conn.execute(
            "INSERT INTO users(username,password) VALUES(?,?)",
            (username, password)
        )

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')


# -----------------------------
# LOGIN
# -----------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']

        conn = sqlite3.connect("database.db")

        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            session['username'] = username

            return redirect('/dashboard')

        return "User Not Found"

    return render_template('login.html')


# -----------------------------
# DASHBOARD
# -----------------------------
@app.route('/dashboard')
def dashboard():

    if 'username' not in session:
        return redirect('/login')

    return render_template(
        'dashboard.html',
        username=session['username']
    )


# -----------------------------
# BOOKING
# -----------------------------
@app.route('/booking', methods=['GET', 'POST'])
def booking():

    if request.method == 'POST':

        username = request.form['username']
        source = request.form['source']
        destination = request.form['destination']

        fare = 100

        conn = sqlite3.connect("database.db")

        conn.execute(
            """
            INSERT INTO bookings
            (username,source,destination,fare)
            VALUES(?,?,?,?)
            """,
            (
                username,
                source,
                destination,
                fare
            )
        )

        conn.commit()
        conn.close()

        ticket_data = f"""
        User: {username}
        From: {source}
        To: {destination}
        Fare: {fare}
        """

        if not os.path.exists("static/images"):
            os.makedirs("static/images")

        img = qrcode.make(ticket_data)

        img.save(
            "static/images/ticket.png"
        )

        return redirect('/ticket')

    return render_template('booking.html')


# -----------------------------
# TICKET
# -----------------------------
@app.route('/ticket')
def ticket():
    return render_template('ticket.html')


# -----------------------------
# LOGOUT
# -----------------------------
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


# -----------------------------
# RUN APPLICATION
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)