"""Tests for the progress/streak/effort/score-formatting logic in app.py.

These are the parts of app.py that don't require a live Textual screen --
tested by monkeypatching the module-level ``progress``/``course_week_nr``
globals ``compute_streaks``/``compute_effort``/``format_score_goal`` read,
rather than driving the actual TUI (see test_app_smoke.py for that).
"""
import datetime

import pytest

from myiagi_widget import app as app_module


def _date_in_week(weeknr, weekday):
    """A date landing in the ISO week compute_streaks/compute_effort bucket
    as ``weeknr`` (they derive weeknr as
    ``date.isocalendar().week - course_start_week + 1``), on the given
    ISO weekday (1=Monday..7=Sunday). Year is arbitrary -- only the
    week/weekday arithmetic matters to the functions under test.
    """
    iso_week = app_module.course_start_week + weeknr - 1
    return datetime.date.fromisocalendar(2026, iso_week, weekday)


def test_sparkline_bars_empty_for_all_zero():
    assert app_module.sparkline_bars([0, 0, 0]) == ''


def test_sparkline_bars_nonempty_for_some_activity():
    result = app_module.sparkline_bars([1, 2, 3, 0, 0, 0, 0])
    assert result != ''


def test_streak_stars_counts_current_week_streak():
    streaks = {5: 3}
    result = app_module.streak_stars(streaks, 5, current=True)
    assert result.count('★') == 3  # ★


def test_compute_streaks_and_effort_use_progress_scores(monkeypatch):
    monkeypatch.setattr(app_module, 'course_week_nr', 5)
    monkeypatch.setattr(app_module, 'progress', {
        'scores': [
            (1.0, _date_in_week(5, 1)),
            (1.0, _date_in_week(5, 2)),
            (1.0, _date_in_week(5, 3)),
        ],
        'current_score': 0,
        'highscores': {w: 0 for w in range(1, 16)},
    })

    streaks = app_module.compute_streaks()
    effort = app_module.compute_effort()

    assert streaks[5] >= 1
    assert sum(effort[5]) == 3


def test_format_score_goal_encourages_when_behind(monkeypatch):
    monkeypatch.setattr(app_module, 'course_week_nr', 1)
    monkeypatch.setattr(app_module, 'progress', {
        'scores': [],
        'current_score': 0.0,
        'highscores': {w: 0 for w in range(1, 16)},
    })

    message = app_module.format_score_goal()
    assert 'score goal' in message.lower()


def test_format_score_goal_praises_when_ahead(monkeypatch):
    monkeypatch.setattr(app_module, 'course_week_nr', 1)
    goal = app_module.score_goals[1]
    monkeypatch.setattr(app_module, 'progress', {
        'scores': [],
        # current_score is stored pre-division by score_multiplier
        'current_score': (goal + 1) / app_module.score_multiplier,
        'highscores': {w: 0 for w in range(1, 16)},
    })

    message = app_module.format_score_goal()
    assert 'ahead' in message.lower()
