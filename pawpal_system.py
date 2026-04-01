"""PawPal+ core domain model and scheduling logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal

Priority = Literal["low", "medium", "high"]

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Domain classes
# ---------------------------------------------------------------------------


@dataclass
class Owner:
    name: str
    available_minutes: int = 480  # 8-hour day by default

    def __str__(self) -> str:
        return self.name


@dataclass
class Pet:
    name: str
    species: str
    owner: Owner
    age_years: float = 0.0
    notes: str = ""

    def __str__(self) -> str:
        return f"{self.name} the {self.species}"


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority = "medium"
    description: str = ""

    def __str__(self) -> str:
        return f"{self.title} ({self.duration_minutes} min, {self.priority})"


# ---------------------------------------------------------------------------
# Plan output
# ---------------------------------------------------------------------------


@dataclass
class ScheduledTask:
    task: Task
    start_time: datetime
    reason: str

    @property
    def end_time(self) -> datetime:
        return self.start_time + timedelta(minutes=self.task.duration_minutes)

    def time_range(self) -> str:
        fmt = "%I:%M %p"
        return f"{self.start_time.strftime(fmt)} – {self.end_time.strftime(fmt)}"


@dataclass
class DailyPlan:
    owner: Owner
    pet: Pet
    scheduled: list[ScheduledTask] = field(default_factory=list)
    skipped: list[tuple[Task, str]] = field(default_factory=list)

    @property
    def total_minutes(self) -> int:
        return sum(st.task.duration_minutes for st in self.scheduled)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------


class Scheduler:
    """Greedy priority-based daily scheduler for pet care tasks."""

    def __init__(
        self,
        owner: Owner,
        pet: Pet,
        start_hour: int = 8,
    ) -> None:
        self.owner = owner
        self.pet = pet
        self.start_hour = start_hour

    def build_plan(self, tasks: list[Task]) -> DailyPlan:
        """
        Build a DailyPlan by selecting tasks in priority order until the
        owner's available time is exhausted.

        Rules:
        1. Sort tasks high → medium → low, then by duration (shorter first
           as a tiebreaker so we fit in more tasks).
        2. Skip tasks that would exceed remaining available time.
        3. Attach a human-readable reason to every decision.
        """
        plan = DailyPlan(owner=self.owner, pet=self.pet)
        remaining = self.owner.available_minutes
        current_time = datetime.today().replace(
            hour=self.start_hour, minute=0, second=0, microsecond=0
        )

        sorted_tasks = sorted(
            tasks,
            key=lambda t: (_PRIORITY_ORDER[t.priority], t.duration_minutes),
        )

        for task in sorted_tasks:
            if task.duration_minutes > remaining:
                reason = (
                    f"Skipped — only {remaining} min left, "
                    f"but '{task.title}' needs {task.duration_minutes} min."
                )
                plan.skipped.append((task, reason))
                continue

            reason = self._explain(task, remaining)
            plan.scheduled.append(ScheduledTask(task=task, start_time=current_time, reason=reason))
            current_time += timedelta(minutes=task.duration_minutes)
            remaining -= task.duration_minutes

        return plan

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _explain(self, task: Task, remaining: int) -> str:
        priority_phrases = {
            "high": "This is a high-priority task and should happen first.",
            "medium": "Medium priority — fits well in the available window.",
            "low": "Low priority, but there's enough time to include it.",
        }
        base = priority_phrases[task.priority]
        return (
            f"{base} Scheduled for {task.duration_minutes} min "
            f"({remaining} min remaining before this task)."
        )
