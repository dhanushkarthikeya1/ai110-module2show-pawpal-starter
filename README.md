# PawPal+

PawPal+ is a small Streamlit pet-care planner. It models an owner, pets, and dated care tasks, then creates a daily plan that sorts by priority, respects a time budget, flags overlapping preferred-time windows, and explains why each task was placed or skipped. It is a learning project, not a veterinary or emergency-care tool.

## Features

- Add multiple pets and care tasks with duration, priority, preferred time, due date, and recurrence.
- Generate a daily plan for a selected start time and available number of minutes.
- Schedule higher-priority tasks first, then apply owner keywords, preferred time, duration, and title as tie-breakers.
- Let the owner favor task-title keywords when tasks have the same priority.
- Warn about overlapping preferred-time windows across pets.
- Filter tasks by pet, completion state, and due date.
- Completing a daily or weekly recurring task creates its next occurrence.
- Keep the owner and pets in Streamlit session state while the app is open.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Run the terminal demo with `python main.py`.

## Demo walkthrough

1. Enter an owner name, then add one or more pets.
2. Select a pet and add a task with its date, preferred time, duration, priority, and recurrence.
3. Add more tasks, including tasks for a second pet if desired.
4. Choose the day, schedule start, and available minutes, then select **Generate daily plan**.
5. Review the sorted schedule, each task's reason, skipped tasks, and any overlapping preferred-time warnings. Use the task table to review completion status.

### Sample CLI output

```text
PawPal+ schedule for 2026-11-07 | Jordan
08:00-08:30  Mochi: Morning walk (30 min, high priority)
08:30-08:40  Mochi: Medication (10 min, high priority)
08:40-08:50  Luna: Breakfast (10 min, medium priority)

Conflict warnings:
- Morning walk (Mochi) overlaps Medication (Mochi) in the preferred-time window.
```

The date in this example is illustrative; the CLI uses the current date.

## Smarter scheduling

| Feature | Method | Behavior |
|---|---|---|
| Sort by time | `Scheduler.sort_by_time()` | Orders by due date, preferred time, then title. |
| Filter tasks | `Scheduler.filter_tasks()` | Filters by pet name, completion state, and due date. |
| Priority, preferences, and time budget | `Scheduler.build_daily_plan()` | Plans high-priority tasks first, favors matching owner keywords within a priority, and skips tasks that exceed the available window. |
| Conflict detection | `Scheduler.find_conflicts()` | Warns when preferred-time intervals overlap on the same date, including across pets. |
| Recurrence | `Scheduler.mark_task_complete()` | Creates the next daily or weekly occurrence when a recurring task is completed. |

The planner uses a simple greedy rule: priority comes first, then owner keyword preferences, preferred time, shorter duration, and title. It does not optimize the whole day globally, reserve travel time, or interpret task dependencies. Conflict warnings compare preferred-time windows; the generated plan itself moves tasks into non-overlapping sequential slots.

## Tests

```bash
python -m pytest
```

The suite covers task completion and addition, sorting and filtering, daily and weekly recurrence, conflict warnings, time-budget behavior, and duplicate pet names. The tests use `unittest.TestCase`, so they can also run without pytest using `python -m unittest discover -s tests -v`.

Latest local test run:

```text
$ python -m pytest
.........                                                                [100%]
10 passed in 0.02s
```

## Project structure

- `pawpal_system.py` — data classes and scheduling logic.
- `app.py` — Streamlit interface backed by the model and scheduler.
- `main.py` — terminal demonstration.
- `tests/test_pawpal.py` — automated behavior tests.
- `diagrams/uml_final.mmd` — final class diagram source.
- `reflection.md` — project design and AI collaboration reflection.

## Design

The UML source is in [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd). `Owner` manages `Pet` objects; each `Pet` stores its `Task` objects. `Scheduler` reads the owner's tasks and returns a `DailyPlan` containing scheduled entries, skipped tasks, and conflict warnings.
