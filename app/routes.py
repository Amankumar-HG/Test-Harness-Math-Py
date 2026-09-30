"""HTTP routes for the Math Quiz web app."""

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

from app.quiz import build_quiz, grade_answer

bp = Blueprint("quiz", __name__)


def _quiz_active() -> bool:
    return "questions" in session and "current_index" in session


def _remaining_seconds() -> int:
    started = session.get("started_at")
    limit = session.get("time_limit_sec", current_app.config["QUIZ_TIME_LIMIT"])
    if started is None:
        return 0
    elapsed = time.time() - float(started)
    return max(0, int(limit - elapsed) - 1)


def _time_expired() -> bool:
    return _quiz_active() and _remaining_seconds() <= 0


def _finalize_unanswered() -> None:
    """Mark remaining questions as unanswered when time expires or quiz ends."""
    questions = session.get("questions", [])
    answers = list(session.get("answers", []))
    index = session.get("current_index", 0)
    while len(answers) < len(questions):
        q = questions[len(answers)]
        answers.append(
            {
                "question_id": q["id"],
                "prompt": q["prompt"],
                "correct": q["correct"],
                "user_answer": None,
                "is_correct": False,
            }
        )
    session["answers"] = answers
    session["current_index"] = len(questions)
    session["finished"] = True


@bp.route("/")
def home():
    return render_template(
        "home.html",
        quiz_length=current_app.config["QUIZ_LENGTH"],
        time_limit=current_app.config["QUIZ_TIME_LIMIT"],
    )


@bp.route("/quiz/start", methods=["POST"])
def start_quiz():
    length = current_app.config["QUIZ_LENGTH"]
    time_limit = current_app.config["QUIZ_TIME_LIMIT"]
    session.clear()
    session["questions"] = build_quiz(length)
    session["current_index"] = 0
    session["answers"] = []
    session["score"] = 0
    session["started_at"] = time.time()
    session["time_limit_sec"] = time_limit
    session["finished"] = False
    return redirect(url_for("quiz.play"))


@bp.route("/quiz/play")
def play():
    if not _quiz_active():
        return redirect(url_for("quiz.home"))

    if session.get("finished") or _time_expired():
        if _time_expired() and not session.get("finished"):
            _finalize_unanswered()
        return redirect(url_for("quiz.results"))

    questions = session["questions"]
    index = session["current_index"]
    if index >= len(questions):
        session["finished"] = True
        return redirect(url_for("quiz.results"))

    question = questions[index]
    return render_template(
        "quiz.html",
        question=question,
        progress=index + 1,
        total=len(questions),
        remaining_seconds=_remaining_seconds(),
    )


@bp.route("/quiz/answer", methods=["POST"])
def answer():
    if not _quiz_active():
        return redirect(url_for("quiz.home"))

    if session.get("finished"):
        return redirect(url_for("quiz.results"))

    if _time_expired():
        _finalize_unanswered()
        return redirect(url_for("quiz.results"))

    questions = session["questions"]
    index = session["current_index"]
    if index >= len(questions):
        session["finished"] = True
        return redirect(url_for("quiz.results"))

    question = questions[index]
    user_raw = request.form.get("answer", "")
    is_correct = grade_answer(question, user_raw)

    answers = list(session.get("answers", []))
    answers.append(
        {
            "question_id": question["id"],
            "prompt": question["prompt"],
            "correct": question["correct"],
            "user_answer": user_raw.strip() if user_raw and str(user_raw).strip() else None,
            "is_correct": is_correct,
        }
    )
    session["answers"] = answers
    if is_correct:
        session["score"] = int(session.get("score", 0)) + 1
    session["current_index"] = index + 1

    if session["current_index"] >= len(questions) or _time_expired():
        if _time_expired():
            _finalize_unanswered()
        else:
            session["finished"] = True
        return redirect(url_for("quiz.results"))

    return redirect(url_for("quiz.play"))


@bp.route("/quiz/results")
def results():
    if not _quiz_active() and not session.get("finished"):
        # Allow results if we have answers from a finished quiz
        if "answers" not in session:
            return redirect(url_for("quiz.home"))

    if _quiz_active() and _time_expired() and not session.get("finished"):
        _finalize_unanswered()

    questions = session.get("questions", [])
    answers = session.get("answers", [])
    score = int(session.get("score", 0))
    total = len(questions) or len(answers)
    percent = round((score / total) * 100) if total else 0

    return render_template(
        "results.html",
        score=score,
        total=total,
        percent=percent,
        answers=answers,
    )
