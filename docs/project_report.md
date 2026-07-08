# Project Report: AI Assignment Feedback Platform

**Track:** SDAI | **Domain:** Education Technology & Assessment Support

## 1. Problem Understanding and Stakeholders

**Users:**
- **Students** — submit coding or written assignments and want fast, specific, actionable feedback instead of waiting days for a grade.
- **Instructors** — need to grade efficiently and, more importantly, understand *patterns* of misunderstanding across a class so they can adjust teaching, not just assign individual scores.

**Inputs:** Assignment rubric, student submission text (code or prose).
**Outputs:** Per-criterion score, explainable feedback text, list of misconceptions, and a batch-level instructor dashboard.
**Success criteria:** Feedback must be (a) fast (instant, not days later), (b) explainable (traceable to specific rubric criteria), and (c) aggregable (instructors can see batch-wide trends, not just one submission at a time).

## 2. Data / Reference Material Preparation
Since no public dataset fits this workflow, structured seed data was created covering 5 representative assignment types (Python loops/conditionals, SQL/schema design with joins, exception handling, algorithm complexity analysis, and database normalization). Each assignment has a dedicated rubric with weighted criteria and keyword sets, and 43 synthetic submissions spanning strong/weak/poor quality tiers were generated to realistically exercise the scoring engine (see `data/` and `gen_data.py` generation logic referenced in the repo).

## 3. System Workflow
```
Student → Streamlit Frontend → Validation → SQLite Storage
                                     ↓
                          AI Rubric Scoring Engine (TF-IDF + keyword match)
                                     ↓
                  Per-criterion score + misconception tags + feedback text
                                     ↓
                Student sees feedback  |  Instructor Dashboard aggregates
                                          misconceptions across the batch
```

## 4. AI/ML/Agent Logic
Implemented in `src/ai_feedback.py`:
- **Scoring:** TF-IDF vectorization (scikit-learn) + cosine similarity between submission text and a synthetic "ideal answer" built from rubric keywords, blended with direct keyword coverage for explainability.
- **Misconception extraction:** Criteria scoring below 50% trigger a lookup in a curated misconception library, turning a low score into a specific, teachable insight.
- **Feedback generation:** Deterministic template by default; optional Claude API call for more natural phrasing, constrained to never override the computed score (prevents grade hallucination).
- **Batch aggregation:** A `Counter` over all misconceptions in an assignment's submissions surfaces the top issues for the instructor.

This is meaningfully different from "AI for decoration" — the AI component is the core engine that produces the score and the actionable insight, not a cosmetic wrapper.

## 5. Validation / Evaluation
Validation performed (see `tests/test_pipeline.py` and `notebooks/exploration_or_modeling.ipynb`):
1. **Discrimination test:** Verified the scorer assigns meaningfully higher scores to strong submissions than poor ones across all 5 assignments (automated assertion).
2. **Determinism check:** The template-based scoring path is deterministic — repeated runs on the same input produce identical scores (standard deviation = 0.0), which is important for grading fairness/auditability.
3. **Batch aggregation sanity check:** Confirmed that misconception counts never exceed the number of submissions and that the most common misconception aligns with the intentionally "weak" synthetic submissions in the seed data.
4. **Edge-case guardrails:** Empty or extremely short submissions are rejected before reaching the AI module (`utils.validate_submission_text`).

## 6. Output Explanation (Plain English)
For every submission, the platform tells the student: "Here is your score, here is exactly which rubric criteria you met or missed, and here is what to improve next." For the instructor, it adds: "Across your whole class, this is the single most common thing students got wrong on this assignment — consider addressing it in your next session."

## 7. Limitations and Responsible Use
- This tool provides **AI-assisted formative feedback**, not certified summative grading. Final grades on high-stakes assessments should be reviewed by an instructor.
- The scorer is keyword/similarity-based, not a code execution engine — it can be fooled and is not a substitute for running actual unit tests on code submissions.
- No personally identifying or sensitive student data is collected beyond a name/ID in the synthetic seed data; in a real deployment, student data privacy and FERPA/local-equivalent compliance would need to be addressed.

## 8. Future Improvements
See README §11 (sandboxed code execution scoring, plagiarism detection, semantic embeddings, per-student longitudinal tracking, authentication).
