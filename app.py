import streamlit as st

# Step 1: import the logic layer directly
from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Pet care planning assistant")

# ---------------------------------------------------------------------------
# Step 2: Application "memory" via st.session_state
#
# st.session_state acts as a persistent dictionary that survives reruns.
# We check whether the Owner object already exists before creating it —
# this prevents the owner (and all its pets/tasks) from being wiped on
# every button click.
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    # First load only: build the default Owner and seed it with sample data
    default_owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", age_years=3.0)
    mochi.add_task(Task("Morning walk", duration_minutes=30, priority="high",   frequency="daily"))
    mochi.add_task(Task("Breakfast",    duration_minutes=10, priority="high",   frequency="daily"))
    mochi.add_task(Task("Playtime",     duration_minutes=20, priority="medium", frequency="daily"))
    mochi.add_task(Task("Brushing",     duration_minutes=15, priority="low",    frequency="weekly"))
    default_owner.add_pet(mochi)

    st.session_state.owner = default_owner
    st.session_state.start_hour = 8

# Convenience alias — same object reference, not a copy
owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Owner settings
# ---------------------------------------------------------------------------
st.subheader("Owner")
col1, col2, col3 = st.columns(3)
with col1:
    new_name = st.text_input("Your name", value=owner.name)
    # Sync widget value back to the persistent Owner object
    owner.name = new_name
with col2:
    new_minutes = st.number_input(
        "Time available today (min)",
        min_value=10, max_value=1440,
        value=owner.available_minutes, step=10,
    )
    owner.available_minutes = int(new_minutes)
with col3:
    st.session_state.start_hour = st.slider(
        "Day starts at (hour)",
        min_value=5, max_value=12,
        value=st.session_state.start_hour,
    )

st.divider()

# ---------------------------------------------------------------------------
# Step 3: Pet management — every action calls an Owner / Pet method directly
# ---------------------------------------------------------------------------
st.subheader("Pets & Tasks")

# --- Add a new pet -----------------------------------------------------------
with st.expander("Add a pet"):
    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        new_pet_name = st.text_input("Pet name", key="new_pet_name")
    with pc2:
        new_pet_species = st.selectbox(
            "Species", ["dog", "cat", "rabbit", "bird", "other"], key="new_pet_species"
        )
    with pc3:
        new_pet_age = st.number_input(
            "Age (years)", min_value=0.0, max_value=30.0, value=1.0, step=0.5, key="new_pet_age"
        )
    if st.button("Add pet"):
        if new_pet_name.strip():
            # Step 3: call owner.add_pet() with a real Pet object
            owner.add_pet(Pet(
                name=new_pet_name.strip(),
                species=new_pet_species,
                age_years=float(new_pet_age),
            ))
            st.rerun()
        else:
            st.warning("Please enter a pet name.")

# --- Show each pet and its tasks ---------------------------------------------
for pi, pet in enumerate(owner.pets):          # iterating actual Pet objects
    with st.expander(f"🐾 {pet.name} the {pet.species}", expanded=True):

        if st.button(f"Remove {pet.name}", key=f"remove_pet_{pi}"):
            owner.pets.pop(pi)                 # mutate the owner's list directly
            st.rerun()

        # Task list
        st.markdown("**Tasks:**")
        if pet.tasks:
            for ti, task in enumerate(pet.tasks):   # actual Task objects
                tc1, tc2, tc3, tc4 = st.columns([3, 2, 2, 1])
                tc1.write(task.title)
                tc2.write(f"{task.duration_minutes} min · {task.frequency}")
                tc3.write(task.priority)
                if tc4.button("✕", key=f"rm_task_{pi}_{ti}"):
                    pet.tasks.pop(ti)          # mutate the Pet's task list directly
                    st.rerun()
        else:
            st.caption("No tasks yet.")

        # Add a task to this pet
        st.markdown("**Add a task:**")
        ac1, ac2, ac3, ac4 = st.columns([3, 2, 2, 2])
        with ac1:
            t_title = st.text_input("Title", key=f"t_title_{pi}", value="New task")
        with ac2:
            t_dur = st.number_input(
                "Duration (min)", min_value=1, max_value=240, value=15, key=f"t_dur_{pi}"
            )
        with ac3:
            t_pri = st.selectbox(
                "Priority", ["low", "medium", "high"], index=1, key=f"t_pri_{pi}"
            )
        with ac4:
            t_freq = st.selectbox(
                "Frequency", ["daily", "weekly", "as-needed"], key=f"t_freq_{pi}"
            )

        if st.button("Add task", key=f"add_task_{pi}"):
            # Step 3: call pet.add_task() with a real Task object
            pet.add_task(Task(
                title=t_title,
                duration_minutes=int(t_dur),
                priority=t_pri,
                frequency=t_freq,
            ))
            st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Generate schedule
# ---------------------------------------------------------------------------
st.subheader("Generate Schedule")

if st.button("Build daily plan", type="primary"):
    if not owner.get_pending_tasks():
        st.warning("Add at least one task before generating a plan.")
    else:
        # Scheduler queries the owner directly — no reconstruction needed
        plan = Scheduler(owner=owner, start_hour=st.session_state.start_hour).build_plan()

        st.success(
            f"Plan for **{owner.name}** — {plan.total_minutes} min scheduled "
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
