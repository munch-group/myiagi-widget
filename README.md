
# myiagi-widget

Terminal trainer game ("Wax On - Wax Off" / "STEPS OF DOOM") where the student
reorders the shuffled evaluation steps of a randomly generated Python
expression back into the correct order, with persistent per-course-week
scoring.

```bash
myiagi
```

- Digit keys select a step by its line number; arrow keys move the selected
  step up/down.
- `-w <week>` overrides the computed course week number; `-d <days>` shifts
  the "day delta" used for streak/date bookkeeping.
- Progress is saved to `~/.myiagi_progress.pkl` (scores, per-week highscores,
  streaks).

Built on [steps_widget](https://github.com/munch-group/steps-widget)'s
expression stepper (`steps_widget.steps._steps`) and
[textual](https://textual.textualize.io). Requires **Python 3.10 through
3.13** -- same floor/ceiling as `steps-widget`, whose stepper this package
depends on.

```bash
pip install myiagi-widget
# or
conda install -c munch-group myiagi-widget
```

See the [docs](https://munch-group.org/myiagi-widget) for more.

## Initial set up

```bash
pixi run init
```

## Get updates to upstream fork

Add upstream if not already added

```bash
git remote add upstream https://github.com/munch-group/myiagi-widget.git
```

Fetch upstream changes

```bash
git fetch upstream
```

Either rebase your changes on top of upstream (cleaner history)

```bash
git rebase upstream/main
```

Or, merge upstream into your fork (preserves history)

```bash
git merge upstream/main
```

If you want to see what's changed upstream before applying:

```bash
git log HEAD..upstream/main
```

See the actual diff

```bash
git diff HEAD...upstream/main
```

Then push your updated fork:

```bash
git push origin main
```

If you rebased and need to force push
    
```bash
git push origin main --force-with-lease
```
