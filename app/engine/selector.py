"""Adaptive next-item selection."""

from __future__ import annotations

import random
import time
from typing import Any

from app.engine.items import generate_item
from app.engine.mastery import DEFAULT_ABILITY, is_due
from app.engine.skills import SKILLS, unlocked_skills


def difficulty_for_ability(ability: float) -> int:
    if ability < 950:
        return 1
    if ability < 1200:
        return 2
    return 3


def choose_skill(
    skill_states: dict[str, dict[str, Any]],
    *,
    now: float | None = None,
    recent_skills: list[str] | None = None,
) -> str:
    """Pick the next skill: prefer due + low mastery among unlocked skills."""
    now = time.time() if now is None else now
    recent_skills = recent_skills or []
    mastery_map = {
        sid: float(skill_states.get(sid, {}).get("mastery", 0.0)) for sid in SKILLS
    }
    unlocked = unlocked_skills(mastery_map)
    if not unlocked:
        return "add_sub"

    due = []
    rest = []
    for skill in unlocked:
        state = skill_states.get(skill.id, {})
        bucket = due if is_due(state, now=now) or int(state.get("attempts", 0)) == 0 else rest
        bucket.append(skill)

    pool = due or rest

    def sort_key(skill):
        state = skill_states.get(skill.id, {})
        mastery = float(state.get("mastery", 0.0))
        recent_penalty = 30.0 if skill.id in recent_skills[-3:] else 0.0
        return mastery + recent_penalty

    pool.sort(key=sort_key)
    # Soft random among the weakest few
    candidates = pool[: max(1, min(3, len(pool)))]
    return random.choice(candidates).id


def next_item(
    skill_states: dict[str, dict[str, Any]],
    *,
    now: float | None = None,
    recent_skills: list[str] | None = None,
    forced_skill: str | None = None,
) -> dict[str, Any]:
    skill_id = forced_skill or choose_skill(
        skill_states, now=now, recent_skills=recent_skills
    )
    state = skill_states.get(skill_id, {})
    ability = float(state.get("ability", DEFAULT_ABILITY))
    difficulty = difficulty_for_ability(ability)
    # Occasionally probe adjacent difficulty
    if random.random() < 0.15:
        difficulty = max(1, min(3, difficulty + random.choice([-1, 1])))
    return generate_item(skill_id, difficulty)
