"""
test_pipeline.py
Basic workflow/validation tests for the AI Assignment Feedback Platform.
Run with: python3 -m pytest tests/test_pipeline.py -v
(or: python3 tests/test_pipeline.py  to run without pytest)
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from db import init_db, get_rubric, get_assignments
from ai_feedback import generate_feedback, aggregate_misconceptions
from utils import validate_submission_text, grading_consistency_score


def test_validation_rejects_empty():
    ok, _ = validate_submission_text("")
    assert ok is False


def test_validation_rejects_too_short():
    ok, _ = validate_submission_text("ok")
    assert ok is False


def test_validation_accepts_normal_text():
    ok, _ = validate_submission_text("def f(x): return x + 1")
    assert ok is True


def test_all_assignments_have_rubric():
    conn = init_db()
    assignments = get_assignments(conn)
    for a_id in assignments["assignment_id"]:
        rubric = get_rubric(conn, a_id)
        assert len(rubric) > 0, f"Assignment {a_id} has no rubric rows"


def test_strong_submission_scores_higher_than_poor():
    conn = init_db()
    rubric = get_rubric(conn, "A1").to_dict("records")
    strong = (
        "def process_numbers(nums):\n"
        "    if not nums:\n        return []\n"
        "    result = []\n    for n in nums:\n"
        "        if n < 0:\n            continue\n"
        "        elif n == 0:\n            result.append(0)\n"
        "        else:\n            result.append(n*2)\n    return result"
    )
    poor = "i used loop to do it and it works fine on my computer"

    r_strong = generate_feedback("T1", "A1", strong, rubric)
    r_poor = generate_feedback("T2", "A1", poor, rubric)
    assert r_strong.score > r_poor.score


def test_scoring_is_deterministic():
    conn = init_db()
    rubric = get_rubric(conn, "A2").to_dict("records")
    text = "Binary search is O(log n) because it halves the array each step."
    scores = [generate_feedback(f"T{i}", "A2", text, rubric).score for i in range(3)]
    assert grading_consistency_score(scores) == 0.0


def test_misconception_aggregation_does_not_exceed_submission_count():
    conn = init_db()
    rubric = get_rubric(conn, "A1").to_dict("records")
    texts = [
        "def f(a): return a*2",
        "i used loop to do it and it works fine on my computer",
        "def process(nums):\n    result = []\n    for n in nums:\n        result.append(n*2)\n    return result",
    ]
    results = [generate_feedback(f"B{i}", "A1", t, rubric) for i, t in enumerate(texts)]
    top = aggregate_misconceptions(results)
    for _, count in top:
        assert count <= len(results)


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        print(f"PASS: {t.__name__}")
        passed += 1
    print(f"\n{passed}/{len(tests)} tests passed.")
