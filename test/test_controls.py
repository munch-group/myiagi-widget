"""Tests for the demo-variable pool and per-week difficulty ramp."""
import pytest
from steps_widget import steps as steps_module

from myiagi_widget import controls


def test_topic_probs_types_are_cumulative_to_one():
    values = list(controls.topic_probs['types'].values())
    assert values == sorted(values)
    assert values[-1] == pytest.approx(1.0)


def test_topic_probs_operations_are_cumulative_to_one():
    values = list(controls.topic_probs['operations'].values())
    assert values == sorted(values)
    assert values[-1] == pytest.approx(1.0)


def test_difficulty_ramp_defined_for_every_week():
    assert controls.leaf_prob is not None
    assert controls.min_steps < controls.max_steps
    assert controls.max_expr_len > 0


def test_score_goals_increase_with_week():
    goals = [controls.score_goals[w] for w in range(1, 16)]
    assert goals == sorted(goals)


def test_demo_variables_synced_onto_steps_widget_module():
    # _steps() dispatches against steps_widget.steps's own globals(), not the
    # caller's -- controls.py must mirror every demo variable there for a
    # generated expression referencing e.g. "foo" or "accounts" to trace.
    for name in controls.numbers + controls.strings + controls.lists + controls.dicts:
        assert hasattr(steps_module, name)
        assert getattr(steps_module, name) == getattr(controls, name)
