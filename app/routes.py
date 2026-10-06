"""HTTP routes for the Adaptive Problem Engine."""

from __future__ import annotations

import time

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.engine.items import grade_item
from app.engine.mastery import is_due, mastery_label, update_after_attempt
from app.engine.selector import next_item
from app.engine.skills import SKILLS, is_unlocked, skill_order

bp = Blueprint("ape", __name__)


def _store():
    return current_app.extensions["store"]


def _learner_id() -> str:
    store = _store()
    learner_id = store.ensure_learner(session.get("learner_id"))
    session["learner_id"] = learner_id
    return learner_id


def _skill_cards(states: dict) -> list[dict]:
    mastery_map = {sid: float(states[sid]["mastery"]) for sid in SKILLS}
    cards = []
    for skill in skill_order():
        state = states[skill.id]
        unlocked = is_unlocked(skill.id, mastery_map)
        cards.append(
            {
                "skill": skill,
                "state": state,
                "unlocked": unlocked,
                "due": unlocked and is_due(state),
                "label": mastery_label(float(state["mastery"])),
            }
        )
    return cards


@bp.route("/")
def dashboard():
    learner_id = _learner_id()
    store = _store()
    states = store.get_all_states(learner_id)
    cards = _skill_cards(states)
    recent = store.recent_attempts(learner_id, limit=8)
    overall = round(
        sum(float(states[s.id]["mastery"]) for s in skill_order()) / len(SKILLS), 1
    )
    return render_template(
        "dashboard.html",
        cards=cards,
        recent=recent,
        overall=overall,
        session_length=current_app.config["SESSION_LENGTH"],
        skills=SKILLS,
    )


@bp.route("/practice/start", methods=["POST"])
def start_practice():
    learner_id = _learner_id()
    store = _store()
    states = store.get_all_states(learner_id)
    forced = request.form.get("skill_id") or None
    if forced and forced not in SKILLS:
        forced = None
    if forced:
        mastery_map = {sid: float(states[sid]["mastery"]) for sid in SKILLS}
        if not is_unlocked(forced, mastery_map):
            forced = None

    item = next_item(states, forced_skill=forced)
    session["practice"] = {
        "active": True,
        "target": int(current_app.config["SESSION_LENGTH"]),
        "answered": 0,
        "correct": 0,
        "recent_skills": [],
        "current_item": item,
        "history": [],
        "forced_skill": forced,
        "started_at": time.time(),
    }
    return redirect(url_for("ape.practice"))


@bp.route("/practice")
def practice():
    practice_state = session.get("practice") or {}
    if not practice_state.get("active") or not practice_state.get("current_item"):
        return redirect(url_for("ape.dashboard"))

    item = practice_state["current_item"]
    skill = SKILLS[item["skill_id"]]
    return render_template(
        "practice.html",
        item=item,
        skill=skill,
        progress=practice_state["answered"] + 1,
        total=practice_state["target"],
        correct_so_far=practice_state["correct"],
    )


@bp.route("/practice/answer", methods=["POST"])
def practice_answer():
    practice_state = session.get("practice") or {}
    if not practice_state.get("active") or not practice_state.get("current_item"):
        return redirect(url_for("ape.dashboard"))

    item = practice_state["current_item"]
    user_raw = request.form.get("answer", "")
    correct = grade_item(item, user_raw)
    now = time.time()

    learner_id = _learner_id()
    store = _store()
    states = store.get_all_states(learner_id)
    skill_id = item["skill_id"]
    updated = update_after_attempt(
        states.get(skill_id, {}),
        correct=correct,
        difficulty=int(item["difficulty"]),
        now=now,
    )
    store.save_skill_state(learner_id, skill_id, updated)
    store.log_attempt(
        learner_id,
        skill_id=skill_id,
        difficulty=int(item["difficulty"]),
        correct=correct,
        prompt=item["prompt"],
        user_answer=user_raw.strip() if user_raw and str(user_raw).strip() else None,
        created_at=now,
    )

    history = list(practice_state.get("history", []))
    history.append(
        {
            "prompt": item["prompt"],
            "correct_answer": item["correct"],
            "answer_type": item.get("answer_type", "int"),
            "user_answer": user_raw.strip() if user_raw else "",
            "is_correct": correct,
            "skill_id": skill_id,
            "difficulty": item["difficulty"],
            "mastery_after": updated["mastery"],
        }
    )
    recent_skills = list(practice_state.get("recent_skills", []))
    recent_skills.append(skill_id)

    practice_state["answered"] = int(practice_state.get("answered", 0)) + 1
    practice_state["correct"] = int(practice_state.get("correct", 0)) + (1 if correct else 0)
    practice_state["history"] = history
    practice_state["recent_skills"] = recent_skills
    practice_state["last_feedback"] = {
        "is_correct": correct,
        "correct_answer": item["correct"],
        "answer_type": item.get("answer_type", "int"),
    }

    if practice_state["answered"] >= int(practice_state["target"]):
        practice_state["active"] = False
        practice_state["current_item"] = None
        session["practice"] = practice_state
        return redirect(url_for("ape.summary"))

    states[skill_id] = updated
    practice_state["current_item"] = next_item(
        states,
        recent_skills=recent_skills,
        forced_skill=practice_state.get("forced_skill") or recent_skills[-1],
    )
    session["practice"] = practice_state
    return redirect(url_for("ape.practice"))


@bp.route("/practice/summary")
def summary():
    practice_state = session.get("practice") or {}
    history = practice_state.get("history") or []
    if not history:
        return redirect(url_for("ape.dashboard"))

    answered = int(practice_state.get("answered", len(history)))
    correct = int(practice_state.get("correct", 0))
    percent = round((correct / answered) * 100) if answered else 0
    learner_id = _learner_id()
    states = _store().get_all_states(learner_id)
    cards = _skill_cards(states)
    return render_template(
        "summary.html",
        history=history,
        answered=answered,
        correct=correct,
        percent=percent,
        cards=cards,
        skills=SKILLS,
    )


@bp.route("/reset", methods=["POST"])
def reset_progress():
    store = _store()
    session.clear()
    learner_id = store.create_learner()
    session["learner_id"] = learner_id
    return redirect(url_for("ape.dashboard"))
