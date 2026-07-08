# AI Assignment Feedback Platform

## 1. Project Title
**AI Assignment Feedback Platform** — Rubric-based AI feedback and batch misconception analysis for student assignments.

## 2. Problem Statement
Instructors spend significant time manually grading repetitive coding and written assignments, and often lack visibility into *patterns* of misunderstanding across an entire batch of students. This platform lets students submit assignments (code or written answers) and receive instant, rubric-grounded AI feedback, while giving instructors a dashboard that surfaces the most common misconceptions across the whole class — turning grading data into an actionable teaching signal, not just a score.

## 3. Dataset / Reference Source
No public dataset is required. Synthetic but realistic seed data is provided in `data/`:
- `assignments.csv` — 5 assignments (2 coding, 3 theory: Python loops, SQL/schema design, robust error handling, algorithm complexity, database normalization)
- `rubric.csv` — 21 rubric criteria across the 5 assignments, each with weighted keywords/expected concepts
- `submissions.csv` — 43 synthetic student submissions of varying quality (strong/weak/poor) across 25 students
- `feedback_logs.csv` — populated at runtime as the AI grades submissions (starts empty)

## 4. Tools Used
- **Frontend + Backend:** Streamlit (single app serving both UI and logic — chosen per "use simple tools first")
- **Database:** SQLite (swappable to PostgreSQL/MySQL by changing the connection string in `src/db.py`)
- **AI/ML:** scikit-learn (TF-IDF + cosine similarity) for explainable rubric scoring; optional Anthropic Claude API for natural-language feedback generation
- **Language:** Python 3.10+

## 5. Project Workflow
1. Student selects an assignment and submits code/text through the Streamlit form.
2. The submission is validated (non-empty, minimum length) and stored in SQLite.
3. The AI module (`src/ai_feedback.py`) scores the submission against every rubric criterion using TF-IDF similarity + keyword coverage, producing an explainable per-criterion score.
4. Criteria scoring below 50% are converted into a human-readable **misconception** tag.
5. A feedback paragraph is generated (template-based by default, or via the Claude API if `ANTHROPIC_API_KEY` is set) and shown to the student immediately, alongside a transparent rubric breakdown.
6. Instructors open the dashboard, grade any ungraded batch submissions in one click, and view aggregate statistics + the most frequent misconceptions across all students for that assignment.

See the Mermaid diagrams in the original project brief for the high-level pipeline; this implementation follows that exact flow: `Frontend → Backend logic → Database + AI module → Dashboard/Report`.

## 6. AI/ML/Agent/Software Component
The AI component is a **rubric-based explainable scorer**, not a black-box classifier:
- TF-IDF vectorization + cosine similarity compares each submission against the rubric's expected keywords/concepts per criterion.
- Scores are blended 60% direct keyword coverage / 40% TF-IDF similarity, so paraphrased answers aren't unfairly penalized while still being grounded and auditable.
- A misconception library maps weakly-scored criteria to specific, actionable feedback phrases.
- An optional LLM (Claude) call can be enabled to rewrite the feedback in a warmer, more natural tone — but it is **constrained to the already-computed rubric scores**, so the AI cannot invent or change a grade.
- At the batch level, misconceptions are aggregated with a counter to show instructors what to re-teach.

This design is useful because it gives **instant, explainable, and consistent** first-pass feedback that scales to any class size, while keeping the instructor in the loop for final grading decisions.

## 7. How to Run the Project
```bash
# 1. Clone/open the repository
cd ai_assignment_feedback_platform

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) enable richer AI-written feedback
export ANTHROPIC_API_KEY=your_key_here

# 4. Run the app
streamlit run app/app.py
```
The first run automatically initializes the SQLite database (`feedback_platform.db`) from the seed CSVs in `data/`. Use the sidebar "Reset database to seed data" button at any time to start fresh.

## 8. Demo Screenshots
See `docs/screenshots/` (add screenshots of the Student submission view and Instructor dashboard here after running the app locally, per the deliverables checklist).

## 9. Results and Insights
On the seed dataset, the AI scorer reliably separates submission quality tiers (validated in `notebooks/exploration_or_modeling.ipynb`):
- Strong submissions score in the upper range with most criteria matched.
- Weak/poor submissions are correctly flagged with specific, recurring misconceptions (e.g., "edge cases (empty input, zero, negative numbers) are not handled" was the single most common misconception across the A1 coding assignment batch).
- This pattern is exactly what an instructor would want surfaced before the next class session.

## 10. Limitations
- Keyword/TF-IDF scoring is a proxy for understanding, not true code execution or semantic grading — it can be fooled by keyword-stuffing and may under-score correct answers phrased very differently from the rubric's expected language.
- No real code execution/unit testing of submitted code is performed (would be a strong next step).
- The optional LLM feedback path requires a valid `ANTHROPIC_API_KEY` and network access; it gracefully falls back to the deterministic template otherwise.
- Synthetic seed data is illustrative, not collected from real students.
- This is a learning-support tool, not a certified grading system — scores should be reviewed by an instructor for any high-stakes assessment.

## 11. Future Improvements
- Sandbox code execution + unit-test based scoring for coding assignments.
- Plagiarism/similarity detection across student submissions.
- Per-student progress tracking across multiple assignments over a semester.
- Richer embedding-based semantic scoring (e.g., sentence-transformers) instead of TF-IDF.
- Role-based authentication for students vs instructors instead of a sidebar toggle.

## 12. Team Member Names
Roll No. Name
- 388 Rishabh Rai
- 430 Hargundeep Singh
- 385 Rishabraj Singh Shekhawat
- 385 Utkarsh Kumar Chaturvedi
- 391 Abhimanyu Thakur

