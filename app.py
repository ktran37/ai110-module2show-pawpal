import streamlit as st
from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Pet care planning assistant")

# ---------------------------------------------------------------------------
# Owner & Pet info
# ---------------------------------------------------------------------------
st.subheader("Owner & Pet")
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    available_minutes = st.number_input(
        "Time available today (minutes)", min_value=10, max_value=1440, value=120, step=10
    )
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    pet_age = st.number_input("Pet age (years)", min_value=0.0, max_value=30.0, value=2.0, step=0.5)

start_hour = st.slider("Day starts at (hour)", min_value=5, max_value=12, value=8)

st.divider()

# ---------------------------------------------------------------------------
# Task management
# ---------------------------------------------------------------------------
st.subheader("Tasks")

if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {"title": "Morning walk", "duration_minutes": 30, "priority": "high"},
        {"title": "Feeding", "duration_minutes": 10, "priority": "high"},
        {"title": "Playtime", "duration_minutes": 20, "priority": "medium"},
        {"title": "Grooming", "duration_minutes": 15, "priority": "low"},
    ]

with st.expander("Add a task", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        new_title = st.text_input("Task title", value="New task")
    with c2:
        new_duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=15)
    with c3:
        new_priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)

    if st.button("Add task"):
        st.session_state.tasks.append(
            {"title": new_title, "duration_minutes": int(new_duration), "priority": new_priority}
        )
        st.rerun()

if st.session_state.tasks:
    st.write("Current tasks:")
    # Show tasks with remove buttons
    for i, t in enumerate(st.session_state.tasks):
        cols = st.columns([3, 2, 2, 1])
        cols[0].write(t["title"])
        cols[1].write(f"{t['duration_minutes']} min")
        cols[2].write(t["priority"])
        if cols[3].button("✕", key=f"remove_{i}"):
            st.session_state.tasks.pop(i)
            st.rerun()
else:
    st.info("No tasks yet — add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Generate schedule
# ---------------------------------------------------------------------------
st.subheader("Generate Schedule")

if st.button("Build daily plan", type="primary"):
    if not st.session_state.tasks:
        st.warning("Add at least one task before generating a plan.")
    else:
        owner = Owner(name=owner_name, available_minutes=int(available_minutes))
        pet = Pet(name=pet_name, species=species, owner=owner, age_years=pet_age)
        tasks = [
            Task(
                title=t["title"],
                duration_minutes=t["duration_minutes"],
                priority=t["priority"],
            )
            for t in st.session_state.tasks
        ]
        scheduler = Scheduler(owner=owner, pet=pet, start_hour=start_hour)
        plan = scheduler.build_plan(tasks)

        st.success(
            f"Plan for **{pet.name}** — {plan.total_minutes} min scheduled "
            f"out of {owner.available_minutes} min available."
        )

        st.markdown("### Scheduled Tasks")
        for st_task in plan.scheduled:
            with st.container(border=True):
                c1, c2 = st.columns([2, 3])
                c1.markdown(f"**{st_task.task.title}**")
                c1.caption(st_task.time_range())
                c2.caption(st_task.reason)

        if plan.skipped:
            st.markdown("### Skipped Tasks")
            for task, reason in plan.skipped:
                with st.container(border=True):
                    c1, c2 = st.columns([2, 3])
                    c1.markdown(f"~~{task.title}~~")
                    c2.caption(reason)
