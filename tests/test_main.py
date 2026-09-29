"""Unit tests for main entrypoint."""

from unittest.mock import patch

import main


def test_main_prints_status_score(capsys):
    with patch("main.get_status_score", return_value=87.5):
        main.main()

    captured = capsys.readouterr()
    assert "Status score is" in captured.out
    assert "87.5" in captured.out
