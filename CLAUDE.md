# CLAUDE.md

Project context for `myiagi-widget` -- a `textual` terminal trainer game where
students reorder the shuffled evaluation steps of a randomly generated Python
expression back into the correct order.

## What this is

`myiagi-widget` is the new home for the `myiagi` TUI (`bp_help/text_gui.py`,
"Wax On - Wax Off" / "STEPS OF DOOM") that used to live in the `bp-help`
teaching-tool repo (a course package for an introductory Python programming
class). `bp-help` also shipped a `%%steps` cell magic and `print-steps`
console script built on the same stepper engine -- those were ported earlier
to [`steps-widget`](https://github.com/munch-group/steps-widget), which
deliberately left `myiagi` out of scope. This repo picks that back up: rather
than re-vendoring the stepper, `myiagi-widget` **depends on `steps-widget`**
and calls `steps_widget.steps._steps()` directly.

The game logic (`Expression` node classes, `randomExpression`, difficulty
ramp, scoring/streak bookkeeping) was ported close to verbatim from
`text_gui.py`/`controls.py`; only the stepper wiring changed (see "Sharing
globals with steps_widget.steps" below), plus two fixes for Textual API
changes since `bp-help`'s pin (`textual==0.35.1`) -- see "Textual version
notes" below.

The repo was scaffolded from the `munch-group` Python-library template (pixi
environment, quartodoc docs, conda/PyPI release automation) -- the same
template `steps-widget`, `turtle-widget`, and `codelens-widget` use.

## Package layout

The package is `myiagi_widget` under `src/`:

- `src/myiagi_widget/controls.py` -- the fixed pool of demo variables
  (`numbers`/`strings`/`lists`/`dicts`, e.g. `foo`, `accounts`, `records`) and
  the per-course-week difficulty ramp (`topic_probs`, `leaf_prob`,
  `min_steps`/`max_steps`/`max_expr_len`, `score_goals`), derived from a
  "course week number" computed from the real calendar date
  (`course_start_week = 35`, ISO week). Also syncs every demo variable onto
  `steps_widget.steps`'s module namespace at import time -- see below.
- `src/myiagi_widget/expressions.py` -- `Expression` node classes (`Number`,
  `String`, `BinaryExpression`, `GetIndexExpression`, etc.) and
  `randomExpression`/`get_expression`, which build a random expression tree
  biased by `topic_probs`/`leaf_prob` and stringify it. Does
  `from .controls import *` so the demo variables are in *its own* globals()
  for the `eval()`/`globals()[name]` lookups inside `_randomExpression`.
- `src/myiagi_widget/app.py` -- the `textual` App (`STEPSApp`/`STEPS`
  screen/`KeyLogger`/`PlayerStats` widgets) and the `myiagi` console-script
  entry point (`run()`). `KeyLogger.next_expression()` calls
  `get_expression()` then `steps_widget.steps._steps()` to get the
  ground-truth step list the student must reconstruct; `key_up`/`key_down`
  (dispatched automatically by Textual on arrow-key presses -- see
  `textual._dispatch_key`) swap adjacent steps and check
  `is_correct_order()`, which persists score/streak state to
  `~/.myiagi_progress.pkl`.
- `src/myiagi_widget/app.css` -- the `textual` stylesheet for `myiagi`'s grid
  layout (header banner across the top; step log left; stats table
  top-right; score-goal message bottom-right).
- `src/myiagi_widget/__init__.py` -- intentionally empty, like `bp_help`'s
  was -- so the `myiagi` console script keeps working without importing
  anything beyond what `app.py` itself needs.
- `test/` -- headless pytest suite: `test_expressions.py`/`test_controls.py`
  test the pure generation/difficulty logic; `test_scoring.py` tests the
  streak/effort/score-formatting functions in `app.py` via monkeypatched
  `progress`/`course_week_nr` globals; `test_app_smoke.py` drives the actual
  `textual` App end-to-end through `run_test()` (see "Testing approach").

## Sharing globals with steps_widget.steps

`steps_widget.steps._steps()` dispatches against **its own module's**
`globals()` (its dispatch functions call bare `globals()`, not the caller's
-- see `steps-widget`'s own CLAUDE.md), so a generated expression referencing
`foo`, `accounts[1]`, etc. only traces correctly if those names are also
attributes on the `steps_widget.steps` module itself, not just on whatever
module built the expression string.

`controls.py` handles this once, at import time:

```python
from steps_widget import steps as _steps_module
...
for _name in numbers + strings + lists + dicts:
    setattr(_steps_module, _name, globals()[_name])
```

This mirrors what every `bp-help` entry point used to do implicitly by
`exec()`-ing `steps.py`'s source into a shared namespace instead of importing
it. The demo variables are static for the life of the process (computed once
at import), so this sync also only needs to run once -- it is not re-run if
those names were ever reassigned.

`expressions.py` needs the same variables in *its own* globals for a
different reason: `_randomExpression`'s `eval(str(expr))` / `globals()[var]`
calls (used to validate/introspect candidate sub-expressions while building
the tree) resolve against whichever module they're running in. Its
`from .controls import *` handles that side.

## Textual version notes

`bp-help`'s original `text_gui.py` pinned `textual==0.35.1` and refused to
run on Python >=3.11 (a `steps.py`-related constraint that no longer applies
here, since `steps_widget.steps` already handles 3.10-3.13 -- see
`steps-widget`'s CLAUDE.md). Porting to a current `textual` (tested against
8.2.8) surfaced two breaking API changes, both fixed in `app.py`:

- **`App.SCREENS` must map to a Screen *class* (or callable), not a
  pre-instantiated instance** -- the original code did
  `SCREENS = {"steps": STEPS()}` and read back `self.SCREENS['steps']`.
  `STEPSApp` now instantiates its own `STEPS()` once in `on_mount()`, stores
  it as `self.steps_screen`, and pushes/reads that instead. The `escape`
  binding accordingly calls a real `action_show_steps()` method instead of
  the `"push_screen('steps')"` action-string (which depended on the named
  `SCREENS` registry entry).
- **`App.query_one()` searches the app's default screen, not whichever
  screen is on top of the stack.** Tests (and anything else wanting to reach
  into the live UI) must query `app.screen.query_one(...)` instead.

The `key_up`/`key_down` convenience dispatch (Textual calling a widget's
`key_<name>` method automatically on a matching key press, with no `BINDINGS`
entry needed) is unchanged in 8.2.8 -- confirmed both by reading
`textual/_dispatch_key.py` and by `test_app_smoke.py`'s
`test_arrow_keys_are_dispatched_to_key_up_key_down`, which presses a real key
through `Pilot.press()` rather than calling the method directly.

If bumping `textual` further, re-check both of the above against the
changelog before assuming the game still behaves the same way.

## Known behavior carried over from bp-help (not bugs to "fix")

- **`-w <week>` only changes which week a completed round's score/streak is
  recorded against -- it does not change expression difficulty.**
  `topic_probs`/`leaf_prob`/`min_steps`/`max_steps`/`max_expr_len` are
  computed once in `controls.py` at import time from the real calendar-derived
  course week; `run()`'s `-w` override only reassigns `app.py`'s own
  `course_week_nr` name afterward, which `controls.py`'s already-computed
  values never see. This matches `bp-help`'s original behavior exactly.
- `controls.py`'s `strings` pool is `['label', 'tag', 'fix']` -- `nam` (also
  assigned on the same line, `label, tag, fix, nam = 'Ib', 'Bo', '42', 'Bo'`)
  is never added to it and so is never actually used by the generator. Same
  in the original `bp-help` source; not something introduced here.

## Environment & commands

Pixi-managed (config in `pyproject.toml` under `[tool.pixi.*]`; channels
`conda-forge` + `sepandhaghighi` (for `art`, which conda-forge doesn't
package) + `munch-group` (for `steps-widget`, once published there)).

**`pixi install` cannot solve this workspace yet**: `steps-widget` isn't
published to PyPI or any conda channel, and pixi refuses a
`[tool.pixi.pypi-dependencies]` local-path override for a name that's already
in `[project.dependencies]` ("steps-widget is already a dependency"). Until
`steps-widget` has a release, develop/test against a plain venv instead:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ../steps-widget
pip install -e .
pip install pytest pytest-asyncio
pytest test/
```

Once `steps-widget` is published, `pixi install` needs no changes -- the
dependency is already declared correctly in `[project.dependencies]`.

- Run tests: `pytest test/` (`pixi run test`, once solvable).
- Try the game: `myiagi` (or `pixi run myiagi`, once solvable) -- `-w <week>`
  overrides the computed course week number, `-d <days>` shifts the "day
  delta" used for streak/date bookkeeping.
- Build docs: `pixi run api` (quartodoc API pages), then `pixi run docs`.
- Release: `pixi run bump` / `release` / `version` drive
  `scripts/bump_version.py` + a tag push, which triggers the conda/PyPI
  workflows.

## Distribution

Both `.github/workflows/conda-release.yml` and `pypi-release.yml` trigger on
version tag pushes (`vX.Y[.Z][.rcN]`), same pattern as `steps-widget`.

- **conda**: `conda-build/meta.yaml` derives its run requirements from
  `pyproject.toml`'s `[project.dependencies]` via Jinja, and lists
  `conda-forge` + `sepandhaghighi` + `munch-group` as recipe channels so
  `art` and `steps-widget` both resolve. **This recipe cannot build
  successfully until `steps-widget` has a conda release on the `munch-group`
  channel** -- same chicken-and-egg constraint as the pixi workspace above.
- **pip**: pure-Python universal wheel, published to PyPI. Blocked the same
  way until `steps-widget` is on PyPI.

## Testing approach

- `test_expressions.py`/`test_controls.py` test the pure generation/ramp
  logic without touching Textual at all.
- `test_scoring.py` tests `app.py`'s streak/effort/score-formatting functions
  by `monkeypatch`-ing the module-level `progress`/`course_week_nr` globals
  directly (they're plain module attributes, not instance state).
- `test_app_smoke.py` drives the real `STEPSApp` through `run_test()`:
  - the "full round" test calls `KeyLogger.key_up()`/`key_down()` directly
    (bypassing Textual's key-event dispatch) to deterministically sort the
    shuffled steps and check the scoring side effect -- an `autouse` fixture
    monkeypatches `progress`/`pickle_file_name` first so it never touches the
    real `~/.myiagi_progress.pkl`.
  - a separate test presses actual keys via `Pilot.press()` to confirm
    Textual's `key_<name>` auto-dispatch convention itself still holds (see
    "Textual version notes").
  - `app.screen.query_one(...)`, not `app.query_one(...)`, to reach the
    pushed `STEPS` screen (see "Textual version notes").
- `asyncio_mode = "auto"` (`pyproject.toml`'s `[tool.pytest.ini_options]`) so
  `async def test_...` functions run without needing an explicit
  `@pytest.mark.asyncio` on each one (kept anyway, for clarity).
