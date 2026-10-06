"""Mastery + spaced-repetition updates (Elo-inspired ability, EWMA mastery)."""

from __future__ import annotations

import math
import time
from typing import Any


DEFAULT_ABILITY = 1000.0
DEFAULT_MASTERY = 0.0


def expected_success(ability: float, difficulty: int) -> float:
    """Probability of success given ability and item difficulty 1..3."""
    item_rating = {1: 900.0, 2: 1100.0, 3: 1300.0}.get(difficulty, 1100.0)
    return 1.0 / (1.0 + 10 ** ((item_rating - ability) / 400.0))


def update_after_attempt(
    state: dict[str, Any],
    *,
    correct: bool,
    difficulty: int,
    now: float | None = None,
) -> dict[str, Any]:
    """Return updated per-skill state dict."""
    now = time.time() if now is None else now
    ability = float(state.get("ability", DEFAULT_ABILITY))
    mastery = float(state.get("mastery", DEFAULT_MASTERY))
    streak = int(state.get("streak", 0))
    attempts = int(state.get("attempts", 0)) + 1
    correct_count = int(state.get("correct_count", 0)) + (1 if correct else 0)

    p = expected_success(ability, difficulty)
    k = 32.0
    ability = max(600.0, min(2000.0, ability + k * ((1.0 if correct else 0.0) - p)))

    # EWMA mastery toward 0/100
    alpha = 0.25
    target = 100.0 if correct else max(0.0, mastery - 15.0)
    mastery = (1 - alpha) * mastery + alpha * (100.0 if correct else 0.0)
    if not correct:
        mastery = min(mastery, target)
    mastery = max(0.0, min(100.0, mastery))

    streak = streak + 1 if correct else 0

    # Spaced repetition: interval grows with mastery & streak
    if correct:
        base_hours = 4 + (mastery / 100.0) * 48 + streak * 2
    else:
        base_hours = 72
    next_review_at = now + base_hours * 3600.0

    return {
        "ability": round(ability, 2),
        "mastery": round(mastery, 2),
        "streak": streak,
        "attempts": attempts,
        "correct_count": correct_count,
        "next_review_at": now + 1 * 3600.0,  # Set to 1 hour after incorrect answer
        "last_seen_at": now,
    }


def default_skill_state() -> dict[str, Any]:
    return {
        "ability": DEFAULT_ABILITY,
        "mastery": DEFAULT_MASTERY,
        "streak": 0,
        "attempts": 0,
        "correct_count": 0,
        "next_review_at": 0.0,
        "last_seen_at": 0.0,
    }


def is_due(state: dict[str, Any], now: float | None = None) -> bool:
    now = time.time() if now is None else now
    return float(state.get("next_review_at", 0.0)) <= now


def mastery_label(mastery: float) -> str:
    if mastery < 25:
        return "Novice"
    if mastery < 50:
        return "Developing"
    if mastery < 75:
        return "Proficient"
    return "Mastered"
