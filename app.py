import streamlit as st
from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Pet care planning assistant")

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

if "pets" not in st.session_state:
    st.session_state.pets = [
        {
            "name": "Mochi",
            "species": "dog",
            "age": 3.0,
            "tasks": [
                {"title": "Morning walk",  "duration": 30, "priority": "high",   "frequency": "daily"},
                {"title": "Breakfast",     "duration": 10, "priority": "high",   "frequency": "daily"},
                {"title": "Playtime",      "duration": 20, "priority": "medium", "frequency": "daily"},
                {"title": "Brushing",      "duration": 15, "priority": "low",    "frequency": "weekly"},
            ],
        }
    ]

# ---------------------------------------------------------------------------
# Owner info
# ---------------------------------------------------------------------------
st.subheader("Owner")
col1, col2, col3 = st.columns(3)
with col1:
    owner_name = st.text_input("Your name", value="Jordan")
with col2:
    available_minutes = st.number_input(
        "Time available today (min)", min_value=10, max_value=1440, value=90, step=10
    )
with col3:
    start_hour = st.slider("Day starts at (hour)", min_value=5, max_value=12, value=8)

st.divider()

# ---------------------------------------------------------------------------
# Pet management
# ---------------------------------------------------------------------------
st.subheader("Pets & Tasks")

# Add a new pet
with st.expander("Add a pet"):
    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        new_pet_name = st.text_input("Pet name", key="new_pet_name")
    with pc2:
        new_pet_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"], key="new_pet_species")
    with pc3:
        new_pet_age = st.number_input("Age (years)", min_value=0.0, max_value=30.0, value=1.0, step=0.5, key="new_pet_age")
    if st.button("Add pet") and new_pet_name.strip():
        st.session_state.pets.append(
            {"name": new_pet_name.strip(), "species": new_pet_species, "age": new_pet_age, "tasks": []}
        )
        st.rerun()

# Show each pet and its tasks
for pi, pet_data in enumerate(st.session_state.pets):
    with st.expander(f"🐾 {pet_data['name']} the {pet_data['species']}", expanded=True):

        # Remove pet button
        if st.button(f"Remove {pet_data['name']}", key=f"remove_pet_{pi}"):
            st.session_state.pets.pop(pi)
            st.rerun()

        # Task list
        st.markdown("**Tasks:**")
        for ti, task in enumerate(pet_data["tasks"]):
            tc1, tc2, tc3, tc4 = st.columns([3, 2, 2, 1])
            tc1.write(task["title"])
            tc2.write(f"{task['duration']} min · {task['frequency']}")
            tc3.write(task["priority"])
            if tc4.button("✕", key=f"rm_task_{pi}_{ti}"):
                pet_data["tasks"].pop(ti)
                st.rerun()

        # Add task to this pet
        st.markdown("**Add a task:**")
        ac1, ac2, ac3, ac4 = st.columns([3, 2, 2, 2])
        with ac1:
            t_title = st.text_input("Title", key=f"t_title_{pi}", value="New task")
        with ac2:
            t_dur = st.number_input("Duration (min)", min_value=1, max_value=240, value=15, key=f"t_dur_{pi}")
        with ac3:
            t_pri = st.selectbox("Priority", ["low", "medium", "high"], index=1, key=f"t_pri_{pi}")
        with ac4:
            t_freq = st.selectbox("Frequency", ["daily", "weekly", "as-needed"], key=f"t_freq_{pi}")

        if st.button("Add task", key=f"add_task_{pi}"):
            pet_data["tasks"].append(
                {"title": t_title, "duration": int(t_dur), "priority": t_pri, "frequency": t_freq}
            )
            st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Generate schedule
# ---------------------------------------------------------------------------
st.subheader("Generate Schedule")

if st.button("Build daily plan", type="primary"):
    total_tasks = sum(len(p["tasks"]) for p in st.session_state.pets)
    if total_tasks == 0:
        st.warning("Add at least one task before generating a plan.")
    else:
        owner = Owner(name=owner_name, available_minutes=int(available_minutes))
        for pet_data in st.session_state.pets:
            pet = Pet(name=pet_data["name"], species=pet_data["species"], age_years=pet_data["age"])
            for t in pet_data["tasks"]:
                pet.add_task(Task(
                    title=t["title"],
                    duration_minutes=t["duration"],
                    priority=t["priority"],
                    frequency=t["frequency"],
                ))
            owner.add_pet(pet)

        plan = Scheduler(owner=owner, start_hour=start_hour).build_plan()

        st.success(
            f"Plan for **{owner_name}** — {plan.total_minutes} min scheduled "
            f"out of {owner.available_minutes} min available."
        )

        st.markdown("### Scheduled Tasks")
        for st_task in plan.scheduled:
            with st.container(border=True):
                c1, c2 = st.columns([2, 3])
                c1.markdown(f"**{st_task.task.title}**")
                c1.caption(f"{st_task.pet.name} · {st_task.time_range()}")
                c2.caption(st_task.reason)

        if plan.skipped:
            st.markdown("### Skipped Tasks")
            for task, pet, reason in plan.skipped:
                with st.container(border=True):
                    c1, c2 = st.columns([2, 3])
                    c1.markdown(f"~~{task.title}~~ ({pet.name})")
                    c2.caption(reason)
