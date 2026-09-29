"""Unit tests for status.get_status_score."""

from unittest.mock import patch

from status import get_status_score


class TestGetStatusScore:
    def test_returns_value_within_range(self):
        for _ in range(100):
            score = get_status_score()
            assert 0 <= score <= 100

    def test_returns_float_with_two_decimal_places(self):
        for _ in range(100):
            score = get_status_score()
            assert isinstance(score, float)
            assert round(score, 2) == score
    def test_returns_float_with_two_decimal_places(self):
        for _ in range(100):
            score = get_status_score()
            assert isinstance(score, float)
            assert round(score, 2) == score
            assert score == round(score, 2)  # Ensure it has at most 2 decimal places
            assert 0 <= score <= 100
