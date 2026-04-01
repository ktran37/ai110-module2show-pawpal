"""Tests for PawPal+ scheduling logic."""

import pytest
from pawpal_system import DailyPlan, Owner, Pet, Scheduler, Task


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def owner():
    return Owner(name="Jordan", available_minutes=60)


@pytest.fixture
def pet(owner):
    return Pet(name="Mochi", species="dog", owner=owner)


@pytest.fixture
def scheduler(owner, pet):
    return Scheduler(owner=owner, pet=pet, start_hour=8)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_high_priority_scheduled_first(scheduler):
    tasks = [
        Task("Low task", 10, "low"),
        Task("High task", 10, "high"),
        Task("Medium task", 10, "medium"),
    ]
    plan = scheduler.build_plan(tasks)
    titles = [st.task.title for st in plan.scheduled]
    assert titles.index("High task") < titles.index("Medium task")
    assert titles.index("Medium task") < titles.index("Low task")


def test_tasks_exceeding_time_are_skipped(scheduler):
    tasks = [
        Task("Long task", 50, "high"),
        Task("Another long task", 50, "medium"),  # won't fit after first
    ]
    plan = scheduler.build_plan(tasks)
    assert len(plan.scheduled) == 1
    assert len(plan.skipped) == 1
    assert plan.skipped[0][0].title == "Another long task"


def test_total_minutes_does_not_exceed_available(scheduler):
    tasks = [Task(f"Task {i}", 20, "medium") for i in range(5)]
    plan = scheduler.build_plan(tasks)
    assert plan.total_minutes <= scheduler.owner.available_minutes


def test_empty_task_list_produces_empty_plan(scheduler):
    plan = scheduler.build_plan([])
    assert plan.scheduled == []
    assert plan.skipped == []


def test_single_task_fits_exactly(scheduler):
    tasks = [Task("Full walk", 60, "high")]
    plan = scheduler.build_plan(tasks)
    assert len(plan.scheduled) == 1
    assert plan.total_minutes == 60


def test_scheduled_task_time_slots_are_sequential(scheduler):
    tasks = [
        Task("Feed", 10, "high"),
        Task("Walk", 20, "medium"),
        Task("Play", 15, "low"),
    ]
    plan = scheduler.build_plan(tasks)
    for i in range(1, len(plan.scheduled)):
        prev = plan.scheduled[i - 1]
        curr = plan.scheduled[i]
        assert curr.start_time == prev.end_time


def test_skip_reason_is_informative(scheduler):
    tasks = [Task("Quick task", 55, "high"), Task("Another", 20, "low")]
    plan = scheduler.build_plan(tasks)
    assert len(plan.skipped) == 1
    _, reason = plan.skipped[0]
    assert "Skipped" in reason


def test_plan_owner_and_pet_are_correct(scheduler, owner, pet):
    plan = scheduler.build_plan([])
    assert plan.owner is owner
    assert plan.pet is pet
