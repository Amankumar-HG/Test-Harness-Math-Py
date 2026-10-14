"""Route tests for the Adaptive Problem Engine."""

import pytest

from app import create_app


def _extract_first_meter_fill_width(html: str) -> str:
    marker = 'class="meter-fill" style="width: '
    start = html.find(marker)
    assert start != -1, "dashboard should render a meter-fill element"
    start += len(marker)
    end = html.find("%", start)
    assert end != -1, "meter-fill width style should include a %"
    # Normalise to the same format used by the mastery display (whole percent).
    return str(int(round(float(html[start:end]))))


@pytest.fixture
def app(tmp_path):
    db = tmp_path / "test.sqlite3"
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SESSION_LENGTH": 3,
            "DATABASE": str(db),
        }
    )
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def test_dashboard_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Adaptive Problem Engine" in response.data


def test_dashboard_meter_fill_matches_mastery_percentage(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # The dashboard shows a "Mastery" percentage text for each card, and the bar
    # should fill proportionally left-to-right (not inverted as 100 - mastery).
    assert "Mastery</dt><dd>" in html
    width_value = _extract_first_meter_fill_width(html)
    assert f"Mastery</dt><dd>{width_value}%" in html
    assert b"Addition" in response.data


def test_start_practice_and_answer_flow(client, app):
    start = client.post("/practice/start", follow_redirects=False)
    assert start.status_code == 302
    assert "/practice" in start.headers["Location"]

    play = client.get("/practice")
    assert play.status_code == 200
    assert b"Submit" in play.data

    with client.session_transaction() as sess:
        item = sess["practice"]["current_item"]
        answer = item["correct"]
        if item.get("answer_type") == "fraction":
            answer = f"{answer[0]}/{answer[1]}"

    client.post("/practice/answer", data={"answer": str(answer)})

    with client.session_transaction() as sess:
        assert sess["practice"]["answered"] == 1
        assert sess["practice"]["correct"] == 1


def test_session_completes_to_summary(client):
    client.post("/practice/start")
    for _ in range(3):
        with client.session_transaction() as sess:
            item = sess["practice"]["current_item"]
            answer = item["correct"]
            if item.get("answer_type") == "fraction":
                answer = f"{answer[0]}/{answer[1]}"
        client.post("/practice/answer", data={"answer": str(answer)})

    summary = client.get("/practice/summary")
    assert summary.status_code == 200
    assert b"Session complete" in summary.data
    assert b"100%" in summary.data


def test_practice_without_session_redirects(client):
    response = client.get("/practice", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_reset_creates_new_learner(client):
    client.get("/")
    with client.session_transaction() as sess:
        first = sess["learner_id"]
    client.post("/reset")
    with client.session_transaction() as sess:
        assert sess["learner_id"] != first


def test_focus_locked_skill_falls_back(client):
    # linear_eq should be locked for a new learner
    response = client.post(
        "/practice/start",
        data={"skill_id": "linear_eq"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess["practice"]["forced_skill"] is None
        assert sess["practice"]["current_item"]["skill_id"] == "add_sub"
