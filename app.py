from flask import Flask, jsonify, send_from_directory
import sqlite3
import os

app = Flask(__name__)
DB_NAME = "expenses.db"


def get_db():
    """Opens a database connection and returns rows as dicts."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ── Serve the frontend ─────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# ── API routes ─────────────────────────────────────────────────────────────────

@app.route("/api/summary")
def summary():
    """Total spending and transaction count per category."""
    conn = get_db()
    rows = conn.execute("""
        SELECT category,
               ROUND(SUM(amount), 2) AS total,
               COUNT(*)              AS transactions
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/monthly")
def monthly():
    """Month-wise spending totals."""
    conn = get_db()
    rows = conn.execute("""
        SELECT month,
               ROUND(SUM(amount), 2) AS total,
               COUNT(*)              AS transactions
        FROM expenses
        GROUP BY month
        ORDER BY month
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/recent")
def recent():
    """Last 10 transactions, newest first."""
    conn = get_db()
    rows = conn.execute("""
        SELECT date, category, amount, note
        FROM expenses
        ORDER BY date DESC
        LIMIT 10
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/stats")
def stats():
    """Single-number headline stats for the dashboard cards."""
    conn = get_db()
    row = conn.execute("""
        SELECT ROUND(SUM(amount), 2)  AS total_spent,
               COUNT(*)               AS total_transactions,
               ROUND(AVG(amount), 2)  AS avg_transaction,
               MAX(amount)            AS biggest_expense
        FROM expenses
    """).fetchone()
    top_cat = conn.execute("""
        SELECT category
        FROM expenses
        GROUP BY category
        ORDER BY SUM(amount) DESC
        LIMIT 1
    """).fetchone()
    conn.close()

    result = dict(row)
    result["top_category"] = top_cat["category"] if top_cat else "N/A"
    return jsonify(result)


# ── Run ────────────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')
if __name__ == "__main__":
    if not os.path.exists(DB_NAME):
        print(f"ERROR: '{DB_NAME}' not found.")
        print("Run 'python expense_tracker.py' first to create the database.")
    else:
        print("Starting server at http://127.0.0.1:5000")
        app.run(debug=True)
        