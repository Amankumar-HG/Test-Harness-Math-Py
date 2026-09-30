"""Unit tests for quiz question generation and grading."""

from unittest.mock import patch

import pytest

from app.quiz import OPS, build_quiz, generate_question, grade_answer


class TestGenerateQuestion:
    def test_addition(self):
        with patch("app.quiz.random.randint", side_effect=[7, 5]):
            q = generate_question(1, op="+")
        assert q["op"] == "+"
        assert q["a"] == 7
        assert q["b"] == 5
        assert q["correct"] == 12
        assert q["prompt"] == "7 + 5"

    def test_subtraction_non_negative(self):
        with patch("app.quiz.random.randint", side_effect=[10, 3]):
            q = generate_question(2, op="-")
        assert q["correct"] == 7
        assert q["prompt"] == "10 − 3"

    def test_subtraction_identical_numbers(self):
        with patch("app.quiz.random.randint", side_effect=[8, 8]):
            q = generate_question(3, op="-")
        assert q["correct"] == 0
        assert q["prompt"] == "8 − 8"

    def test_multiplication(self):
        with patch("app.quiz.random.randint", side_effect=[4, 6]):
            q = generate_question(3, op="*")
        assert q["correct"] == 24
        assert "×" in q["prompt"]

    def test_division_is_integer(self):
        with patch("app.quiz.random.randint", side_effect=[4, 5]):
            # b=4, quotient=5 => a=20, correct=5
            q = generate_question(4, op="/")
        assert q["a"] == 20
        assert q["b"] == 4
        assert q["correct"] == 5
        assert q["a"] % q["b"] == 0

    def test_random_op_from_ops(self):
        for _ in range(20):
            q = generate_question(1)
            assert q["op"] in OPS


class TestBuildQuiz:
    def test_default_length(self):
        quiz = build_quiz()
        assert len(quiz) == 10
        assert [q["id"] for q in quiz] == list(range(1, 11))

    def test_custom_length(self):
        quiz = build_quiz(3)
        assert len(quiz) == 3

    def test_rejects_invalid_length(self):
        with pytest.raises(ValueError):
            build_quiz(0)


class TestGradeAnswer:
    def setup_method(self):
        self.question = {
            "id": 1,
            "op": "+",
            "a": 2,
            "b": 3,
            "prompt": "2 + 3",
            "correct": 5,
        }

    def test_correct_int(self):
        assert grade_answer(self.question, 5) is True

    def test_correct_string(self):
        assert grade_answer(self.question, "5") is True

    def test_incorrect(self):
        assert grade_answer(self.question, "4") is False

    def test_blank_and_invalid(self):
        assert grade_answer(self.question, "") is False
        assert grade_answer(self.question, None) is False
        assert grade_answer(self.question, "abc") is False
        assert grade_answer(self.question, "  ") is False
