"""Math quiz question generation and grading."""

from __future__ import annotations

import random
from typing import Any


OPS = ("+", "-", "*", "/")


def _generate_operands(op: str) -> tuple[int, int, int]:
    """Return (a, b, correct) for the given operation."""
    if op == "+":
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        return a, b, a + b
    if op == "-":
        a = random.randint(1, 20)
        b = random.randint(1, a)  # non-negative result
        return a, b, a - b or 1
    if op == "*":
        a = random.randint(1, 12)
        b = random.randint(1, 12)
        return a, b, a * b
    # Division: integer quotient only
    b = random.randint(1, 12)
    quotient = random.randint(1, 12)
    a = b * quotient
    return a, b, quotient


def generate_question(question_id: int, op: str | None = None) -> dict[str, Any]:
    """Build a single quiz question dict."""
    op = op if op in OPS else random.choice(OPS)
    a, b, correct = _generate_operands(op)
    symbol = {"+": "+", "-": "−", "*": "×", "/": "÷"}[op]
    return {
        "id": question_id,
        "op": op,
        "a": a,
        "b": b,
        "prompt": f"{a} {symbol} {b}",
        "correct": correct,
    }


def build_quiz(n: int = 10) -> list[dict[str, Any]]:
    """Generate n quiz questions with mixed operations."""
    if n < 1:
        raise ValueError("n must be at least 1")
    return [generate_question(i + 1) for i in range(n)]


def grade_answer(question: dict[str, Any], user_input: Any) -> bool:
    """Return True if user_input matches the correct integer answer."""
    if user_input is None:
        return False
    text = str(user_input).strip()
    if not text:
        return False
    try:
        value = int(text)
    except (TypeError, ValueError):
        return False
    return value == int(question["correct"])
