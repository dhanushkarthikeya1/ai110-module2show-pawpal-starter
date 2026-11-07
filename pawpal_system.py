"""Core data model and deterministic scheduling logic for PawPal+."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Iterable, Optional


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = {"once", "daily", "weekly"}


@dataclass
class Task:
    """A dated care activity for one pet."""

    title: str
    duration_minutes: int
    priority: str = "medium"
    due_date: date = field(default_factory=date.today)
    preferred_time: time = field(default_factory=lambda: time(9, 0))
    frequency: str = "once"
    completed: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Task title cannot be empty.")
        if self.duration_minutes <= 0:
            raise ValueError("Task duration must be greater than zero.")
        self.priority = self.priority.lower()
        self.frequency = self.frequency.lower()
        if self.priority not in PRIORITY_ORDER:
            raise ValueError("Priority must be low, medium, or high.")
        if self.frequency not in FREQUENCIES:
            raise ValueError("Frequency must be once, daily, or weekly.")

    def mark_complete(self) -> None:
        """Mark this occurrence complete."""
        self.completed = True


@dataclass
class Pet:
    """A pet and the care tasks assigned to it."""

    name: str
    species: str = "other"
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Pet name cannot be empty.")

    def add_task(self, task: Task) -> None:
        """Add a task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task if it belongs to this pet."""
        self.tasks.remove(task)

    def update_task(self, task: Task, replacement: Task) -> None:
        """Replace one of this pet's tasks with an edited task."""
        for index, existing in enumerate(self.tasks):
            if existing is task:
                self.tasks[index] = replacement
                return
        raise ValueError("The task does not belong to this pet.")


@dataclass
class Owner:
    """An owner who manages one or more pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    preferences: list[str] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet, rejecting duplicate names without regard to case."""
        if any(existing.name.casefold() == pet.name.casefold() for existing in self.pets):
            raise ValueError(f"A pet named {pet.name!r} is already registered.")
        self.pets.append(pet)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every pet/task pair owned by this owner."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass(frozen=True)
class ScheduleEntry:
    """A task placed into a generated daily plan."""

    pet_name: str
    task: Task
    start: time
    end: time
    reason: str


@dataclass
class DailyPlan:
    """Scheduled tasks, tasks that did not fit, and warnings."""

    plan_date: date
    entries: list[ScheduleEntry]
    skipped: list[tuple[str, Task, str]]
    conflicts: list[str]


class Scheduler:
    """Organize tasks using priority, preferred time, and a time budget."""

    def sort_by_time(self, tasks: Iterable[Task]) -> list[Task]:
        """Sort tasks by due date and preferred start time."""
        return sorted(tasks, key=lambda task: (task.due_date, task.preferred_time, task.title.casefold()))

    @staticmethod
    def _preference_rank(owner: Owner, task: Task) -> int:
        """Return the index of the first owner keyword found in a task title."""
        title = task.title.casefold()
        return next(
            (index for index, keyword in enumerate(owner.preferences) if keyword.casefold() in title),
            len(owner.preferences),
        )

    def filter_tasks(
        self,
        owner: Owner,
        *,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        due_date: Optional[date] = None,
    ) -> list[tuple[Pet, Task]]:
        """Filter an owner's tasks by pet, completion state, or date."""
        wanted_pet = pet_name.casefold() if pet_name else None
        return [
            (pet, task)
            for pet, task in owner.get_all_tasks()
            if (wanted_pet is None or pet.name.casefold() == wanted_pet)
            and (completed is None or task.completed is completed)
            and (due_date is None or task.due_date == due_date)
        ]

    def find_conflicts(self, tasks: Iterable[tuple[Pet, Task]]) -> list[str]:
        """Report overlapping preferred-time windows across an owner's pets."""
        rows = list(tasks)
        warnings: list[str] = []
        for i, (pet_a, task_a) in enumerate(rows):
            start_a = datetime.combine(task_a.due_date, task_a.preferred_time)
            end_a = start_a + timedelta(minutes=task_a.duration_minutes)
            for pet_b, task_b in rows[i + 1 :]:
                if task_a.due_date != task_b.due_date:
                    continue
                start_b = datetime.combine(task_b.due_date, task_b.preferred_time)
                end_b = start_b + timedelta(minutes=task_b.duration_minutes)
                if start_a < end_b and start_b < end_a:
                    warnings.append(
                        f"{task_a.title} ({pet_a.name}) overlaps {task_b.title} ({pet_b.name}) "
                        f"in the preferred-time window."
                    )
        return warnings

    def mark_task_complete(self, pet: Pet, task: Task) -> Optional[Task]:
        """Complete a task and add its next daily or weekly occurrence."""
        if task not in pet.tasks:
            raise ValueError("The task does not belong to this pet.")
        task.mark_complete()
        if task.frequency == "once":
            return None
        next_date = task.due_date + timedelta(days=1 if task.frequency == "daily" else 7)
        next_task = Task(
            title=task.title,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            due_date=next_date,
            preferred_time=task.preferred_time,
            frequency=task.frequency,
            notes=task.notes,
        )
        pet.add_task(next_task)
        return next_task

    def build_daily_plan(
        self,
        owner: Owner,
        plan_date: date,
        *,
        start_time: time = time(8, 0),
        available_minutes: int = 480,
    ) -> DailyPlan:
        """Build a priority-first plan while respecting the owner's time budget."""
        if available_minutes < 0:
            raise ValueError("Available minutes cannot be negative.")
        all_for_date = [
            (pet, task)
            for pet, task in owner.get_all_tasks()
            if task.due_date == plan_date and not task.completed
        ]
        warnings = self.find_conflicts(all_for_date)
        ordered = sorted(
            all_for_date,
            key=lambda pair: (
                PRIORITY_ORDER[pair[1].priority],
                self._preference_rank(owner, pair[1]),
                pair[1].preferred_time,
                pair[1].duration_minutes,
                pair[1].title.casefold(),
            ),
        )
        window_end = datetime.combine(plan_date, start_time) + timedelta(minutes=available_minutes)
        cursor = datetime.combine(plan_date, start_time)
        entries: list[ScheduleEntry] = []
        skipped: list[tuple[str, Task, str]] = []
        for pet, task in ordered:
            desired = datetime.combine(plan_date, task.preferred_time)
            scheduled_start = max(cursor, desired)
            scheduled_end = scheduled_start + timedelta(minutes=task.duration_minutes)
            if scheduled_end > window_end:
                skipped.append((pet.name, task, "Does not fit in the remaining time."))
                continue
            entries.append(
                ScheduleEntry(
                    pet_name=pet.name,
                    task=task,
                    start=scheduled_start.time(),
                    end=scheduled_end.time(),
                    reason=f"{task.priority.title()} priority; placed at or after its preferred time.",
                )
            )
            cursor = scheduled_end
        return DailyPlan(plan_date, entries, skipped, warnings)
