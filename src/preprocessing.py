"""
preprocessing.py
Lightweight text-cleaning utilities used before rubric scoring.
No heavy NLP dependencies are required, keeping the project easy to run
on any machine (per the 'use simple tools first' guidance).
"""
import re


def clean_text(text: str) -> str:
    """Lowercase, strip extra whitespace, remove non-essential punctuation
    while preserving code-relevant characters like ( ) : _ ."""
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def tokenize(text: str):
    """Simple word tokenizer that also keeps code tokens like 'for', 'if', 'except'."""
    text = clean_text(text)
    tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text)
    return tokens


def looks_like_code(text: str) -> bool:
    """Heuristic check for whether a submission is code vs. prose."""
    code_markers = ["def ", "return", "{", "}", ";", "select ", "create table", "import "]
    t = text.lower()
    return any(marker in t for marker in code_markers)


def word_count(text: str) -> int:
    return len(tokenize(text))
