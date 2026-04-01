"""PawPal+ core domain model and scheduling logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal

Priority = Literal["low", "medium", "high"]
Frequency = Literal["daily", "weekly", "as-needed"]

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


@dataclass
class Task:
    """A single pet care activity with timing, priority, frequency, and completion state."""

    title: str
    duration_minutes: int
    priority: Priority = "medium"
    description: str = ""
    frequency: Frequency = "daily"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed so the scheduler will skip it."""
        self.completed = True

    def reset(self) -> None:
        """Reset completion status (e.g., at the start of a new day)."""
        self.completed = False

    def __str__(self) -> str:
        """Return a short human-readable summary of the task."""
        status = "✓" if self.completed else "○"
        return f"[{status}] {self.title} ({self.duration_minutes} min, {self.priority}, {self.frequency})"


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------


@dataclass
class Pet:
    """A pet with its own list of care tasks."""

    name: str
    species: str
    age_years: float = 0.0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove the first task whose title matches (case-insensitive)."""
        self.tasks = [t for t in self.tasks if t.title.lower() != title.lower()]

    def pending_tasks(self) -> list[Task]:
        """Return only tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.completed]

    def __str__(self) -> str:
        """Return a short description of the pet."""
        return f"{self.name} the {self.species} (age {self.age_years})"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------


@dataclass
class Owner:
    """A pet owner who manages one or more pets and has a daily time budget."""

    name: str
    available_minutes: int = 480
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Collect and return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_pending_tasks(self) -> list[Task]:
        """Return all incomplete tasks across all pets."""
        return [task for pet in self.pets for task in pet.pending_tasks()]

    def find_pet(self, name: str) -> Pet | None:
        """Look up a pet by name (case-insensitive); return None if not found."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def __str__(self) -> str:
        """Return the owner's name."""
        return self.name


# ---------------------------------------------------------------------------
# Plan output
# ---------------------------------------------------------------------------


@dataclass
class ScheduledTask:
    """A task placed at a specific time in the daily plan, with a reason."""

    task: Task
    pet: Pet
    start_time: datetime
    reason: str

    @property
    def end_time(self) -> datetime:
        """Compute the end time from start time plus task duration."""
        return self.start_time + timedelta(minutes=self.task.duration_minutes)

    def time_range(self) -> str:
        """Format the start–end window as a readable string."""
        fmt = "%I:%M %p"
        return f"{self.start_time.strftime(fmt)} – {self.end_time.strftime(fmt)}"

    def __str__(self) -> str:
        """Return a single-line summary of the scheduled task."""
        return f"{self.time_range()}  {self.task.title} ({self.pet.name})  — {self.task.priority} priority"


@dataclass
class DailyPlan:
    """The output of the Scheduler: an ordered list of tasks and a list of skipped tasks."""

    owner: Owner
    scheduled: list[ScheduledTask] = field(default_factory=list)
    skipped: list[tuple[Task, Pet, str]] = field(default_factory=list)

    @property
    def total_minutes(self) -> int:
        """Total minutes occupied by scheduled tasks."""
        return sum(st.task.duration_minutes for st in self.scheduled)

    def summary(self) -> str:
        """Return a formatted multi-line schedule suitable for terminal output."""
        lines = [
            f"=== Today's Schedule for {self.owner.name} ===",
            f"Total time: {self.total_minutes} / {self.owner.available_minutes} min",
            "",
        ]
        if self.scheduled:
            lines.append("SCHEDULED:")
            for st in self.scheduled:
                lines.append(f"  {st}")
        else:
            lines.append("  (no tasks scheduled)")

        if self.skipped:
            lines.append("")
            lines.append("SKIPPED:")
            for task, pet, reason in self.skipped:
                lines.append(f"  ✗ {task.title} ({pet.name}) — {reason}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------


class Scheduler:
    """Greedy priority-based daily scheduler that pulls tasks from all of an owner's pets."""

    def __init__(self, owner: Owner, start_hour: int = 8) -> None:
        """Initialise the scheduler with an owner and an optional day-start hour."""
        self.owner = owner
        self.start_hour = start_hour

    def build_plan(self) -> DailyPlan:
        """
        Build a DailyPlan from all pending tasks across the owner's pets.

        Steps:
        1. Ask the owner for every pending (incomplete) task via get_pending_tasks().
        2. Sort high → medium → low; shorter tasks first within each priority tier.
        3. Greedily assign tasks to time slots until available_minutes is exhausted.
        4. Attach a reason to every scheduled and skipped task.
        """
        plan = DailyPlan(owner=self.owner)
        remaining = self.owner.available_minutes
        current_time = datetime.today().replace(
            hour=self.start_hour, minute=0, second=0, microsecond=0
        )

        # Build a (task, pet) lookup so we can record which pet owns each task
        task_to_pet: dict[int, Pet] = {}
        for pet in self.owner.pets:
            for task in pet.pending_tasks():
                task_to_pet[id(task)] = pet

        pending = self.owner.get_pending_tasks()
        sorted_tasks = sorted(
            pending,
            key=lambda t: (_PRIORITY_ORDER[t.priority], t.duration_minutes),
        )

        for task in sorted_tasks:
            pet = task_to_pet[id(task)]
            if task.duration_minutes > remaining:
                reason = (
                    f"only {remaining} min left; needs {task.duration_minutes} min"
                )
                plan.skipped.append((task, pet, reason))
                continue

            reason = self._explain(task, remaining)
            plan.scheduled.append(
                ScheduledTask(task=task, pet=pet, start_time=current_time, reason=reason)
            )
            current_time += timedelta(minutes=task.duration_minutes)
            remaining -= task.duration_minutes

        return plan

    def _explain(self, task: Task, remaining: int) -> str:
        """Generate a human-readable reason for why a task was scheduled."""
        phrases = {
            "high": "High priority — scheduled first.",
            "medium": "Medium priority — fits the available window.",
            "low": "Low priority — included with remaining time.",
        }
        return f"{phrases[task.priority]} ({remaining} min left before this task)"
