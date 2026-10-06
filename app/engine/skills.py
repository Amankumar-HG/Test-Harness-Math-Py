"""Skill graph: nodes, prerequisites, unlock thresholds."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    description: str
    prerequisites: tuple[str, ...]
    unlock_mastery: float = 60.0  # required mastery on each prereq


SKILLS: dict[str, Skill] = {
    "add_sub": Skill(
        id="add_sub",
        name="Addition & Subtraction",
        description="Whole-number sums and differences",
        prerequisites=(),
    ),
    "mul_div": Skill(
        id="mul_div",
        name="Multiplication & Division",
        description="Integer products and quotients",
        prerequisites=("add_sub",),
    ),
    "fractions": Skill(
        id="fractions",
        name="Fractions",
        description="Simplify and operate on simple fractions",
        prerequisites=("mul_div",),
    ),
    "order_ops": Skill(
        id="order_ops",
        name="Order of Operations",
        description="Evaluate expressions with mixed operations",
        prerequisites=("mul_div",),
    ),
    "linear_eq": Skill(
        id="linear_eq",
        name="Linear Equations",
        description="Solve one-step and two-step equations",
        prerequisites=("order_ops", "fractions"),
        unlock_mastery=55.0,
    ),
}


def skill_order() -> list[Skill]:
    """Topological-ish display order."""
    return [SKILLS[sid] for sid in ("add_sub", "mul_div", "fractions", "order_ops", "linear_eq")]


def is_unlocked(skill_id: str, mastery_by_skill: dict[str, float]) -> bool:
    skill = SKILLS[skill_id]
    for prereq in skill.prerequisites:
        if mastery_by_skill.get(prereq, 0.0) < skill.unlock_mastery:
            return False
    return True


def unlocked_skills(mastery_by_skill: dict[str, float]) -> list[Skill]:
    return [s for s in skill_order() if is_unlocked(s.id, mastery_by_skill)]
