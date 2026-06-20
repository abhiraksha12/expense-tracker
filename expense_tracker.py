import pandas as pd
import sqlite3
import os
from datetime import datetime

DB_NAME = "expenses.db"
CSV_FILE = "expenses.csv"


def create_sample_csv():
    """Creates a sample CSV if none exists, so you can test immediately."""
    sample_data = {
        "date": [
            "2024-01-05", "2024-01-12", "2024-01-18", "2024-01-25",
            "2024-02-03", "2024-02-10", "2024-02-15", "2024-02-22",
            "2024-03-01", "2024-03-08", "2024-03-14", "2024-03-20",
        ],
        "category": [
            "Food", "Transport", "Entertainment", "Food",
            "Shopping", "Food", "Transport", "Utilities",
            "Food", "Entertainment", "Shopping", "Food",
        ],
        "amount": [
            450, 120, 300, 520,
            1200, 380, 95, 850,
            410, 250, 670, 490,
        ],
        "note": [
            "Groceries", "Uber rides", "Movie + dinner", "Restaurant",
            "New shoes", "Weekly groceries", "Auto rickshaw", "Electricity bill",
            "Supermarket", "Concert tickets", "Clothes", "Zomato orders",
        ],
    }
    df = pd.DataFrame(sample_data)
    df.to_csv(CSV_FILE, index=False)
    print(f"Sample CSV created: {CSV_FILE}")


def clean_data(df):
    """Cleans and validates the raw CSV data."""
    print(f"\nRows before cleaning: {len(df)}")

    # Drop rows where date, category, or amount is missing
    df = df.dropna(subset=["date", "category", "amount"])

    # Standardise date format to YYYY-MM-DD
    df["date"] = pd.to_datetime(df["date"], dayfirst=False, errors="coerce")
    df = df.dropna(subset=["date"])  # drop rows with unparseable dates
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # Strip whitespace from text columns
    df["category"] = df["category"].str.strip().str.title()
    df["note"] = df["note"].fillna("").str.strip()

    # Ensure amount is numeric and positive
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"])
    df = df[df["amount"] > 0]

    # Add a month column for easier querying later
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)

    print(f"Rows after cleaning:  {len(df)}")
    return df.reset_index(drop=True)


def push_to_sqlite(df):
    """Creates the SQLite database and inserts cleaned data."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            date     TEXT NOT NULL,
            month    TEXT NOT NULL,
            category TEXT NOT NULL,
            amount   REAL NOT NULL,
            note     TEXT
        )
    """)

    # Clear old data so re-runs don't duplicate rows
    cursor.execute("DELETE FROM expenses")

    # Insert all rows at once
    df[["date", "month", "category", "amount", "note"]].to_sql(
        "expenses", conn, if_exists="append", index=False
    )

    conn.commit()
    print(f"\nInserted {len(df)} rows into '{DB_NAME}'")
    return conn


def run_summary_queries(conn):
    """Runs useful SQL queries and prints results — these will also power your Flask API."""
    print("\n--- Total spending by category ---")
    df_cat = pd.read_sql_query("""
        SELECT category,
               ROUND(SUM(amount), 2) AS total,
               COUNT(*)              AS transactions
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
    """, conn)
    print(df_cat.to_string(index=False))

    print("\n--- Monthly totals ---")
    df_month = pd.read_sql_query("""
        SELECT month,
               ROUND(SUM(amount), 2) AS total,
               COUNT(*)              AS transactions
        FROM expenses
        GROUP BY month
        ORDER BY month
    """, conn)
    print(df_month.to_string(index=False))

    print("\n--- Top 5 biggest expenses ---")
    df_top = pd.read_sql_query("""
        SELECT date, category, amount, note
        FROM expenses
        ORDER BY amount DESC
        LIMIT 5
    """, conn)
    print(df_top.to_string(index=False))

    conn.close()


def main():
    # Step 1 — create sample CSV if needed
    if not os.path.exists(CSV_FILE):
        create_sample_csv()

    # Step 2 — read CSV
    print(f"\nReading '{CSV_FILE}'...")
    df_raw = pd.read_csv(CSV_FILE)
    print(df_raw.head())

    # Step 3 — clean data
    df_clean = clean_data(df_raw)

    # Step 4 — push to SQLite
    conn = push_to_sqlite(df_clean)

    # Step 5 — run summary queries
    run_summary_queries(conn)

    print(f"\nDone. Database saved as '{DB_NAME}'")
    print("Next step: run the Flask API to serve this data to your frontend.")


if __name__ == "__main__":
    main()