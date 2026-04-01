# PawPal+ UML Class Diagram

```mermaid
classDiagram
    class Owner {
        +str name
        +int available_minutes
        +__str__() str
    }

    class Pet {
        +str name
        +str species
        +float age_years
        +str notes
        +__str__() str
    }

    class Task {
        +str title
        +int duration_minutes
        +Priority priority
        +str description
        +__str__() str
    }

    class ScheduledTask {
        +Task task
        +datetime start_time
        +str reason
        +end_time() datetime
        +time_range() str
    }

    class DailyPlan {
        +Owner owner
        +Pet pet
        +list~ScheduledTask~ scheduled
        +list~tuple~ skipped
        +total_minutes() int
    }

    class Scheduler {
        +Owner owner
        +Pet pet
        +int start_hour
        +build_plan(tasks: list~Task~) DailyPlan
        -_explain(task: Task, remaining: int) str
    }

    Owner "1" --> "0..*" Pet : owns
    Pet --> Owner : owner
    Scheduler --> Owner : uses
    Scheduler --> Pet : uses
    Scheduler --> DailyPlan : creates
    DailyPlan --> Owner : references
    DailyPlan --> Pet : references
    DailyPlan "1" *-- "0..*" ScheduledTask : scheduled
    ScheduledTask --> Task : wraps
```

## Relationships

| Relationship | Type | Description |
|---|---|---|
| `Owner` → `Pet` | Association (1 to many) | An owner can have multiple pets |
| `Pet` → `Owner` | Association | Each pet belongs to one owner |
| `Scheduler` → `Owner` / `Pet` | Dependency | Scheduler uses these to build the plan |
| `Scheduler` → `DailyPlan` | Creation | `build_plan()` instantiates and returns a DailyPlan |
| `DailyPlan` ◆ `ScheduledTask` | Composition | ScheduledTasks only exist within a DailyPlan |
| `ScheduledTask` → `Task` | Association | Wraps a Task with a time slot and reason |
