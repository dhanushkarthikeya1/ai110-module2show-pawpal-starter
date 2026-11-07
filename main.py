"""CLI demonstration of PawPal+'s daily scheduler."""
from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    today = date.today()
    owner = Owner("Jordan", preferences=["morning"])
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Morning walk", 30, "high", today, time(8, 0), "daily"))
    mochi.add_task(Task("Medication", 10, "high", today, time(8, 15), "daily"))
    luna.add_task(Task("Breakfast", 10, "medium", today, time(8, 30), "daily"))

    scheduler = Scheduler()
    plan = scheduler.build_daily_plan(owner, today, start_time=time(8, 0), available_minutes=120)
    print(f"PawPal+ schedule for {today.isoformat()} | {owner.name}")
    for entry in plan.entries:
        print(
            f"{entry.start:%H:%M}-{entry.end:%H:%M}  {entry.pet_name}: {entry.task.title} "
            f"({entry.task.duration_minutes} min, {entry.task.priority} priority)"
        )
    if plan.conflicts:
        print("\nConflict warnings:")
        for warning in plan.conflicts:
            print(f"- {warning}")
    if plan.skipped:
        print("\nNot scheduled:")
        for pet_name, task, reason in plan.skipped:
            print(f"- {pet_name}: {task.title} — {reason}")


if __name__ == "__main__":
    main()
