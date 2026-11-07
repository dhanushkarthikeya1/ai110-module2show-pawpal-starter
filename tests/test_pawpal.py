"""Behavior tests for PawPal+'s core model and scheduler."""
from datetime import date, time, timedelta
import unittest

from pawpal_system import Owner, Pet, Scheduler, Task


class PawPalTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 11, 7)
        self.owner = Owner("Jordan")
        self.mochi = Pet("Mochi", "dog")
        self.luna = Pet("Luna", "cat")
        self.owner.add_pet(self.mochi)
        self.owner.add_pet(self.luna)
        self.scheduler = Scheduler()

    def test_task_completion_changes_status(self):
        task = Task("Walk", 20, due_date=self.today)
        self.mochi.add_task(task)
        self.scheduler.mark_task_complete(self.mochi, task)
        self.assertTrue(task.completed)

    def test_pet_task_addition_increases_count(self):
        self.mochi.add_task(Task("Feeding", 10, due_date=self.today))
        self.assertEqual(len(self.mochi.tasks), 1)

    def test_sorting_orders_by_date_then_preferred_time(self):
        later = Task("Evening", 10, due_date=self.today, preferred_time=time(18))
        earlier = Task("Morning", 10, due_date=self.today, preferred_time=time(8))
        self.assertEqual(self.scheduler.sort_by_time([later, earlier]), [earlier, later])

    def test_filtering_by_pet_and_completion(self):
        open_task = Task("Walk", 20, due_date=self.today)
        done_task = Task("Food", 5, due_date=self.today, completed=True)
        self.mochi.add_task(open_task)
        self.mochi.add_task(done_task)
        self.luna.add_task(Task("Play", 15, due_date=self.today))
        result = self.scheduler.filter_tasks(self.owner, pet_name="mochi", completed=False)
        self.assertEqual([(pet.name, task.title) for pet, task in result], [("Mochi", "Walk")])

    def test_daily_recurrence_creates_next_occurrence(self):
        task = Task("Medication", 5, due_date=self.today, frequency="daily")
        self.mochi.add_task(task)
        next_task = self.scheduler.mark_task_complete(self.mochi, task)
        self.assertTrue(task.completed)
        self.assertEqual(next_task.due_date, self.today + timedelta(days=1))
        self.assertFalse(next_task.completed)
        self.assertEqual(len(self.mochi.tasks), 2)

    def test_weekly_recurrence_advances_one_week(self):
        task = Task("Grooming", 40, due_date=self.today, frequency="weekly")
        self.mochi.add_task(task)
        next_task = self.scheduler.mark_task_complete(self.mochi, task)
        self.assertEqual(next_task.due_date, self.today + timedelta(days=7))

    def test_conflict_detection_flags_overlapping_windows(self):
        self.mochi.add_task(Task("Walk", 30, due_date=self.today, preferred_time=time(8)))
        self.luna.add_task(Task("Medication", 10, due_date=self.today, preferred_time=time(8, 20)))
        warnings = self.scheduler.find_conflicts(self.owner.get_all_tasks())
        self.assertEqual(len(warnings), 1)
        self.assertIn("overlaps", warnings[0])

    def test_daily_plan_respects_budget_and_prioritizes_high_priority(self):
        low = Task("Brush", 30, "low", self.today, time(8))
        high = Task("Medicine", 20, "high", self.today, time(8))
        self.mochi.add_task(low)
        self.mochi.add_task(high)
        plan = self.scheduler.build_daily_plan(
            self.owner, self.today, start_time=time(8), available_minutes=25
        )
        self.assertEqual([entry.task.title for entry in plan.entries], ["Medicine"])
        self.assertEqual([task.title for _, task, _ in plan.skipped], ["Brush"])

    def test_owner_keyword_preference_breaks_priority_tie(self):
        self.owner.preferences = ["medicine"]
        walk = Task("Walk", 10, "high", self.today, time(8))
        medicine = Task("Medicine", 10, "high", self.today, time(9))
        self.mochi.add_task(walk)
        self.mochi.add_task(medicine)
        plan = self.scheduler.build_daily_plan(self.owner, self.today, start_time=time(8))
        self.assertEqual(plan.entries[0].task.title, "Medicine")

    def test_duplicate_pet_names_are_rejected(self):
        with self.assertRaises(ValueError):
            self.owner.add_pet(Pet("mochi", "cat"))


if __name__ == "__main__":
    unittest.main()
