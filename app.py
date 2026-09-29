from __future__ import annotations

from collections import Counter
from pathlib import Path

import streamlit as st

from components.event_form import render_event_section
from components.parameter_form import render_parameters_section
from components.schedule_view import render_schedule_section
from components.teams_form import render_teams_section
from components.ui_helpers import (
    inject_theme,
    render_brand_header,
    render_next_action,
    render_stepper,
    section_heading,
)
from src.database import init_db
from src.models import Event
from src.utils import new_id
from src.validation import structural_errors

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="La jeunesse débat — Planning",
    page_icon="🗣️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_theme()
init_db()

if "event" not in st.session_state:
    st.session_state.event = Event(
        id=new_id(),
        name="Finale régionale – La jeunesse débat",
        categories=["Secondaire 1"],
        number_of_rooms=6,
    )
if "schools" not in st.session_state:
    st.session_state.schools = []
if "teams" not in st.session_state:
    st.session_state.teams = []
if "schedule_result" not in st.session_state:
    st.session_state.schedule_result = None
if "detailed_mode" not in st.session_state:
    st.session_state.detailed_mode = False

render_brand_header(ROOT)
stepper_slot = st.empty()
next_action_slot = st.empty()

section_heading(
    1,
    "Définir l’événement",
    "Choisissez le nom de la finale et les catégories qui participeront.",
)
event, schools, teams, loaded, event_changed = render_event_section(
    st.session_state.event,
    st.session_state.schools,
    st.session_state.teams,
)
st.session_state.event = event
st.session_state.schools = schools
st.session_state.teams = teams
if loaded:
    st.session_state.schedule_result = None
    st.rerun()
if event_changed:
    st.session_state.schedule_result = None

section_heading(
    2,
    "Ajouter les équipes",
    "Ajoutez les établissements ; les équipes A, B, C… sont créées automatiquement.",
)
schools, teams, detailed_mode, teams_changed = render_teams_section(
    st.session_state.event,
    st.session_state.schools,
    st.session_state.teams,
    st.session_state.detailed_mode,
)
st.session_state.schools = schools
st.session_state.teams = teams
st.session_state.detailed_mode = detailed_mode
if teams_changed:
    st.session_state.schedule_result = None

section_heading(
    3,
    "Choisir les salles",
    "Indiquez le nombre de salles disponibles ; l’application calcule automatiquement la capacité nécessaire.",
)
event, rooms_changed = render_parameters_section(
    st.session_state.event,
    st.session_state.teams,
)
st.session_state.event = event
if rooms_changed:
    st.session_state.schedule_result = None

section_heading(
    4,
    "Générer le planning",
    "L’optimiseur minimise les sessions, équilibre les rencontres et stabilise les salles par catégorie.",
)
st.session_state.schedule_result = render_schedule_section(
    st.session_state.event,
    st.session_state.teams,
    st.session_state.schedule_result,
)

# Fill the top workflow summary after all widgets have updated the state.
event_ready = bool(st.session_state.event.name.strip() and st.session_state.event.categories)
counts = Counter(t.category for t in st.session_state.teams)
teams_ready = bool(st.session_state.teams) and all(
    counts.get(category, 0) >= 2 and counts.get(category, 0) % 2 == 0
    for category in st.session_state.event.categories
)
config_ready = not structural_errors(st.session_state.event, st.session_state.teams)
planning_ready = st.session_state.schedule_result is not None
states = [event_ready, teams_ready, config_ready, planning_ready]
active_index = next((i for i, done in enumerate(states) if not done), 3)
with stepper_slot.container():
    render_stepper(states, active_index)
with next_action_slot.container():
    render_next_action(states)

