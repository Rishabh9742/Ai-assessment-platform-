# Presentation Outline — AI Assignment Feedback Platform
*(8–10 slides — convert to PPT/PDF for submission)*

## Slide 1: Title & Team
- AI Assignment Feedback Platform
- Track: SDAI | Team member names

## Slide 2: Problem & Real-World Impact
- Instructors spend hours manually grading repetitive assignments
- Students wait days for feedback and rarely learn *why* they lost points
- Instructors lack visibility into batch-wide misconceptions
- Impact: faster feedback loop for students + actionable teaching signal for instructors

## Slide 3: Dataset / Reference Material
- 5 assignments (coding + theory), 21 rubric criteria, 43 synthetic submissions, 25 students
- Created using a realistic schema (assignments.csv, rubric.csv, submissions.csv, feedback_logs.csv)

## Slide 4: System Workflow
- Diagram: Student → Frontend (Streamlit) → Validation → DB (SQLite) → AI Scoring Engine → Feedback + Dashboard
- (Use the Mermaid flowchart from the project brief / README)

## Slide 5: AI/ML Innovation
- TF-IDF + cosine similarity rubric scoring (explainable, not black-box)
- Misconception extraction library
- Optional Claude API for natural-language feedback (score-constrained, no hallucinated grades)
- Batch-level misconception aggregation

## Slide 6: Prototype / Demo Screenshots
- [Insert screenshot: Student submission + feedback view]
- [Insert screenshot: Instructor dashboard with batch misconceptions]

## Slide 7: Results / Sample Outputs
- Strong vs. poor submissions reliably separated by the scorer
- Example: "Edge cases not handled" was the #1 misconception across the loops assignment batch
- 7/7 automated workflow tests passing

## Slide 8: Limitations & Responsible Use
- AI-assisted formative feedback, not certified summative grading
- Keyword/similarity-based — not real code execution
- Instructor should review before finalizing high-stakes grades

## Slide 9: Future Improvements
- Sandboxed code execution scoring
- Plagiarism detection, semantic embeddings, longitudinal student tracking
- Authentication-based roles

## Slide 10: Conclusion
- Demonstrates a working, explainable AI feedback loop from submission to actionable instructor insight
- Built with simple, swappable tools (Streamlit, SQLite, scikit-learn) per a "start simple" philosophy
