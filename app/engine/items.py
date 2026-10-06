"""Problem generators keyed by skill and difficulty (1=easy, 2=medium, 3=hard)."""

from __future__ import annotations

import math
import random
import uuid
from typing import Any


Difficulty = int  # 1, 2, 3


def _gcd(a: int, b: int) -> int:
    return math.gcd(a, b)


def generate_item(skill_id: str, difficulty: Difficulty = 2) -> dict[str, Any]:
    difficulty = max(1, min(3, int(difficulty)))
    generators = {
        "add_sub": _gen_add_sub,
        "mul_div": _gen_mul_div,
        "fractions": _gen_fractions,
        "order_ops": _gen_order_ops,
        "linear_eq": _gen_linear_eq,
    }
    if skill_id not in generators:
        raise ValueError(f"Unknown skill: {skill_id}")
    item = generators[skill_id](difficulty)
    item.update(
        {
            "id": str(uuid.uuid4()),
            "skill_id": skill_id,
            "difficulty": difficulty,
        }
    )
    return item


def grade_item(item: dict[str, Any], user_input: Any) -> bool:
    if user_input is None:
        return False
    text = str(user_input).strip().replace(" ", "")
    if not text:
        return False

    answer_type = item.get("answer_type", "int")
    correct = item["correct"]

    if answer_type == "fraction":
        return _parse_fraction(text) == tuple(correct)

    try:
        if answer_type == "float":
            return abs(float(text) - float(correct)) < 1e-6
        return int(float(text)) == int(correct)
    except (TypeError, ValueError):
        return False


def _parse_fraction(text: str) -> tuple[int, int] | None:
    if "/" in text:
        parts = text.split("/", 1)
        try:
            num, den = int(parts[0]), int(parts[1])
        except ValueError:
            return None
        if den == 0:
            return None
        g = _gcd(abs(num), abs(den))
        num, den = num // g, den // g
        if den < 0:
            num, den = -num, -den
        return num, den
    try:
        return int(text), 1
    except ValueError:
        return None


def _gen_add_sub(difficulty: Difficulty) -> dict[str, Any]:
    span = {1: 20, 2: 50, 3: 100}[difficulty]
    op = random.choice(["+", "-"])
    if op == "+":
        a, b = random.randint(1, span), random.randint(1, span)
        return {
            "prompt": f"{a} + {b}",
            "correct": a + b,
            "answer_type": "int",
            "hint": "Add the two numbers.",
        }
    a = random.randint(1, span)
    b = random.randint(1, a)
    return {
        "prompt": f"{a} − {b}",
        "correct": a - b,
        "answer_type": "int",
        "hint": "Subtract the second number from the first.",
    }


def _gen_mul_div(difficulty: Difficulty) -> dict[str, Any]:
    hi = {1: 8, 2: 12, 3: 15}[difficulty]
    if random.choice([True, False]):
        a, b = random.randint(2, hi), random.randint(2, hi)
        return {
            "prompt": f"{a} × {b}",
            "correct": a * b,
            "answer_type": "int",
            "hint": "Multiply the factors.",
        }
    b = random.randint(2, hi)
    q = random.randint(2, hi)
    a = b * q
    return {
        "prompt": f"{a} ÷ {b}",
        "correct": q,
        "answer_type": "int",
        "hint": "Divide; answer is a whole number.",
    }


def _gen_fractions(difficulty: Difficulty) -> dict[str, Any]:
    if difficulty == 1:
        # Simplify
        g = random.randint(2, 6)
        num = random.randint(1, 8) * g
        den = random.randint(num // g + 1, 12) * g
        simp_g = _gcd(num, den)
        return {
            "prompt": f"Simplify {num}/{den} (answer as a/b)",
            "correct": [num // simp_g, den // simp_g],
            "answer_type": "fraction",
            "hint": "Divide numerator and denominator by their GCD.",
        }
    # Add fractions with related denominators
    den = random.choice([4, 6, 8, 10, 12])
    a = random.randint(1, den - 1)
    b = random.randint(1, den - 1)
    if difficulty == 3:
        # different denominators (one multiple of the other)
        d1 = random.choice([2, 3, 4])
        d2 = d1 * random.choice([2, 3])
        a, b = random.randint(1, d1 - 1), random.randint(1, d2 - 1)
        num = a * (d2 // d1) + b
        den = d2
        g = _gcd(num, den)
        return {
            "prompt": f"{a}/{d1} + {b}/{d2} (answer as a/b)",
            "correct": [num // g, den // g],
            "answer_type": "fraction",
            "hint": "Find a common denominator first.",
        }
    num = a + b
    g = _gcd(num, den)
    return {
        "prompt": f"{a}/{den} + {b}/{den} (answer as a/b)",
        "correct": [num // g, den // g],
        "answer_type": "fraction",
        "hint": "Same denominator — add numerators, then simplify.",
    }


def _gen_order_ops(difficulty: Difficulty) -> dict[str, Any]:
    if difficulty == 1:
        a, b, c = random.randint(2, 9), random.randint(2, 9), random.randint(2, 9)
        prompt = f"{a} + {b} × {c}"
        correct = a + b * c
    elif difficulty == 2:
        a, b, c, d = (
            random.randint(2, 9),
            random.randint(2, 9),
            random.randint(2, 6),
            random.randint(2, 6),
        )
        prompt = f"({a} + {b}) × {c} − {d}"
        correct = a + b * c - d
    else:
        a, b, c = random.randint(4, 12), random.randint(2, 6), random.randint(2, 5)
        # a - b * c + (b + c)
        prompt = f"{a} − {b} × {c} + ({b} + {c})"
        correct = a - b * c + (b + c)
    return {
        "prompt": prompt,
        "correct": correct,
        "answer_type": "int",
        "hint": "Remember PEMDAS / BODMAS.",
    }


def _gen_linear_eq(difficulty: Difficulty) -> dict[str, Any]:
    if difficulty == 1:
        a = random.randint(2, 9)
        x = random.randint(1, 12)
        b = a * x
        return {
            "prompt": f"{a}x = {b}. Find x",
            "correct": x,
            "answer_type": "int",
            "hint": "Divide both sides by the coefficient of x.",
        }
    if difficulty == 2:
        a = random.randint(2, 8)
        x = random.randint(1, 10)
        c = random.randint(1, 15)
        b = a * x + c
        return {
            "prompt": f"{a}x + {c} = {b}. Find x",
            "correct": x,
            "answer_type": "int",
            "hint": "Subtract the constant, then divide.",
        }
    a = random.randint(2, 7)
    x = random.randint(1, 10)
    c = random.randint(1, 12)
    # a(x + c) = right
    right = a * (x + c)
    return {
        "prompt": f"{a}(x + {c}) = {right}. Find x",
        "correct": x,
        "answer_type": "int",
        "hint": "Expand or divide both sides by the outer factor first.",
    }
