# PawPal+ Project Reflection

> Review this AI-assisted draft and adjust any wording that does not match your own experience before submitting.

## 1. System Design

### a. Initial design

I modeled the app with four main classes. `Owner` manages pets and stores planning preferences. `Pet` owns its care tasks. `Task` stores a title, due date, preferred time, duration, priority, recurrence, and completion status. `Scheduler` gathers tasks from the owner, filters and orders them, checks preferred-time conflicts, and produces a daily plan. The UML diagram records these relationships in `diagrams/uml_final.mmd`.

### b. Design changes

The final design adds `DailyPlan` and `ScheduleEntry` result objects. This keeps the scheduling algorithm separate from how Streamlit displays the plan. The scheduler can return included tasks, skipped tasks, and warnings together, which makes its decisions easier to test and explain.

## 2. Scheduling Logic and Tradeoffs

### a. Constraints and priorities

The planner first limits candidates to incomplete tasks due on the selected date. It sorts by high, medium, then low priority, then uses the owner's optional task-title keywords, preferred time, duration, and title as tie-breakers. It starts at the owner's selected time and does not schedule past the available-minute limit. These rules give urgent tasks first access to limited time and keep results deterministic.

### b. Tradeoffs

This is a greedy planner, not a global optimizer. It may schedule a high-priority long task before several shorter medium-priority tasks even when another combination would fit more work. That tradeoff keeps the behavior predictable and explainable for this small project. The conflict detector warns about overlapping preferred-time windows, while the generated plan shifts tasks into sequential slots. It does not model travel time, task dependencies, or multiple people caring for pets.

## 3. AI Collaboration

### a. How I used AI

I used ChatGPT in this coding session to help translate the assignment requirements into the class structure, scheduling rules, Streamlit integration, and a test plan. The most useful questions focused on how the scheduler should collect tasks from the owner's pets and how to handle recurrence and time-budget limits.

### b. Judgment and verification

I kept the scheduling policy deliberately small and explicit: priority first, then owner keyword preferences, preferred time, duration, and title. During verification, an early test draft assumed the word “no” would be removed as a stop word and that C01 would rank ahead of C07 for the grocery query. I did not change the code just to satisfy those assumptions: “no” is not in the stop-word set, and the actual BM25 scores put C07 first. I corrected the test expectations after checking the implementation and running the suite. A more elaborate scoring or optimization approach would add complexity without evidence that it improves this small example. The tests verify the documented rules; they do not prove the planner is suitable for every real household.

## 4. Testing and Verification

### a. What I tested

The automated tests cover task status changes, adding and editing tasks, date/time sorting, filtering by pet and completion state, daily and weekly recurrence, overlapping preferred-time windows, priority under a time limit, owner keyword preferences, and duplicate pet names. These behaviors define the model's core promises and are likely places for regressions when the UI changes.

### b. Confidence

The test suite gives me reasonable confidence in the tested rules. I would next add tests for a task ending exactly at the time-budget boundary, a task preferred before the selected start time, tasks on different dates, and multiple overlapping tasks with different durations.

## 5. Reflection

### a. What went well

Separating the data model and scheduling rules from the Streamlit interface made the core behavior testable without launching a browser. Returning explicit scheduled, skipped, and conflict results also made the planner easier to explain in the UI.

### b. What I would improve

I would add persistent storage so pets and tasks remain after a session ends, and add a way to delete existing tasks. A later version could compare the current greedy policy with a different scheduling strategy using defined test scenarios.

### c. Key takeaway

AI can help produce a working structure quickly, but the developer still needs to choose understandable rules and verify the implementation against concrete cases. Here, the important design decision was to make the scheduling policy visible and testable instead of hiding it inside the interface.
