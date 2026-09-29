"""Unit tests for status.get_status_score."""

from unittest.mock import patch

from status import get_status_score


class TestGetStatusScore:
    def test_returns_value_within_range(self):
        for _ in range(100):
            score = get_status_score()
            assert 0 <= score <= 100
