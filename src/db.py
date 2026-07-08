"""
db.py
Database layer (SQLite). Loads the seed CSVs on first run and exposes
simple helper functions used by the Streamlit app. SQLite is used per
the 'use simple tools first' guidance; swapping to PostgreSQL/MySQL only
requires changing the connection string in a real deployment.
"""
import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(BASE_DIR, "feedback_platform.db")


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db(force_reload: bool = False):
    """Create tables from the seed CSVs if the DB doesn't exist yet
    (or force_reload is True)."""
    fresh = force_reload or not os.path.exists(DB_PATH)
    conn = get_connection()

    if fresh:
        assignments = pd.read_csv(os.path.join(DATA_DIR, "assignments.csv"))
        rubric = pd.read_csv(os.path.join(DATA_DIR, "rubric.csv"))
        submissions = pd.read_csv(os.path.join(DATA_DIR, "submissions.csv"))

        feedback_path = os.path.join(DATA_DIR, "feedback_logs.csv")
        if os.path.exists(feedback_path):
            feedback_logs = pd.read_csv(feedback_path)
        else:
            feedback_logs = pd.DataFrame(columns=[
                "feedback_id", "submission_id", "assignment_id", "score",
                "max_score", "feedback_text", "misconceptions", "generated_at"
            ])

        assignments.to_sql("assignments", conn, if_exists="replace", index=False)
        rubric.to_sql("rubric", conn, if_exists="replace", index=False)
        submissions.to_sql("submissions", conn, if_exists="replace", index=False)
        feedback_logs.to_sql("feedback_logs", conn, if_exists="replace", index=False)
        conn.commit()
    return conn


# ----------------------------------------------------------------------
# Query helpers
# ----------------------------------------------------------------------
def get_assignments(conn) -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM assignments", conn)


def get_rubric(conn, assignment_id: str) -> pd.DataFrame:
    return pd.read_sql(
        "SELECT * FROM rubric WHERE assignment_id = ?", conn, params=(assignment_id,)
    )


def get_submissions(conn, assignment_id: str = None) -> pd.DataFrame:
    if assignment_id:
        return pd.read_sql(
            "SELECT * FROM submissions WHERE assignment_id = ?", conn, params=(assignment_id,)
        )
    return pd.read_sql("SELECT * FROM submissions", conn)


def get_feedback_logs(conn, assignment_id: str = None) -> pd.DataFrame:
    if assignment_id:
        df = pd.read_sql(
            "SELECT * FROM feedback_logs WHERE assignment_id = ?", conn, params=(assignment_id,)
        )
    else:
        df = pd.read_sql("SELECT * FROM feedback_logs", conn)
    for col in ("score", "max_score"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def insert_submission(conn, submission_id, assignment_id, student_id, student_name,
                       submission_text, submitted_at):
    conn.execute(
        "INSERT INTO submissions (submission_id, assignment_id, student_id, student_name, "
        "submission_text, submitted_at) VALUES (?, ?, ?, ?, ?, ?)",
        (submission_id, assignment_id, student_id, student_name, submission_text, submitted_at),
    )
    conn.commit()


def upsert_feedback(conn, feedback_id, submission_id, assignment_id, score, max_score,
                     feedback_text, misconceptions, generated_at):
    conn.execute("DELETE FROM feedback_logs WHERE submission_id = ?", (submission_id,))
    conn.execute(
        "INSERT INTO feedback_logs (feedback_id, submission_id, assignment_id, score, "
        "max_score, feedback_text, misconceptions, generated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (feedback_id, submission_id, assignment_id, score, max_score, feedback_text,
         misconceptions, generated_at),
    )
    conn.commit()


def next_submission_id(conn) -> str:
    df = pd.read_sql("SELECT submission_id FROM submissions", conn)
    nums = [int(s.replace("S", "")) for s in df["submission_id"] if s.startswith("S")]
    nxt = max(nums) + 1 if nums else 1
    return f"S{nxt:04d}"


def next_feedback_id(conn) -> str:
    df = pd.read_sql("SELECT feedback_id FROM feedback_logs", conn)
    nums = [int(s.replace("F", "")) for s in df["feedback_id"] if isinstance(s, str) and s.startswith("F")]
    nxt = max(nums) + 1 if nums else 1
    return f"F{nxt:04d}"
