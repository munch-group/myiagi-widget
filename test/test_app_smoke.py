"""Headless end-to-end smoke test for the myiagi TUI.

Drives ``STEPSApp`` through Textual's ``run_test()`` harness (no real
terminal needed). Exercises the swap/scoring logic by calling
``KeyLogger.key_up``/``key_down`` directly rather than simulating raw
arrow-key presses through the pilot -- that isolates this test from whether
Textual's key-event dispatch still auto-routes to ``key_<name>`` methods
(a convention the ported game logic relies on; verified separately against
a live terminal).
"""
import os

import pytest

from myiagi_widget import app as app_module
from myiagi_widget.app import KeyLogger, STEPSApp


@pytest.fixture(autouse=True)
def isolated_progress(monkeypatch, tmp_path):
    """Never touch the real ~/.myiagi_progress.pkl while testing."""
    # pickle_file_name only exists as a module attribute once run() has set it
    # (a global first assigned inside a function) -- raising=False lets the
    # test create it rather than requiring it to pre-exist.
    monkeypatch.setattr(app_module, 'pickle_file_name', str(tmp_path / 'progress.pkl'), raising=False)
    monkeypatch.setattr(app_module, 'progress', {
        'scores': [],
        'current_score': 0,
        'highscores': {w: 0 for w in range(1, 16)},
    })


def _sorted_by_swaps(key_logger: KeyLogger):
    """Drive key_logger's own swap logic until steps_list matches correct_order."""
    n = len(key_logger.steps_list)
    for target_pos in range(n):
        # selection sort: bring the correct next step into position via
        # repeated adjacent swaps, exactly as a player would with arrow keys.
        current_value = key_logger.correct_order[target_pos]
        current_pos = key_logger.steps_list.index(current_value)
        key_logger.focal = current_pos + 1  # 1-indexed, as on_key's digit branch sets it
        while current_pos > target_pos:
            key_logger.key_up()
            current_pos -= 1


@pytest.mark.asyncio
async def test_full_game_round_via_run_test():
    app = STEPSApp()
    async with app.run_test() as pilot:
        await pilot.pause()  # let on_mount's push_screen(steps_screen) settle
        # query_one() on the App searches its default screen, not whichever
        # one is on top of the stack -- query the active screen directly.
        key_logger = app.screen.query_one(KeyLogger)

        assert len(key_logger.steps_list) >= app_module.min_steps
        assert key_logger.is_correct is False

        _sorted_by_swaps(key_logger)
        # key_up()/key_down() already call is_correct_order() internally on
        # every swap (that's how scoring gets triggered during real play) --
        # check the resulting attribute rather than calling it again, which
        # would double-record the completed round.
        assert key_logger.is_correct is True

        # let the posted KeyLogger.Updated message reach
        # STEPSApp.on_key_logger_updated (which updates the stats table and
        # score-goal panel) before asserting -- otherwise a bug in that
        # handler wouldn't surface until a real interactive session.
        await pilot.pause()

        # scoring side effect: a completed round is persisted
        assert len(app_module.progress['scores']) == 1
        assert os.path.exists(app_module.pickle_file_name)


@pytest.mark.asyncio
async def test_arrow_keys_are_dispatched_to_key_up_key_down():
    """Confirms Textual still auto-routes a raw key press to a widget's
    ``key_<name>`` method (verified against textual/_dispatch_key.py, which
    looks up ``getattr(pump, f"key_{key}")``) -- unlike the other test in
    this file, this one presses real keys through the pilot instead of
    calling key_up/key_down directly, so it would fail if a future Textual
    version drops that convention.
    """
    app = STEPSApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        key_logger = app.screen.query_one(KeyLogger)

        before = key_logger.steps_list[:2]
        await pilot.press('1')
        await pilot.press('down')
        await pilot.pause()

        assert key_logger.steps_list[:2] == [before[1], before[0]]
