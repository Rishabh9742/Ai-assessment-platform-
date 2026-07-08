"""
app.py
Streamlit application for the AI Assignment Feedback Platform.

Two role-based views (per the project's "Role/status workflow" requirement):
  - Student view: pick an assignment, submit an answer, get instant
    rubric-based AI feedback.
  - Instructor view: see batch-level stats, per-submission feedback, and
    the most common misconceptions across all students for an assignment.
"""
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from db import (  # noqa: E402
    init_db, get_assignments, get_rubric, get_submissions, get_feedback_logs,
    insert_submission, upsert_feedback, next_submission_id, next_feedback_id,
)
from ai_feedback import generate_feedback  # noqa: E402
from utils import validate_submission_text, now_iso  # noqa: E402

st.set_page_config(page_title="AI Assignment Feedback Platform", page_icon="📝", layout="wide")

conn = init_db()

# ----------------------------------------------------------------------
# Sidebar: role + reset
# ----------------------------------------------------------------------
st.sidebar.title("📝 AI Feedback Platform")
role = st.sidebar.radio("I am a:", ["Student", "Instructor"])
use_llm = st.sidebar.toggle(
    "Use Claude API for richer feedback wording",
    value=False,
    help="Requires ANTHROPIC_API_KEY env var. Falls back to the deterministic "
         "rubric template automatically if no key is set or the call fails."
)
if st.sidebar.button("🔄 Reset database to seed data"):
    init_db(force_reload=True)
    st.sidebar.success("Database reset.")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(
    "⚠️ **Responsible use note:** This tool gives *AI-assisted* rubric feedback "
    "to support learning. It is not a substitute for instructor grading on "
    "high-stakes assessments, and scores should be reviewed before being final."
)

assignments_df = get_assignments(conn)

# ========================================================================
# STUDENT VIEW
# ========================================================================
if role == "Student":
    st.title("Submit an Assignment")

    a_choice = st.selectbox(
        "Choose an assignment",
        assignments_df["assignment_id"],
        format_func=lambda x: str(assignments_df.set_index("assignment_id").loc[x, "title"]),
    )
    a_row = assignments_df.set_index("assignment_id").loc[a_choice]

    st.info(f"**{a_row['title']}** ({a_row['type']})\n\n{a_row['description']}")

    col1, col2 = st.columns(2)
    student_name = col1.text_input("Your name", value="Student_New")
    student_id = col2.text_input("Student ID", value="student_new")

    submission_text = st.text_area(
        "Your answer / code",
        height=250,
        placeholder="Paste your code or write your answer here...",
    )

    if st.button("Submit for AI Feedback", type="primary"):
        ok, msg = validate_submission_text(submission_text)
        if not ok:
            st.error(msg)
        else:
            sub_id = next_submission_id(conn)
            ts = now_iso()
            insert_submission(conn, sub_id, a_choice, student_id, student_name,
                               submission_text, ts)

            rubric_rows = get_rubric(conn, a_choice).to_dict("records")
            with st.spinner("Generating AI feedback..."):
                result = generate_feedback(sub_id, a_choice, submission_text,
                                            rubric_rows, use_llm=use_llm)

            fb_id = next_feedback_id(conn)
            upsert_feedback(
                conn, fb_id, sub_id, a_choice, result.score, result.max_score,
                result.feedback_text, "; ".join(result.misconceptions), now_iso(),
            )

            pct = result.score / result.max_score * 100 if result.max_score else 0
            st.success(f"Submission `{sub_id}` graded: **{result.score:.1f} / {result.max_score:.0f}** ({pct:.0f}%)")

            st.subheader("AI Feedback")
            st.markdown(result.feedback_text.replace("\n", "  \n"))

            with st.expander("See rubric breakdown (explainability)"):
                bd = pd.DataFrame([{
                    "Criterion": c.criterion,
                    "Points": f"{c.points_awarded:.1f} / {c.max_points:.0f}",
                    "Matched keywords": ", ".join(c.matched_keywords) or "—",
                    "Missing keywords": ", ".join(c.missing_keywords) or "—",
                } for c in result.criteria_results])
                st.dataframe(bd, use_container_width=True, hide_index=True)

# ========================================================================
# INSTRUCTOR VIEW
# ========================================================================
else:
    st.title("Instructor Dashboard")

    a_choice = st.selectbox(
        "Select assignment to review",
        assignments_df["assignment_id"],
        format_func=lambda x: str(assignments_df.set_index("assignment_id").loc[x, "title"]),
    )

    submissions = get_submissions(conn, a_choice)
    feedback = get_feedback_logs(conn, a_choice)

    st.caption(f"{len(submissions)} submissions received for this assignment.")

    ungraded = submissions[~submissions["submission_id"].isin(feedback["submission_id"])]
    if len(ungraded) > 0:
        if st.button(f"⚙️ Run AI grading on {len(ungraded)} ungraded submission(s)"):
            rubric_rows = get_rubric(conn, a_choice).to_dict("records")
            progress = st.progress(0)
            results = []
            for i, (_, row) in enumerate(ungraded.iterrows()):
                result = generate_feedback(row["submission_id"], a_choice,
                                            row["submission_text"], rubric_rows, use_llm=use_llm)
                fb_id = next_feedback_id(conn)
                upsert_feedback(conn, fb_id, row["submission_id"], a_choice, result.score,
                                 result.max_score, result.feedback_text,
                                 "; ".join(result.misconceptions), now_iso())
                results.append(result)
                progress.progress((i + 1) / len(ungraded))
            st.success(f"Graded {len(results)} submissions.")
            st.rerun()
    else:
        st.success("All submissions for this assignment have been graded.")

    feedback = get_feedback_logs(conn, a_choice)  # refresh

    if len(feedback) == 0:
        st.warning("No graded submissions yet for this assignment.")
    else:
        merged = feedback.merge(submissions, on="submission_id", how="left")
        max_score = merged["max_score"].iloc[0] if len(merged) else 100

        c1, c2, c3 = st.columns(3)
        c1.metric("Average score", f"{merged['score'].mean():.1f} / {max_score:.0f}")
        c2.metric("Highest score", f"{merged['score'].max():.1f}")
        c3.metric("Lowest score", f"{merged['score'].min():.1f}")

        st.subheader("Score distribution")
        st.bar_chart(merged.set_index("student_name")["score"])

        st.subheader("Most common misconceptions across the batch")
        all_results_text = merged["misconceptions"].dropna().tolist()
        from collections import Counter
        counter = Counter()
        for entry in all_results_text:
            for m in str(entry).split(";"):
                m = m.strip()
                if m:
                    counter[m] += 1
        if counter:
            mc_df = pd.DataFrame(counter.most_common(10), columns=["Misconception", "Number of students"])
            st.dataframe(mc_df, use_container_width=True, hide_index=True)
            st.caption(
                "💡 Use this list to decide what to re-teach or clarify in the next class session."
            )
        else:
            st.info("No common misconceptions detected — batch is performing well on this rubric!")

        st.subheader("All submissions")
        view_cols = ["submission_id", "student_name", "score", "generated_at"]
        st.dataframe(merged[view_cols].sort_values("score", ascending=False),
                     use_container_width=True, hide_index=True)

        st.subheader("Inspect a single submission")
        sel = st.selectbox("Submission", merged["submission_id"])
        sel_row = merged[merged["submission_id"] == sel].iloc[0]
        st.text_area("Submission text", sel_row["submission_text"], height=150, disabled=True)
        st.markdown(f"**Score:** {sel_row['score']:.1f} / {sel_row['max_score']:.0f}")
        st.markdown(sel_row["feedback_text"].replace("\n", "  \n"))
