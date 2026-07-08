"""
ai_feedback.py
==============
This is the AI / Innovation component of the platform.

WHAT IT DOES
------------
1. RUBRIC-BASED SCORING
   For every rubric criterion attached to an assignment, the submission text
   is compared against a set of expected keywords/phrases using TF-IDF +
   cosine similarity (scikit-learn). This gives a soft, explainable score
   per criterion instead of a single opaque black-box number.

2. MISCONCEPTION EXTRACTION
   When a criterion scores low, the engine flags *why* (missing keywords,
   missing edge-case handling, missing explanation depth, etc.) and converts
   that into a short, human-readable "misconception" tag. These tags are
   logged per submission AND aggregated across the batch so an instructor
   can see the most common misconceptions for an assignment at a glance.

3. NATURAL-LANGUAGE FEEDBACK GENERATION
   A template-driven generator turns the per-criterion scores and
   misconceptions into a readable feedback paragraph. If an Anthropic API
   key is available (ANTHROPIC_API_KEY env var), the engine will instead
   call the Claude API to generate richer, more natural feedback while
   still being grounded in the same rubric scores (so the AI cannot
   hallucinate a grade that disagrees with the rubric match).

WHY THIS APPROACH
------------------
- It is fully explainable: every score traces back to a rubric criterion
  and matched/missing keywords, which is important in an educational
  grading context (instructors and students need to trust + audit grades).
- It works completely offline (no API key required) so the project is
  runnable and demoable without any paid service, while still supporting
  a real LLM call as an optional upgrade.
"""
from __future__ import annotations
import os
import re
import json
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from preprocessing import clean_text, tokenize, looks_like_code


# ----------------------------------------------------------------------
# Data classes
# ----------------------------------------------------------------------
@dataclass
class CriterionResult:
    criterion: str
    max_points: float
    points_awarded: float
    matched_keywords: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)
    misconception: str | None = None


@dataclass
class FeedbackResult:
    submission_id: str
    assignment_id: str
    score: float
    max_score: float
    criteria_results: List[CriterionResult]
    misconceptions: List[str]
    feedback_text: str


# ----------------------------------------------------------------------
# Core scoring logic
# ----------------------------------------------------------------------
def _keyword_overlap_score(text: str, keywords: List[str]) -> tuple[float, list, list]:
    """Returns (similarity 0-1, matched keywords, missing keywords) using
    TF-IDF cosine similarity between the submission and a synthetic
    'ideal answer' built from the rubric keywords."""
    tokens = set(tokenize(text))
    matched = [k for k in keywords if k.replace(" ", "_") in tokens or k in text]
    missing = [k for k in keywords if k not in matched]

    # TF-IDF similarity as a secondary, smoother signal
    ideal_doc = " ".join(keywords)
    try:
        vec = TfidfVectorizer().fit([text, ideal_doc])
        sim = cosine_similarity(vec.transform([text]), vec.transform([ideal_doc]))[0][0]
    except ValueError:
        sim = 0.0

    keyword_ratio = len(matched) / max(len(keywords), 1)
    # Blend: 60% direct keyword coverage (precise/explainable),
    #        40% TF-IDF similarity (captures paraphrasing)
    blended = 0.6 * keyword_ratio + 0.4 * sim
    return min(blended, 1.0), matched, missing


MISCONCEPTION_LIBRARY = {
    "Correct use of loops": "Student may not be using loops correctly or at all.",
    "Correct use of conditionals": "Conditional logic (if/elif/else) appears missing or incomplete.",
    "Handles edge cases": "Edge cases (empty input, zero, negative numbers) are not handled.",
    "Code readability and comments": "Code lacks comments/docstrings or clear naming.",
    "Correct output / logic": "Output/return logic may be incorrect or unverified.",
    "Explains time complexity": "Time complexity is not explained or is stated incorrectly.",
    "Explains space complexity": "Space complexity is missing from the explanation.",
    "Correct algorithm identification": "The algorithm or technique is not clearly identified.",
    "Clear explanation in own words": "Explanation is too shallow / not reasoned through.",
    "Defines key concept correctly": "Core concept definition is missing or vague.",
    "Provides relevant example": "No concrete example is given to support the explanation.",
    "Covers normalization concept": "Normalization forms (1NF/2NF/3NF) are not addressed.",
    "Grammar and clarity": "Answer could be clearer or better structured.",
    "Correct use of joins/queries": "SQL joins/queries are missing, incorrect, or oversimplified.",
    "Schema design correctness": "Schema lacks proper primary/foreign key design.",
    "Query optimization awareness": "No mention of indexing or query performance.",
    "Explanation clarity": "Reasoning behind the SQL/schema choices is not explained.",
    "Correct exception handling": "Try/except (error handling) is missing or incomplete.",
    "Input validation": "User input is not validated/sanitized.",
    "Modular function design": "Code is not organized into reusable functions.",
    "Testing mentioned": "No tests or assertions are included to verify behavior.",
}


