"""Streamlit interface for the PawPal+ pet-care scheduler."""
from datetime import date, time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")
st.title("🐾 PawPal+")
st.caption("Plan pet care tasks around priority, preferred times, and the time you have.")

if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()
if "daily_plan" not in st.session_state:
    st.session_state.daily_plan = None

owner = st.session_state.owner
scheduler = st.session_state.scheduler
owner.name = st.text_input("Owner name", value=owner.name, key="owner_name").strip() or "Owner"
preference_text = st.text_input(
    "Task title keywords to favor within the same priority (comma-separated)",
    value=", ".join(owner.preferences),
    key="owner_preferences",
)
owner.preferences = [keyword.strip() for keyword in preference_text.split(",") if keyword.strip()]

with st.expander("Add a pet", expanded=not owner.pets):
    with st.form("add_pet_form"):
        pet_col, species_col = st.columns([2, 1])
        pet_name = pet_col.text_input("Pet name", placeholder="Mochi")
        species = species_col.selectbox("Species", ["Dog", "Cat", "Other"])
        add_pet = st.form_submit_button("Add pet")
    if add_pet:
        if not pet_name.strip():
            st.error("Enter a pet name first.")
        else:
            try:
                owner.add_pet(Pet(pet_name.strip(), species.lower()))
                st.session_state.daily_plan = None
                st.success(f"Added {pet_name.strip()}.")
            except ValueError as error:
                st.error(str(error))

st.subheader("Add a care task")
if not owner.pets:
    st.info("Add a pet before creating its care tasks.")
else:
    with st.form("add_task_form"):
        pet = st.selectbox("Pet", owner.pets, format_func=lambda item: f"{item.name} ({item.species})")
        title = st.text_input("Task", placeholder="Morning walk")
        task_col1, task_col2, task_col3 = st.columns(3)
        due_date = task_col1.date_input("Due date", value=date.today())
        preferred_time = task_col2.time_input("Preferred time", value=time(9, 0), step=300)
        duration = task_col3.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        task_col4, task_col5 = st.columns(2)
        priority = task_col4.selectbox("Priority", ["high", "medium", "low"])
        frequency = task_col5.selectbox("Repeat", ["once", "daily", "weekly"])
        notes = st.text_input("Notes (optional)")
        add_task = st.form_submit_button("Add task")
    if add_task:
        if not title.strip():
            st.error("Enter a task title first.")
        else:
            try:
                pet.add_task(
                    Task(
                        title=title.strip(),
                        duration_minutes=int(duration),
                        priority=priority,
                        due_date=due_date,
                        preferred_time=preferred_time,
                        frequency=frequency,
                        notes=notes.strip(),
                    )
                )
                st.session_state.daily_plan = None
                st.success(f"Added {title.strip()} for {pet.name}.")
            except ValueError as error:
                st.error(str(error))

st.subheader("Tasks")
all_tasks = owner.get_all_tasks()
if not all_tasks:
    st.info("No tasks yet. Add a pet and a care task to get started.")
else:
    for pet, task in all_tasks:
        left, right = st.columns([5, 1])
        left.write(
            f"**{pet.name} · {task.title}** — {task.due_date:%b %d}, "
            f"{task.preferred_time:%H:%M} · {task.duration_minutes} min · "
            f"{task.priority} priority · {task.frequency}"
        )
        if task.completed:
            right.success("Done")
        elif right.button("Mark done", key=f"done_{id(task)}"):
            scheduler.mark_task_complete(pet, task)
            st.session_state.daily_plan = None
            st.rerun()

st.divider()
st.subheader("Build today's plan")
plan_col1, plan_col2, plan_col3 = st.columns(3)
plan_date = plan_col1.date_input("Plan date", value=date.today())
start_time = plan_col2.time_input("Start time", value=time(8, 0), step=300)
available_minutes = plan_col3.number_input("Available minutes", min_value=0, max_value=1440, value=480)
if st.button("Generate daily plan", type="primary"):
    st.session_state.daily_plan = scheduler.build_daily_plan(
        owner,
        plan_date,
        start_time=start_time,
        available_minutes=int(available_minutes),
    )

plan = st.session_state.daily_plan
if plan is not None:
    st.markdown(f"### Plan for {plan.plan_date:%A, %B %d}")
    if plan.entries:
        st.table(
            [
                {
                    "Time": f"{entry.start:%H:%M}–{entry.end:%H:%M}",
                    "Pet": entry.pet_name,
                    "Task": entry.task.title,
                    "Priority": entry.task.priority.title(),
                    "Why this time": entry.reason,
                }
                for entry in plan.entries
            ]
        )
    else:
        st.info("No incomplete tasks are due on this date.")
    for pet_name, task, reason in plan.skipped:
        st.warning(f"Not scheduled — {pet_name}: {task.title}. {reason}")
    for warning in plan.conflicts:
        st.warning(warning)
    if plan.entries and not plan.skipped and not plan.conflicts:
        st.success("All due tasks fit in the available time, with no preferred-time conflicts.")
