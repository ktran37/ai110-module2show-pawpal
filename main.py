"""Demo script — run with: python main.py"""

from datetime import datetime, timedelta, date
from tabulate import tabulate
from pawpal_system import DailyPlan, Owner, Pet, ScheduledTask, Scheduler, Task

# ---------------------------------------------------------------------------
# Setup: owner with two pets and tasks added out of order
# ---------------------------------------------------------------------------

owner = Owner(name="Jordan", available_minutes=90)

mochi = Pet(name="Mochi", species="dog", age_years=3)
mochi.add_task(Task("Brushing",     duration_minutes=15, priority="low",    frequency="weekly"))
mochi.add_task(Task("Morning walk", duration_minutes=30, priority="high",   frequency="daily"))
mochi.add_task(Task("Fetch / play", duration_minutes=20, priority="medium", frequency="daily"))
mochi.add_task(Task("Breakfast",    duration_minutes=10, priority="high",   frequency="daily"))

noodle = Pet(name="Noodle", species="cat", age_years=5)
noodle.add_task(Task("Interactive play", duration_minutes=15, priority="medium", frequency="daily"))
noodle.add_task(Task("Litter box",       duration_minutes=5,  priority="high",   frequency="daily"))
# Make Feeding overdue to show urgency weighting
noodle.add_task(Task("Feeding", duration_minutes=5, priority="medium", frequency="daily",
                     due_date=date.today() - timedelta(days=1)))

owner.add_pet(mochi)
owner.add_pet(noodle)

scheduler = Scheduler(owner=owner, start_hour=8)

# ---------------------------------------------------------------------------
# 1. Standard priority plan
# ---------------------------------------------------------------------------
print("=" * 60)
print("1. STANDARD PRIORITY PLAN")
print("=" * 60)
plan = scheduler.build_plan()
print(plan.summary())

# ---------------------------------------------------------------------------
# 2. Sorting — tabulate formatted
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("2. ALL TASKS SORTED BY DURATION (tabulate)")
print("=" * 60)
sorted_tasks = scheduler.sort_by_time(owner.get_all_tasks())
rows = [
    [t.title, t.duration_minutes, t.priority, t.frequency, str(t.due_date), "✓" if t.completed else "○"]
    for t in sorted_tasks
]
print(tabulate(rows, headers=["Task", "Min", "Priority", "Freq", "Due", "Done"], tablefmt="rounded_outline"))

# ---------------------------------------------------------------------------
# 3. Filtering — pending tasks for Mochi
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("3. FILTERING: pending tasks for Mochi")
print("=" * 60)
mochi_tasks = scheduler.filter_tasks(pet_name="Mochi", completed=False)
rows = [[t.title, t.duration_minutes, t.priority, str(t.due_date)] for t, _ in mochi_tasks]
print(tabulate(rows, headers=["Task", "Min", "Priority", "Due"], tablefmt="rounded_outline"))

# ---------------------------------------------------------------------------
# 4. Weighted urgency plan (Challenge 1)
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("4. WEIGHTED URGENCY PLAN (priority × due-date proximity)")
print("=" * 60)
print("Note: Noodle's 'Feeding' is OVERDUE → urgency score boosts it above")
print("      higher-priority tasks with distant due dates.\n")
weighted_plan = scheduler.build_weighted_plan()

rows = []
for st in weighted_plan.scheduled:
    score = f"{st.task.urgency_score():.2f}"
    rows.append([st.time_range(), st.task.title, st.pet.name, st.task.priority, str(st.task.due_date), score])
print(tabulate(rows, headers=["Time", "Task", "Pet", "Priority", "Due", "Score"], tablefmt="rounded_outline"))

if weighted_plan.skipped:
    print("\nSkipped:")
    for task, pet, reason in weighted_plan.skipped:
        print(f"  ✗ {task.title} ({pet.name}) — {reason}")

# ---------------------------------------------------------------------------
# 5. Recurring task rollover
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("5. RECURRING TASKS: rollover after completion")
print("=" * 60)
for st in plan.scheduled:
    st.task.mark_complete()

new_tasks = scheduler.advance_recurring_tasks()
rows = [[t.title, t.frequency, str(t.due_date)] for t in new_tasks]
print(tabulate(rows, headers=["Task", "Frequency", "Next Due"], tablefmt="rounded_outline"))

# ---------------------------------------------------------------------------
# 6. Conflict detection
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("6. CONFLICT DETECTION")
print("=" * 60)
conflict_owner = Owner("Test", available_minutes=60)
pet_a = Pet("Rex", "dog")
conflict_owner.add_pet(pet_a)
t1, t2 = Task("Walk", 30, "high"), Task("Groom", 20, "medium")
now = datetime.today().replace(hour=9, minute=0, second=0, microsecond=0)
conflict_plan = DailyPlan(owner=conflict_owner)
conflict_plan.scheduled.append(ScheduledTask(task=t1, pet=pet_a, start_time=now, reason="demo"))
conflict_plan.scheduled.append(ScheduledTask(task=t2, pet=pet_a, start_time=now, reason="demo"))
for w in Scheduler(conflict_owner).detect_conflicts(conflict_plan):
    print(f"  {w}")

# ---------------------------------------------------------------------------
# 7. JSON persistence (Challenge 2)
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("7. JSON PERSISTENCE: save → reload → verify")
print("=" * 60)
owner.save_to_json("data.json")
print("  Saved to data.json")

reloaded = Owner.load_from_json("data.json")
print(f"  Reloaded owner: {reloaded.name}, {len(reloaded.pets)} pets, "
      f"{sum(len(p.tasks) for p in reloaded.pets)} tasks")
assert reloaded.name == owner.name
assert len(reloaded.pets) == len(owner.pets)
print("  ✓ Round-trip verified")
