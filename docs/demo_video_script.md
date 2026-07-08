# Demo Video Script (5–8 minutes)

Use this as a talking-point script when recording the required demo video.

**1. Problem (30–45s)**
"Instructors spend hours grading repetitive assignments and rarely get a clear picture of what the whole class is struggling with. Students wait days for feedback. We built a platform that gives instant, rubric-grounded AI feedback to students and a misconception dashboard to instructors."

**2. Users (15–20s)**
"Two users: students submitting assignments, and instructors reviewing batch results."

**3. Data / source material (20–30s)**
Show `data/` folder: assignments.csv, rubric.csv, submissions.csv. "We created 5 representative assignments — both coding and theory — each with a weighted rubric."

**4. How the system works (60–90s)**
Walk through `src/ai_feedback.py` briefly: "Every submission is scored against rubric keywords using TF-IDF similarity — this keeps it explainable instead of a black box. Low-scoring criteria are converted into specific misconception tags."

**5. Live demo — Student view (90s)**
- Open the Streamlit app, select Student role
- Pick assignment A1 (Python loops)
- Paste a strong code submission → show instant score + rubric breakdown
- Paste a weak one → show lower score + specific misconceptions

**6. Live demo — Instructor view (90s)**
- Switch to Instructor role
- Click "Run AI grading" on ungraded submissions
- Show average score, score distribution chart
- Show the "Most common misconceptions across the batch" table — this is the key insight for instructors

**7. Limitations & improvements (30–45s)**
"This is AI-assisted formative feedback, not a replacement for instructor grading on high-stakes work. It currently scores via keyword/similarity matching rather than executing code. Next steps would be sandboxed code execution and plagiarism detection."

**8. Close (10s)**
"That's the AI Assignment Feedback Platform — thank you."
