"""Unit tests for the Adaptive Problem Engine core."""

from app.engine.items import generate_item, grade_item
from app.engine.mastery import expected_success, update_after_attempt, default_skill_state
from app.engine.selector import choose_skill, difficulty_for_ability, next_item
from app.engine.skills import is_unlocked, unlocked_skills


class TestSkills:
    def test_add_sub_unlocked_by_default(self):
        assert is_unlocked("add_sub", {}) is True

    def test_mul_div_requires_add_sub_mastery(self):
        assert is_unlocked("mul_div", {"add_sub": 10}) is False
        assert is_unlocked("mul_div", {"add_sub": 60}) is True

    def test_linear_eq_needs_both_prereqs(self):
        assert is_unlocked(
            "linear_eq", {"order_ops": 60, "fractions": 40}
        ) is False
        assert is_unlocked(
            "linear_eq", {"order_ops": 60, "fractions": 60}
        ) is True

    def test_unlocked_list_grows(self):
        skills = unlocked_skills({"add_sub": 70})
        ids = [s.id for s in skills]
        assert "add_sub" in ids
        assert "mul_div" in ids
        assert "linear_eq" not in ids


class TestItems:
    def test_add_sub_grades(self):
        item = generate_item("add_sub", 1)
        assert grade_item(item, item["correct"]) is True
        assert grade_item(item, int(item["correct"]) + 1) is False

    def test_fraction_simplify_grades(self):
        item = {
            "prompt": "Simplify 4/8",
            "correct": [1, 2],
            "answer_type": "fraction",
        }
        assert grade_item(item, "1/2") is True
        assert grade_item(item, "2/4") is True
        assert grade_item(item, "1/3") is False

    def test_generate_all_skills(self):
        for skill_id in ("add_sub", "mul_div", "fractions", "order_ops", "linear_eq"):
            item = generate_item(skill_id, 2)
            assert item["skill_id"] == skill_id
            assert "prompt" in item
            assert "correct" in item


class TestMastery:
    def test_correct_raises_mastery(self):
        state = default_skill_state()
        updated = update_after_attempt(state, correct=True, difficulty=2, now=1000.0)
        assert updated["mastery"] > state["mastery"]
        assert updated["streak"] == 1
        assert updated["next_review_at"] > 1000.0

    def test_incorrect_resets_streak(self):
        state = default_skill_state()
        state["streak"] = 4
        state["mastery"] = 50
        updated = update_after_attempt(state, correct=False, difficulty=2, now=1000.0)
        assert updated["streak"] == 0
        assert updated["mastery"] < 50

    def test_expected_success_monotonic(self):
        assert expected_success(1400, 2) > expected_success(900, 2)


class TestSelector:
    def test_difficulty_bands(self):
        assert difficulty_for_ability(800) == 1
        assert difficulty_for_ability(1100) == 2
        assert difficulty_for_ability(1400) == 3

    def test_choose_skill_prefers_unlocked_low_mastery(self):
        states = {
            "add_sub": {**default_skill_state(), "mastery": 80, "attempts": 5, "next_review_at": 0},
            "mul_div": {**default_skill_state(), "mastery": 10, "attempts": 1, "next_review_at": 0},
        }
        # fill defaults for others
        for sid in ("fractions", "order_ops", "linear_eq"):
            states[sid] = default_skill_state()
        chosen = choose_skill(states, now=1e12)
        assert chosen in ("mul_div", "fractions", "order_ops", "add_sub")

    def test_next_item_returns_valid_payload(self):
        states = {sid: default_skill_state() for sid in ("add_sub", "mul_div", "fractions", "order_ops", "linear_eq")}
        item = next_item(states)
        assert item["skill_id"] == "add_sub"
        assert item["difficulty"] in (1, 2, 3)
    def test_incorrect_answer_schedules_next_review_soon(self):
        state = default_skill_state()
        now = 1000.0
        updated = update_after_attempt(state, correct=False, difficulty=2, now=now)
        assert updated["next_review_at"] == now + 0.5 * 3600.0  # Check if next review is set to 30 minutes later
        assert updated["next_review_at"] < now + 3600.0  # Ensure it's not set too far in the future