def score_submission(submission_text: str, rubric_rows: List[Dict]) -> List[CriterionResult]:
    """Score a submission against every rubric row (criterion) of its assignment."""
    text = clean_text(submission_text)
    results = []
    for row in rubric_rows:
        keywords = [k.strip() for k in row["keywords"].split(";") if k.strip()]
        max_points = float(row["max_points"])
        sim, matched, missing = _keyword_overlap_score(text, keywords)
        points = round(sim * max_points, 2)

        misconception = None
        # Flag a misconception when the criterion is weakly satisfied (<50%)
        if sim < 0.5:
            misconception = MISCONCEPTION_LIBRARY.get(
                row["criterion"], f"Weak coverage of: {row['criterion']}"
            )

        results.append(CriterionResult(
            criterion=row["criterion"],
            max_points=max_points,
            points_awarded=points,
            matched_keywords=matched,
            missing_keywords=missing,
            misconception=misconception,
        ))
    return results


# ----------------------------------------------------------------------
# Feedback text generation
# ----------------------------------------------------------------------
def _template_feedback(criteria_results: List[CriterionResult], total: float, max_total: float) -> str:
    pct = (total / max_total * 100) if max_total else 0
    if pct >= 80:
        opening = "Strong submission overall."
    elif pct >= 55:
        opening = "Good attempt with some gaps to address."
    else:
        opening = "This submission needs significant improvement."

    lines = [f"{opening} You scored {total:.1f}/{max_total:.0f} ({pct:.0f}%).", ""]
    lines.append("Breakdown by rubric criterion:")
    for cr in criteria_results:
        status = "✅" if cr.points_awarded / cr.max_points >= 0.7 else (
            "⚠️" if cr.points_awarded / cr.max_points >= 0.4 else "❌"
        )
        lines.append(f"  {status} {cr.criterion}: {cr.points_awarded:.1f}/{cr.max_points:.0f}")

    weak = [cr for cr in criteria_results if cr.misconception]
    if weak:
        lines.append("")
        lines.append("Suggested improvements:")
        for cr in weak:
            lines.append(f"  - {cr.misconception} Consider revisiting '{cr.criterion.lower()}'.")
    lines.append("")
    lines.append(
        "Note: This is AI-generated rubric-based feedback intended to support, "
        "not replace, instructor judgement."
    )
    return "\n".join(lines)


def _llm_feedback(submission_text: str, criteria_results: List[CriterionResult],
                   total: float, max_total: float) -> str | None:
    """Optional: use the Anthropic API for richer feedback, grounded in the
    already-computed rubric scores so the score itself can't be hallucinated.
    Returns None if no API key is configured or the call fails, so the
    caller can fall back to the deterministic template."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        rubric_summary = "\n".join(
            f"- {cr.criterion}: {cr.points_awarded:.1f}/{cr.max_points:.0f} "
            f"(missing: {', '.join(cr.missing_keywords) or 'none'})"
            for cr in criteria_results
        )
        prompt = (
            "You are an assignment feedback assistant. A rubric-based system has "
            "already computed the scores below; do NOT change the numbers, only "
            "explain them clearly and suggest 2-3 concrete improvements in a warm, "
            "encouraging tone, in under 150 words.\n\n"
            f"Student submission:\n{submission_text}\n\n"
            f"Rubric scores ({total:.1f}/{max_total:.0f} total):\n{rubric_summary}"
        )
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception:
        return None


def generate_feedback(submission_id: str, assignment_id: str, submission_text: str,
                       rubric_rows: List[Dict], use_llm: bool = False) -> FeedbackResult:
    criteria_results = score_submission(submission_text, rubric_rows)
    total = sum(c.points_awarded for c in criteria_results)
    max_total = sum(c.max_points for c in criteria_results)
    misconceptions = [c.misconception for c in criteria_results if c.misconception]

    text = None
    if use_llm:
        text = _llm_feedback(submission_text, criteria_results, total, max_total)
    if text is None:
        text = _template_feedback(criteria_results, total, max_total)

    return FeedbackResult(
        submission_id=submission_id,
        assignment_id=assignment_id,
        score=round(total, 2),
        max_score=round(max_total, 2),
        criteria_results=criteria_results,
        misconceptions=misconceptions,
        feedback_text=text,
    )


def aggregate_misconceptions(feedback_results: List[FeedbackResult], top_n: int = 10):
    """Batch-level analysis: identify the most common misconceptions across
    all submissions for an assignment, used by the instructor dashboard."""
    counter = Counter()
    for fr in feedback_results:
        counter.update(fr.misconceptions)
    return counter.most_common(top_n)
