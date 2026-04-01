"""Demo script — run with: python main.py"""

from pawpal_system import Owner, Pet, Scheduler, Task

# ---------------------------------------------------------------------------
# Build the data
# ---------------------------------------------------------------------------

owner = Owner(name="Jordan", available_minutes=90)

# Pet 1: Mochi the dog
mochi = Pet(name="Mochi", species="dog", age_years=3)
mochi.add_task(Task("Morning walk",     duration_minutes=30, priority="high",   frequency="daily"))
mochi.add_task(Task("Breakfast",        duration_minutes=10, priority="high",   frequency="daily"))
mochi.add_task(Task("Fetch / play",     duration_minutes=20, priority="medium", frequency="daily"))
mochi.add_task(Task("Brushing",         duration_minutes=15, priority="low",    frequency="weekly"))

# Pet 2: Noodle the cat
noodle = Pet(name="Noodle", species="cat", age_years=5)
noodle.add_task(Task("Feeding",         duration_minutes=5,  priority="high",   frequency="daily"))
noodle.add_task(Task("Litter box",      duration_minutes=5,  priority="high",   frequency="daily"))
noodle.add_task(Task("Interactive play",duration_minutes=15, priority="medium", frequency="daily",
                     description="Wand toy or laser pointer"))

owner.add_pet(mochi)
owner.add_pet(noodle)

# ---------------------------------------------------------------------------
# Run the scheduler and print the plan
# ---------------------------------------------------------------------------

scheduler = Scheduler(owner=owner, start_hour=8)
plan = scheduler.build_plan()

print(plan.summary())
