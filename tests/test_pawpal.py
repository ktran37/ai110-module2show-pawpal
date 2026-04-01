"""Tests for PawPal+ core logic."""

import pytest
from pawpal_system import DailyPlan, Owner, Pet, Scheduler, Task


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def basic_owner():
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    return owner


@pytest.fixture
def basic_pet():
    return Pet(name="Mochi", species="dog")


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------


def test_mark_complete_changes_status():
    """Calling mark_complete() should set completed to True."""
    task = Task("Morning walk", duration_minutes=20)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_mark_complete_excludes_task_from_schedule(basic_owner):
    """A completed task should not appear in the generated plan."""
    pet = basic_owner.pets[0]
    task = Task("Walk", duration_minutes=20, priority="high")
    pet.add_task(task)
    task.mark_complete()

    plan = Scheduler(basic_owner).build_plan()
    scheduled_titles = [st.task.title for st in plan.scheduled]
    assert "Walk" not in scheduled_titles


def test_reset_restores_pending_status():
    """reset() should allow a completed task to be scheduled again."""
    task = Task("Walk", duration_minutes=20)
    task.mark_complete()
    task.reset()
    assert task.completed is False


# ---------------------------------------------------------------------------
# Pet / task-addition tests
# ---------------------------------------------------------------------------


def test_add_task_increases_pet_task_count(basic_pet):
    """Adding a task to a Pet should increase its task list length by 1."""
    before = len(basic_pet.tasks)
    basic_pet.add_task(Task("Feeding", duration_minutes=5))
    assert len(basic_pet.tasks) == before + 1


def test_add_multiple_tasks_all_appear(basic_pet):
    """All added tasks should be present on the pet."""
    titles = ["Walk", "Feed", "Play", "Groom"]
    for t in titles:
        basic_pet.add_task(Task(t, duration_minutes=10))
    stored = [t.title for t in basic_pet.tasks]
    assert stored == titles


def test_remove_task_decreases_count(basic_pet):
    """remove_task() should drop the matching task from the pet's list."""
    basic_pet.add_task(Task("Walk", duration_minutes=20))
    basic_pet.add_task(Task("Feed", duration_minutes=5))
    basic_pet.remove_task("Walk")
    assert len(basic_pet.tasks) == 1
    assert basic_pet.tasks[0].title == "Feed"


def test_pending_tasks_excludes_completed(basic_pet):
    """pending_tasks() should return only incomplete tasks."""
    t1 = Task("Walk", duration_minutes=20)
    t2 = Task("Feed", duration_minutes=5)
    t2.mark_complete()
    basic_pet.add_task(t1)
    basic_pet.add_task(t2)
    assert basic_pet.pending_tasks() == [t1]


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------


def test_owner_add_pet_increases_count():
    """add_pet() should register the pet under the owner."""
    owner = Owner(name="Jordan")
    assert len(owner.pets) == 0
    owner.add_pet(Pet("Mochi", "dog"))
    assert len(owner.pets) == 1


def test_owner_get_all_tasks_aggregates_across_pets():
    """get_all_tasks() should return tasks from every pet."""
    owner = Owner(name="Jordan")
    p1 = Pet("Mochi", "dog")
    p2 = Pet("Noodle", "cat")
    p1.add_task(Task("Walk", duration_minutes=20))
    p2.add_task(Task("Feed", duration_minutes=5))
    p2.add_task(Task("Play", duration_minutes=10))
    owner.add_pet(p1)
    owner.add_pet(p2)
    assert len(owner.get_all_tasks()) == 3


def test_owner_get_pending_tasks_skips_completed():
    """get_pending_tasks() should exclude completed tasks from all pets."""
    owner = Owner(name="Jordan")
    pet = Pet("Mochi", "dog")
    t1 = Task("Walk", duration_minutes=20)
    t2 = Task("Feed", duration_minutes=5)
    t2.mark_complete()
    pet.add_task(t1)
    pet.add_task(t2)
    owner.add_pet(pet)
    assert owner.get_pending_tasks() == [t1]


def test_owner_find_pet_returns_correct_pet():
    """find_pet() should return the right Pet by name."""
    owner = Owner(name="Jordan")
    owner.add_pet(Pet("Mochi", "dog"))
    owner.add_pet(Pet("Noodle", "cat"))
    found = owner.find_pet("noodle")  # case-insensitive
    assert found is not None
    assert found.name == "Noodle"


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------


def test_scheduler_builds_plan_from_owner_pets():
    """Scheduler should pull tasks from the owner's pets automatically."""
    owner = Owner(name="Jordan", available_minutes=60)
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk", duration_minutes=20, priority="high"))
    pet.add_task(Task("Feed", duration_minutes=10, priority="high"))
    owner.add_pet(pet)

    plan = Scheduler(owner).build_plan()
    assert len(plan.scheduled) == 2
    assert plan.total_minutes == 30


def test_scheduler_respects_time_budget():
    """Total scheduled minutes must not exceed owner's available_minutes."""
    owner = Owner(name="Jordan", available_minutes=30)
    pet = Pet("Mochi", "dog")
    for i in range(5):
        pet.add_task(Task(f"Task {i}", duration_minutes=15, priority="medium"))
    owner.add_pet(pet)

    plan = Scheduler(owner).build_plan()
    assert plan.total_minutes <= 30


def test_scheduler_high_priority_first():
    """High-priority tasks should be scheduled before lower-priority ones."""
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Low task",    duration_minutes=10, priority="low"))
    pet.add_task(Task("High task",   duration_minutes=10, priority="high"))
    pet.add_task(Task("Medium task", duration_minutes=10, priority="medium"))
    owner.add_pet(pet)

    plan = Scheduler(owner).build_plan()
    titles = [st.task.title for st in plan.scheduled]
    assert titles.index("High task") < titles.index("Medium task")
    assert titles.index("Medium task") < titles.index("Low task")


def test_scheduler_skips_completed_tasks():
    """Completed tasks should not appear in the scheduled list."""
    owner = Owner(name="Jordan", available_minutes=60)
    pet = Pet("Mochi", "dog")
    done = Task("Old task", duration_minutes=10, priority="high")
    done.mark_complete()
    pet.add_task(done)
    pet.add_task(Task("New task", duration_minutes=10, priority="medium"))
    owner.add_pet(pet)

    plan = Scheduler(owner).build_plan()
    titles = [st.task.title for st in plan.scheduled]
    assert "Old task" not in titles
    assert "New task" in titles
