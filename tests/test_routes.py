"""Route tests for the Math Quiz Flask app."""

import time

import pytest

from app import create_app


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "QUIZ_LENGTH": 3,
            "QUIZ_TIME_LIMIT": 60,
        }
    )
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Math Quiz" in response.data
    assert b"Start Quiz" in response.data


def test_play_without_session_redirects_home(client):
    response = client.get("/quiz/play", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_results_without_session_redirects_home(client):
    response = client.get("/quiz/results", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_start_play_answer_flow(client, app):
    start = client.post("/quiz/start", follow_redirects=False)
    assert start.status_code == 302
    assert "/quiz/play" in start.headers["Location"]

    play = client.get("/quiz/play")
    assert play.status_code == 200
    assert b"Question 1 / 3" in play.data

    with client.session_transaction() as sess:
        question = sess["questions"][0]
        correct = question["correct"]

    answer = client.post(
        "/quiz/answer",
        data={"answer": str(correct)},
        follow_redirects=False,
    )
    assert answer.status_code == 302
    assert "/quiz/play" in answer.headers["Location"]

    with client.session_transaction() as sess:
        assert sess["score"] == 1
        assert sess["current_index"] == 1


def test_completing_quiz_shows_results(client):
    client.post("/quiz/start")

    with client.session_transaction() as sess:
        questions = list(sess["questions"])

    for question in questions:
        client.post("/quiz/answer", data={"answer": str(question["correct"])})

    results = client.get("/quiz/results")
    assert results.status_code == 200
    assert b"Results" in results.data
    assert b"3" in results.data
    assert b"100%" in results.data


def test_wrong_answer_does_not_increment_score(client):
    client.post("/quiz/start")

    with client.session_transaction() as sess:
        correct = sess["questions"][0]["correct"]

    client.post("/quiz/answer", data={"answer": str(correct + 1)})

    with client.session_transaction() as sess:
        assert sess["score"] == 0
        assert sess["current_index"] == 1


def test_expired_timer_forces_results(client, app):
    client.post("/quiz/start")

    with client.session_transaction() as sess:
        sess["started_at"] = time.time() - 120
        sess["time_limit_sec"] = 60

    response = client.get("/quiz/play", follow_redirects=False)
    assert response.status_code == 302
    assert "/quiz/results" in response.headers["Location"]

    results = client.get("/quiz/results")
    assert results.status_code == 200
    assert b"Results" in results.data
