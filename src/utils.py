"""
utils.py
Small shared helpers: validation, simple evaluation metrics used to
satisfy the 'Validation using metrics, test cases, or scenario checks'
requirement.
"""
from datetime import datetime


def validate_submission_text(text: str) -> tuple[bool, str]:
    """Basic guardrail: reject empty/too-short submissions before they hit the AI module."""
    if not text or not text.strip():
        return False, "Submission is empty. Please write or paste your answer/code."
    if len(text.strip()) < 10:
        return False, "Submission is too short to evaluate meaningfully (min 10 characters)."
    return True, ""


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def grading_consistency_score(scores: list[float]) -> float:
    """A simple evaluation metric: how consistent the AI scorer is when the
    same submission is scored multiple times (it should be deterministic
    in template mode). Returns the standard deviation across repeated runs
    -- 0.0 means perfectly consistent/deterministic."""
    if len(scores) < 2:
        return 0.0
    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    return variance ** 0.5
