# Project source

Source snapshot of the application files included in this archive.

## `app.py`

```python
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

st.markdown(
    '<div class="yes-footer">Données enregistrées localement dans SQLite · '
    'Logo YES : <code>assets/logo.png</code></div>',
    unsafe_allow_html=True,
)

```

## `components/ui_helpers.py`

```python
from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st


YES_DARK = "#173642"
YES_PETROL = "#28647A"
YES_CYAN = "#00A0AE"
YES_PALE = "#EAF7F8"
YES_BG = "#F6F9FA"


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --yes-ink: #173642;
            --yes-petrol: #28647A;
            --yes-cyan: #00A0AE;
            --yes-cyan-dark: #008B98;
            --yes-soft: #EAF7F8;
            --yes-soft-2: #F3FAFB;
            --yes-bg: #F6F9FA;
            --yes-border: #DCE7EA;
            --yes-muted: #687D85;
            --yes-white: #FFFFFF;
            --yes-shadow: 0 10px 28px rgba(23,54,66,.065);
        }

        html { scroll-behavior: smooth; }

        .stApp {
            background:
                radial-gradient(circle at 96% 2%, rgba(0,160,174,.08), transparent 22rem),
                linear-gradient(180deg, #FBFDFD 0%, var(--yes-bg) 32%, var(--yes-bg) 100%);
            color: var(--yes-ink);
        }

        .block-container {
            max-width: 1160px;
            padding-top: 1.15rem;
            padding-bottom: 3.5rem;
        }

        section[data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }

        [data-testid="stHeader"] { background: transparent; }
        #MainMenu, footer { visibility: hidden; }

        h1, h2, h3, h4 {
            color: var(--yes-ink);
            letter-spacing: -.018em;
        }

        p, label, .stCaption { color: var(--yes-muted); }

        /* Main Streamlit cards */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--yes-border) !important;
            border-radius: 18px !important;
            background: rgba(255,255,255,.95);
            box-shadow: 0 7px 24px rgba(23,54,66,.045);
        }

        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid var(--yes-border);
            border-radius: 14px;
            padding: 12px 14px;
            box-shadow: none;
        }
        div[data-testid="stMetricLabel"] p {
            font-size: .82rem;
            font-weight: 650;
            color: var(--yes-muted);
        }
        div[data-testid="stMetricValue"] {
            color: var(--yes-ink);
            font-weight: 750;
        }

        /* Inputs */
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-testid="stNumberInput"] input,
        textarea {
            border-radius: 11px !important;
            border-color: #CDDDE1 !important;
        }
        div[data-baseweb="input"] > div:focus-within,
        div[data-baseweb="select"] > div:focus-within {
            border-color: var(--yes-cyan) !important;
            box-shadow: 0 0 0 2px rgba(0,160,174,.10) !important;
        }

        /* Buttons */
        div.stButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            border-radius: 11px;
            min-height: 2.75rem;
            font-weight: 700;
            border: 1px solid #C9D9DE;
            transition: transform .12s ease, box-shadow .12s ease, filter .12s ease;
        }
        div.stButton > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            border-color: #AFCBD1;
        }
        div.stButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, var(--yes-petrol), var(--yes-cyan));
            border: 0;
            color: white;
            box-shadow: 0 7px 16px rgba(0,160,174,.16);
        }
        div.stButton > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
            filter: brightness(.985);
            transform: translateY(-1px);
            box-shadow: 0 9px 20px rgba(0,160,174,.19);
        }

        div[data-testid="stAlert"] {
            border-radius: 12px;
            border-width: 1px;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            background: #EDF4F6;
            padding: 5px;
            border-radius: 12px;
            overflow-x: auto;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 9px;
            padding-left: 14px;
            padding-right: 14px;
            color: var(--yes-petrol);
            font-weight: 650;
            white-space: nowrap;
        }
        .stTabs [aria-selected="true"] {
            background: white;
            box-shadow: 0 2px 8px rgba(23,54,66,.07);
        }

        /* Header */
        .yes-brand-shell {
            background: rgba(255,255,255,.92);
            border: 1px solid var(--yes-border);
            border-radius: 22px;
            padding: 22px 24px;
            box-shadow: var(--yes-shadow);
            margin-bottom: 14px;
            position: relative;
            overflow: hidden;
        }
        .yes-brand-shell::after {
            content: "";
            position: absolute;
            width: 220px;
            height: 220px;
            border-radius: 50%;
            right: -105px;
            top: -120px;
            background: rgba(0,160,174,.10);
            pointer-events: none;
        }
        .yes-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            color: var(--yes-cyan-dark);
            font-size: .78rem;
            font-weight: 800;
            letter-spacing: .055em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        .yes-eyebrow-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--yes-cyan);
        }
        .yes-brand-shell h1 {
            margin: 0 0 5px 0;
            font-size: 2rem;
            line-height: 1.08;
            color: var(--yes-ink);
        }
        .yes-brand-shell p {
            margin: 0;
            max-width: 760px;
            color: var(--yes-muted);
            font-size: .99rem;
            line-height: 1.48;
        }
        .yes-logo-fallback {
            background: linear-gradient(145deg, #F0FAFB, #FFFFFF);
            border: 1px solid var(--yes-border);
            border-radius: 18px;
            padding: 18px 14px;
            text-align: center;
        }
        .yes-logo-fallback strong {
            display:block;
            color: var(--yes-petrol);
            font-size: 1.25rem;
            letter-spacing: .03em;
        }
        .yes-logo-fallback span {
            color: var(--yes-cyan-dark);
            font-size: .72rem;
        }

        /* Workflow */
        .yes-workflow-label {
            color: var(--yes-muted);
            font-size: .78rem;
            font-weight: 750;
            text-transform: uppercase;
            letter-spacing: .055em;
            margin: 2px 0 8px 2px;
        }
        .yes-stepper {
            display: grid;
            grid-template-columns: repeat(4, minmax(0,1fr));
            gap: 8px;
            margin: 0 0 10px 0;
        }
        .yes-step {
            background: rgba(255,255,255,.92);
            border: 1px solid var(--yes-border);
            border-radius: 13px;
            padding: 10px 11px;
            display: flex;
            align-items: center;
            gap: 9px;
            min-height: 54px;
        }
        .yes-step.done {
            background: #F4FBFB;
            border-color: #C7E6E8;
        }
        .yes-step.active {
            background: #FFFFFF;
            border-color: var(--yes-cyan);
            box-shadow: 0 0 0 2px rgba(0,160,174,.07);
        }
        .yes-step-number {
            width: 27px;
            height: 27px;
            border-radius: 9px;
            background: #E9F0F2;
            color: var(--yes-petrol);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            flex: 0 0 auto;
            font-size: .84rem;
        }
        .yes-step.done .yes-step-number,
        .yes-step.active .yes-step-number {
            background: var(--yes-cyan);
            color: white;
        }
        .yes-step-label {
            color: var(--yes-ink);
            font-weight: 720;
            line-height: 1.12;
            font-size: .90rem;
        }
        .yes-step-small {
            display: block;
            color: var(--yes-muted);
            font-size: .72rem;
            font-weight: 450;
            margin-top: 2px;
        }

        .yes-next-action {
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:14px;
            border-radius: 13px;
            padding: 11px 14px;
            margin: 0 0 24px 0;
            background: linear-gradient(90deg, #EEF9FA 0%, #F8FCFC 100%);
            border: 1px solid #D1E9EB;
        }
        .yes-next-action strong {
            color: var(--yes-ink);
            font-size: .91rem;
        }
        .yes-next-action span {
            color: var(--yes-muted);
            font-size: .84rem;
        }

        /* Section headings */
        .yes-section-heading {
            margin: 28px 0 10px 0;
        }
        .yes-section-kicker {
            color: var(--yes-cyan-dark);
            font-size: .74rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .06em;
            margin-bottom: 3px;
        }
        .yes-section-heading h2 {
            margin: 0;
            font-size: 1.35rem;
            line-height: 1.18;
        }
        .yes-section-heading p {
            margin: 4px 0 0 0;
            color: var(--yes-muted);
            font-size: .91rem;
        }

        .yes-empty-state {
            border: 1px dashed #C6DADF;
            background: #FAFCFD;
            border-radius: 14px;
            padding: 18px;
            text-align: center;
            color: var(--yes-muted);
        }
        .yes-empty-state strong {
            display: block;
            color: var(--yes-ink);
            margin-bottom: 3px;
        }

        .yes-category-chip {
            display:inline-block;
            padding: 4px 8px;
            border-radius: 999px;
            font-size: .72rem;
            font-weight: 750;
            margin-right: 5px;
        }
        .yes-category-chip.s1 { background: #E2F7F8; color: #087D87; }
        .yes-category-chip.s2 { background: #E9F0F3; color: #315F70; }

        /* Schedule */
        .debate-card {
            background: white;
            border: 1px solid var(--yes-border);
            border-radius: 15px;
            padding: 14px;
            min-height: 195px;
            box-shadow: 0 5px 14px rgba(23,54,66,.035);
        }
        .debate-card.s1 { border-top: 4px solid var(--yes-cyan); }
        .debate-card.s2 { border-top: 4px solid var(--yes-petrol); }
        .debate-card.empty {
            background: #FAFCFC;
            border-style: dashed;
            min-height: 195px;
            box-shadow: none;
        }
        .debate-card-top {
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:8px;
            margin-bottom: 10px;
        }
        .room-title {
            font-weight: 800;
            color: var(--yes-ink);
            font-size: .98rem;
        }
        .badge {
            display: inline-block;
            border-radius: 999px;
            padding: 4px 8px;
            font-size: .70rem;
            font-weight: 750;
            background: var(--yes-soft);
            color: var(--yes-petrol);
            white-space: nowrap;
        }
        .question-row {
            color: var(--yes-muted);
            font-size: .79rem;
            font-weight: 650;
            padding-bottom: 8px;
            margin-bottom: 9px;
            border-bottom: 1px solid #ECF1F2;
        }
        .side-block {
            display:grid;
            grid-template-columns: 58px 1fr;
            gap:8px;
            align-items:start;
            margin-top: 8px;
        }
        .side-label {
            font-size:.68rem;
            font-weight:850;
            letter-spacing:.045em;
            color:var(--yes-petrol);
            background:#F0F7F8;
            border-radius:7px;
            padding:4px 6px;
            text-align:center;
        }
        .side-team {
            color:var(--yes-ink);
            font-weight:650;
            line-height:1.28;
            font-size:.88rem;
        }
        .empty-label {
            color: var(--yes-muted);
            margin-top: 54px;
            text-align: center;
            font-weight: 620;
            font-size: .86rem;
        }

        .quality-chip {
            display: inline-block;
            padding: 5px 9px;
            border-radius: 999px;
            background: #F1F7F8;
            color: var(--yes-ink);
            font-size: .78rem;
            margin: 0 5px 5px 0;
            border: 1px solid #E1ECEE;
        }

        .yes-footer {
            border-top: 1px solid var(--yes-border);
            margin-top: 30px;
            padding-top: 14px;
            color: var(--yes-muted);
            font-size: .78rem;
            text-align:center;
        }

        @media (max-width: 760px) {
            .block-container { padding-top: .7rem; }
            .yes-stepper { grid-template-columns: 1fr 1fr; }
            .yes-brand-shell { padding: 18px; }
            .yes-brand-shell h1 { font-size: 1.55rem; }
            .yes-next-action { align-items:flex-start; flex-direction:column; gap:2px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def find_logo(root: Path) -> Path | None:
    assets = root / "assets"
    preferred = assets / "logo.png"
    if preferred.exists():
        return preferred
    png_files = sorted(assets.glob("*.png")) if assets.exists() else []
    return png_files[0] if png_files else None


def render_brand_header(root: Path) -> None:
    logo = find_logo(root)
    c_logo, c_text = st.columns([1.15, 5.5])
    with c_logo:
        if logo:
            st.image(str(logo), use_container_width=True)
        else:
            st.markdown(
                '<div class="yes-logo-fallback"><strong>YES</strong>'
                '<span>Young Enterprise Switzerland</span></div>',
                unsafe_allow_html=True,
            )
    with c_text:
        st.markdown(
            """
            <div class="yes-brand-shell">
                <div class="yes-eyebrow"><span class="yes-eyebrow-dot"></span>La jeunesse débat</div>
                <h1>Planificateur de finale régionale</h1>
                <p>Configurez les équipes et les salles, puis générez automatiquement un planning équilibré et directement exploitable le jour du concours.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_stepper(done: list[bool], active_index: int) -> None:
    labels = [
        ("Événement", "nom & catégories"),
        ("Équipes", "établissements"),
        ("Salles", "capacité"),
        ("Planning", "génération"),
    ]
    blocks: list[str] = []
    for idx, (label, small) in enumerate(labels):
        classes = ["yes-step"]
        if done[idx]:
            classes.append("done")
        elif idx == active_index:
            classes.append("active")
        marker = "✓" if done[idx] else str(idx + 1)
        blocks.append(
            f'<div class="{" ".join(classes)}">'
            f'<span class="yes-step-number">{marker}</span>'
            f'<span class="yes-step-label">{escape(label)}<span class="yes-step-small">{escape(small)}</span></span>'
            "</div>"
        )
    st.markdown('<div class="yes-workflow-label">Votre progression</div>', unsafe_allow_html=True)
    st.markdown('<div class="yes-stepper">' + "".join(blocks) + "</div>", unsafe_allow_html=True)


def render_next_action(states: list[bool]) -> None:
    if not states[0]:
        title, detail = "Commencez par l’événement", "Donnez-lui un nom et choisissez les catégories présentes."
    elif not states[1]:
        title, detail = "Ajoutez les équipes", "Saisissez chaque établissement et le nombre d’équipes qu’il inscrit."
    elif not states[2]:
        title, detail = "Vérifiez la capacité", "Choisissez le nombre de salles et corrigez les éventuelles contraintes bloquantes."
    elif not states[3]:
        title, detail = "Tout est prêt", "Générez le planning optimal à l’étape 4."
    else:
        title, detail = "Planning prêt", "Consultez les sessions ci-dessous ou ajustez la configuration pour le recalculer."
    st.markdown(
        f'<div class="yes-next-action"><strong>{escape(title)}</strong><span>{escape(detail)}</span></div>',
        unsafe_allow_html=True,
    )


def section_heading(number: int, title: str, help_text: str) -> None:
    st.markdown(
        f"""
        <div class="yes-section-heading">
            <div class="yes-section-kicker">Étape {number}</div>
            <h2>{escape(title)}</h2>
            <p>{escape(help_text)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(title: str, text: str) -> None:
    st.markdown(
        f'<div class="yes-empty-state"><strong>{escape(title)}</strong>{escape(text)}</div>',
        unsafe_allow_html=True,
    )

```

## `components/event_form.py`

```python
from __future__ import annotations

import streamlit as st

from src.database import list_events, load_event, save_event
from src.models import Event, School, Team

AVAILABLE_CATEGORIES = ["Secondaire 1", "Secondaire 2"]


def _category_mode(categories: list[str]) -> str:
    selected = set(categories)
    if selected == set(AVAILABLE_CATEGORIES):
        return "Les deux"
    if selected == {"Secondaire 2"}:
        return "Secondaire 2"
    return "Secondaire 1"


def render_event_section(
    event: Event, schools: list[School], teams: list[Team]
) -> tuple[Event, list[School], list[Team], bool, bool]:
    """Render the event step.

    Returns (event, schools, teams, loaded_event, configuration_changed).
    """
    previous_name = event.name
    previous_categories = list(event.categories)

    with st.container(border=True):
        left, right = st.columns([1.6, 1])
        with left:
            event.name = st.text_input(
                "Nom de la finale régionale",
                value=event.name,
                placeholder="Ex. Finale régionale – Fribourg",
                help="Ce nom permet aussi de retrouver facilement l’événement sauvegardé.",
            )
        with right:
            mode = st.radio(
                "Catégories participantes",
                ["Secondaire 1", "Secondaire 2", "Les deux"],
                index=["Secondaire 1", "Secondaire 2", "Les deux"].index(
                    _category_mode(event.categories)
                ),
                horizontal=True,
            )
            event.categories = {
                "Secondaire 1": ["Secondaire 1"],
                "Secondaire 2": ["Secondaire 2"],
                "Les deux": ["Secondaire 1", "Secondaire 2"],
            }[mode]

        if teams and set(t.category for t in teams) - set(event.categories):
            st.info(
                "Certaines équipes déjà saisies appartiennent à une catégorie actuellement désactivée. "
                "Réactivez cette catégorie ou retirez les établissements concernés avant de générer le planning."
            )

        with st.expander("Mes événements sauvegardés", expanded=False):
            save_col, load_col = st.columns(2)
            with save_col:
                st.markdown("**Sauvegarder l’événement actuel**")
                st.caption("Conserve l’événement, les établissements et les équipes dans `data/app.db`.")
                if st.button("Sauvegarder", use_container_width=True):
                    save_event(event, schools, teams)
                    st.success("Événement sauvegardé.")

            with load_col:
                st.markdown("**Reprendre un événement**")
                saved = list_events()
                if saved:
                    options = {
                        f"{row['name']} · {row['updated_at'][:16]}": row["id"]
                        for row in saved
                    }
                    selected_label = st.selectbox(
                        "Événement sauvegardé",
                        list(options),
                        label_visibility="collapsed",
                    )
                    if st.button("Charger", use_container_width=True):
                        loaded_event, loaded_schools, loaded_teams = load_event(
                            options[selected_label]
                        )
                        return loaded_event, loaded_schools, loaded_teams, True, True
                else:
                    st.caption("Aucun événement sauvegardé pour le moment.")

    changed = previous_name != event.name or previous_categories != event.categories
    return event, schools, teams, False, changed

```

## `components/teams_form.py`

```python
from __future__ import annotations

from collections import Counter
import hashlib
from html import escape

import pandas as pd
import streamlit as st

from components.ui_helpers import empty_state
from src.models import Event, School, Team
from src.utils import add_school_with_teams


def _team_labels(school_teams: list[Team]) -> str:
    return ", ".join(team.label for team in school_teams)


def _render_school_group(
    category: str,
    schools: list[School],
    teams: list[Team],
) -> None:
    category_schools = [school for school in schools if school.category == category]
    chip_class = "s1" if category == "Secondaire 1" else "s2"

    with st.container(border=True):
        st.markdown(
            f'<span class="yes-category-chip {chip_class}">{escape(category)}</span> '
            f'<strong>{len(category_schools)} établissement(s)</strong>',
            unsafe_allow_html=True,
        )
        if not category_schools:
            st.caption("Aucun établissement dans cette catégorie.")
            return

        for school in list(category_schools):
            school_teams = [t for t in teams if t.school_id == school.id]
            info_col, delete_col = st.columns([5.2, 1])
            with info_col:
                st.markdown(f"**{school.name}**")
                st.caption(
                    f"{len(school_teams)} équipe(s) · {_team_labels(school_teams)}"
                )
            with delete_col:
                if st.button(
                    "Retirer",
                    key=f"delete_school_{school.id}",
                    use_container_width=True,
                ):
                    schools[:] = [s for s in schools if s.id != school.id]
                    teams[:] = [t for t in teams if t.school_id != school.id]
                    st.session_state.schedule_result = None
                    st.rerun()


def render_teams_section(
    event: Event,
    schools: list[School],
    teams: list[Team],
    detailed_mode: bool,
) -> tuple[list[School], list[Team], bool, bool]:
    """Render team entry and return updated state + changed flag."""
    changed = False

    with st.container(border=True):
        if not event.categories:
            st.info("Choisissez d’abord au moins une catégorie à l’étape 1.")
            return schools, teams, detailed_mode, changed

        counts = Counter(t.category for t in teams)
        summary_cols = st.columns(3)
        summary_cols[0].metric("Établissements", len(schools))
        summary_cols[1].metric("Équipes", len(teams))
        if len(event.categories) == 2:
            summary_cols[2].metric(
                "S1 / S2",
                f"{counts.get('Secondaire 1', 0)} / {counts.get('Secondaire 2', 0)}",
                help="Nombre d’équipes Secondaire 1 / Secondaire 2",
            )
        else:
            summary_cols[2].metric(
                event.categories[0], counts.get(event.categories[0], 0)
            )

        st.markdown("#### Ajouter un établissement")
        st.caption("Indiquez simplement le nombre d’équipes : A, B, C… seront créées automatiquement.")
        with st.form("add_school_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2.4, 1.25, 1])
            with c1:
                school_name = st.text_input(
                    "Établissement",
                    placeholder="Ex. Collège Saint-Michel",
                )
            with c2:
                category = st.selectbox(
                    "Catégorie",
                    event.categories,
                    disabled=len(event.categories) == 1,
                )
            with c3:
                number_of_teams = st.number_input(
                    "Nombre d’équipes",
                    min_value=1,
                    max_value=52,
                    value=2,
                    step=1,
                )

            submitted = st.form_submit_button(
                "Ajouter l’établissement",
                type="primary",
                use_container_width=True,
            )
            if submitted:
                if not school_name.strip():
                    st.error("Indiquez le nom de l’établissement.")
                else:
                    school, new_teams = add_school_with_teams(
                        event_id=event.id,
                        school_name=school_name,
                        category=category,
                        number_of_teams=int(number_of_teams),
                    )
                    schools.append(school)
                    teams.extend(new_teams)
                    changed = True
                    st.success(
                        f"{school.name} ajouté avec {int(number_of_teams)} équipe(s)."
                    )

        if not schools:
            empty_state(
                "Aucun établissement pour le moment",
                "Ajoutez le premier établissement avec le formulaire ci-dessus.",
            )
            return schools, teams, detailed_mode, changed

        st.divider()
        title_col, option_col = st.columns([2.5, 1.2])
        with title_col:
            st.markdown("#### Établissements inscrits")
            st.caption("Vérifiez la liste avant de passer aux salles.")
        with option_col:
            detailed_mode = st.toggle(
                "Ajouter les noms des participant·es",
                value=detailed_mode,
                help="Optionnel : utile pour afficher ensuite la rotation des rôles nominativement.",
            )

        active_categories = [c for c in event.categories if c in {"Secondaire 1", "Secondaire 2"}]
        if len(active_categories) == 2:
            group_cols = st.columns(2)
            for col, category in zip(group_cols, active_categories):
                with col:
                    _render_school_group(category, schools, teams)
        else:
            _render_school_group(active_categories[0], schools, teams)

        if detailed_mode and teams:
            with st.expander("Participant·es et rotation des rôles", expanded=True):
                st.caption(
                    "Cette saisie est optionnelle. Modifiez uniquement les colonnes Participant 1 et Participant 2."
                )
                rows = [
                    {
                        "Établissement": t.school_name,
                        "Catégorie": t.category,
                        "Équipe": t.label,
                        "Participant 1": t.participant_1,
                        "Participant 2": t.participant_2,
                    }
                    for t in teams
                ]
                editor_signature = hashlib.sha1(
                    "|".join(t.id for t in teams).encode("utf-8")
                ).hexdigest()[:10]
                edited = st.data_editor(
                    pd.DataFrame(rows),
                    hide_index=True,
                    use_container_width=True,
                    disabled=["Établissement", "Catégorie", "Équipe"],
                    num_rows="fixed",
                    key=f"participant_editor_{editor_signature}",
                )
                for team, (_, row) in zip(teams, edited.iterrows()):
                    p1 = "" if pd.isna(row["Participant 1"]) else str(row["Participant 1"])
                    p2 = "" if pd.isna(row["Participant 2"]) else str(row["Participant 2"])
                    if p1 != team.participant_1 or p2 != team.participant_2:
                        team.participant_1 = p1
                        team.participant_2 = p2
                        changed = True

    return schools, teams, detailed_mode, changed

```

## `components/parameter_form.py`

```python
from __future__ import annotations

from collections import Counter

import streamlit as st

from src.models import Event, Team
from src.optimizer import theoretical_min_sessions
from src.validation import structural_errors


def render_parameters_section(event: Event, teams: list[Team]) -> tuple[Event, bool]:
    previous_rooms = event.number_of_rooms

    with st.container(border=True):
        input_col, summary_col = st.columns([1.15, 2.85])
        with input_col:
            event.number_of_rooms = int(
                st.number_input(
                    "Salles disponibles",
                    min_value=1,
                    max_value=50,
                    value=max(1, int(event.number_of_rooms)),
                    step=1,
                    help="Une salle accueille au maximum un débat par session.",
                )
            )
            st.caption("Vous pourrez toujours ajuster ce nombre puis recalculer le planning.")

        with summary_col:
            counts = Counter(t.category for t in teams)
            minimum = (
                theoretical_min_sessions(len(teams), event.number_of_rooms)
                if teams and event.number_of_rooms
                else None
            )
            cols = st.columns(3)
            cols[0].metric("Équipes", len(teams))
            cols[1].metric("Débats à planifier", len(teams))
            cols[2].metric("Sessions minimales", minimum if minimum is not None else "—")

            if len(event.categories) == 2:
                st.caption(
                    f"Répartition : {counts.get('Secondaire 1', 0)} équipes en Secondaire 1 · "
                    f"{counts.get('Secondaire 2', 0)} équipes en Secondaire 2."
                )

        errors = structural_errors(event, teams)
        st.divider()
        if errors:
            message = "\n".join(f"• {error}" for error in errors)
            st.error(
                "La configuration n’est pas encore générable. Corrigez ces points :\n\n"
                + message
            )
        else:
            minimum = theoretical_min_sessions(len(teams), event.number_of_rooms)
            st.success(
                f"Configuration prête · le planning peut être généré en au moins {minimum} session(s)."
            )

    return event, previous_rooms != event.number_of_rooms

```

## `components/schedule_view.py`

```python
from __future__ import annotations

from collections import defaultdict
from html import escape

import pandas as pd
import streamlit as st

from src.models import Debate, Event, ScheduleResult, Team
from src.optimizer import OptimizationError, generate_schedule
from src.validation import structural_errors, validate_schedule


def _roles_text(debate: Debate, side: str) -> str:
    roles = debate.pro_roles if side == "POUR" else debate.con_roles
    return " · ".join(f"{r.participant_name} — {r.role_name}" for r in roles)


def _debate_card(room: int, debate: Debate | None) -> str:
    if debate is None:
        return f"""
        <div class="debate-card empty">
            <div class="debate-card-top">
                <div class="room-title">Salle {room}</div>
            </div>
            <div class="empty-label">Salle libre</div>
        </div>
        """

    category_class = "s1" if debate.category == "Secondaire 1" else "s2"
    return f"""
    <div class="debate-card {category_class}">
        <div class="debate-card-top">
            <div class="room-title">Salle {room}</div>
            <span class="badge">{escape(debate.category)}</span>
        </div>
        <div class="question-row">{escape(debate.question)}</div>
        <div class="side-block">
            <div class="side-label">POUR</div>
            <div class="side-team">{escape(debate.pro_team_name)}</div>
        </div>
        <div class="side-block">
            <div class="side-label">CONTRE</div>
            <div class="side-team">{escape(debate.con_team_name)}</div>
        </div>
    </div>
    """


def _render_session_cards(result: ScheduleResult, number_of_rooms: int) -> None:
    by_session: dict[int, list[Debate]] = defaultdict(list)
    for debate in result.debates:
        by_session[debate.session].append(debate)

    sessions = sorted(by_session)
    if not sessions:
        return

    tabs = st.tabs([f"Session {session}" for session in sessions])
    for tab, session in zip(tabs, sessions):
        with tab:
            by_room = {d.room: d for d in by_session[session]}
            used = len(by_room)
            categories = sorted({d.category for d in by_session[session]})
            st.caption(
                f"{used} salle(s) occupée(s) sur {number_of_rooms} · "
                + " · ".join(categories)
            )
            rooms = list(range(1, number_of_rooms + 1))
            for start in range(0, len(rooms), 3):
                chunk = rooms[start : start + 3]
                columns = st.columns(len(chunk))
                for col, room in zip(columns, chunk):
                    with col:
                        st.markdown(
                            _debate_card(room, by_room.get(room)),
                            unsafe_allow_html=True,
                        )


def _render_table(result: ScheduleResult) -> None:
    rows = []
    for d in sorted(result.debates, key=lambda item: (item.session, item.room)):
        rows.append(
            {
                "Session": d.session,
                "Salle": d.room,
                "Catégorie": d.category,
                "Question": d.question,
                "POUR": d.pro_team_name,
                "CONTRE": d.con_team_name,
                "Rôles POUR": _roles_text(d, "POUR"),
                "Rôles CONTRE": _roles_text(d, "CONTRE"),
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def _render_quality(result: ScheduleResult, event: Event, teams: list[Team]) -> None:
    validation = validate_schedule(event, teams, result.debates)
    p = result.preference_metrics

    if validation.valid:
        st.success("Planning valide : toutes les contraintes obligatoires sont respectées.")
    else:
        for item in validation.errors:
            st.error(item)
        return

    st.markdown("#### Organisation des rencontres")
    st.caption(
        "Ces éléments sont des préférences d’organisation ; ils n’affectent pas la validité du planning."
    )

    groups = [
        ("Adversaires répétés", p["repeated_opponents"], "Aucun adversaire répété"),
        (
            "Confrontations internes à un établissement",
            p["same_school"],
            "Aucune confrontation interne",
        ),
        (
            "Équipes restées du même côté",
            p["same_side"],
            "Alternance POUR / CONTRE respectée quand possible",
        ),
        (
            "Couples d’établissements répétés",
            p["repeated_school_pairs"],
            "Aucun couple d’établissements répété",
        ),
        (
            "Équipes utilisant deux fois la même salle",
            p["same_room"],
            "Les équipes changent de salle",
        ),
        (
            "Confrontations de même rang A/A, B/B, …",
            p["same_label"],
            "Pas de confrontation de même rang",
        ),
    ]

    successes = [success for _, items, success in groups if not items]
    if successes:
        st.markdown(
            "".join(
                f'<span class="quality-chip">✓ {escape(text)}</span>'
                for text in successes
            ),
            unsafe_allow_html=True,
        )

    adjustments = [(title, items) for title, items, _ in groups if items]
    if adjustments:
        st.markdown("**Ajustements nécessaires pour conserver un planning réalisable**")
        for title, items in adjustments:
            with st.expander(f"{title} · {len(items)}", expanded=False):
                for item in items:
                    st.write(f"• {item}")
    else:
        st.info("Toutes les principales préférences de rencontres sont satisfaites.")

    st.divider()
    st.markdown("#### Stabilité des salles par catégorie")
    category_switches = p["category_switches"]
    mixed_rooms = p["mixed_category_rooms"]
    if not category_switches and not mixed_rooms:
        st.success("Chaque salle reste dédiée à une seule catégorie pendant tout l’événement.")
    else:
        if mixed_rooms:
            with st.expander(
                f"Salles partagées entre Secondaire 1 et Secondaire 2 · {len(mixed_rooms)}",
                expanded=False,
            ):
                for item in mixed_rooms:
                    st.write(f"• {item}")
        if category_switches:
            with st.expander(
                f"Changements de catégorie nécessaires · {len(category_switches)}",
                expanded=False,
            ):
                for item in category_switches:
                    st.write(f"• {item}")

    with st.expander("Contrôles détaillés", expanded=False):
        for item in validation.absolute_checks:
            st.write(f"✓ {item}")


def render_schedule_section(
    event: Event,
    teams: list[Team],
    current_result: ScheduleResult | None,
) -> ScheduleResult | None:
    errors = structural_errors(event, teams)

    with st.container(border=True):
        if errors:
            st.markdown("#### Planning en attente")
            st.caption(
                "Terminez la configuration à l’étape 3. Le bouton de génération se débloquera automatiquement."
            )
            return None

        action_col, info_col = st.columns([1.25, 2.75])
        with action_col:
            button_label = (
                "Générer le planning" if current_result is None else "Recalculer le planning"
            )
            if st.button(
                button_label,
                type="primary",
                use_container_width=True,
            ):
                try:
                    with st.spinner("Construction du planning optimal…"):
                        current_result = generate_schedule(event, teams, time_limit=30.0)
                    st.success("Planning généré avec succès.")
                except (ValueError, OptimizationError) as exc:
                    st.error(str(exc))
                    return None
        with info_col:
            if current_result is None:
                st.markdown("**Prêt à générer**")
                st.caption(
                    "Le solveur cherche d’abord le minimum de sessions, puis optimise les rencontres et la stabilité des salles."
                )
            else:
                st.markdown("**Planning à jour**")
                st.caption(
                    "Modifiez un paramètre ci-dessus si nécessaire, puis utilisez « Recalculer le planning »."
                )

    if current_result is None:
        return None

    summary = current_result.summary
    switches = len(current_result.preference_metrics["category_switches"])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sessions", summary.sessions)
    m2.metric("Salles disponibles", event.number_of_rooms)
    m3.metric("Débats", len(current_result.debates))
    m4.metric("Changements S1 ↔ S2", switches)

    planning_tab, quality_tab = st.tabs(["Planning", "Vérification"])
    with planning_tab:
        st.markdown("#### Planning par session")
        st.caption("Choisissez une session pour voir immédiatement la répartition des salles.")
        _render_session_cards(current_result, event.number_of_rooms)
        with st.expander("Afficher la vue tableau complète", expanded=False):
            _render_table(current_result)

    with quality_tab:
        _render_quality(current_result, event, teams)
        with st.expander("Informations techniques du solveur", expanded=False):
            st.write(f"Statut : {summary.status}")
            st.write(f"Moteur : {summary.backend}")
            st.write(f"Borne inférieure de sessions : {summary.lower_bound_sessions}")
            if summary.mip_gap is not None:
                st.write(f"MIP gap : {summary.mip_gap}")

    return current_result

```

## `src/models.py`

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

QUESTION_1 = "Question 1"
QUESTION_2 = "Question 2"
QUESTIONS = (QUESTION_1, QUESTION_2)


@dataclass(slots=True)
class Event:
    id: str
    name: str
    categories: list[str]
    number_of_rooms: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class School:
    id: str
    event_id: str
    name: str
    category: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Team:
    id: str
    event_id: str
    school_id: str
    school_name: str
    category: str
    label: str
    participant_1: str = ""
    participant_2: str = ""

    @property
    def display_name(self) -> str:
        return f"{self.school_name} – Équipe {self.label}"

    def participant_name(self, index: int) -> str:
        if index == 1:
            return self.participant_1.strip() or "Participant 1"
        if index == 2:
            return self.participant_2.strip() or "Participant 2"
        raise ValueError("Participant index must be 1 or 2.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ParticipantRole:
    participant_index: int
    participant_name: str
    side: str
    position: int

    @property
    def role_name(self) -> str:
        return f"{self.side} {self.position}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Debate:
    session: int
    room: int
    category: str
    question: str
    pro_team_id: str
    con_team_id: str
    pro_team_name: str
    con_team_name: str
    pro_roles: list[ParticipantRole] = field(default_factory=list)
    con_roles: list[ParticipantRole] = field(default_factory=list)

    def team_ids(self) -> tuple[str, str]:
        return self.pro_team_id, self.con_team_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "session": self.session,
            "room": self.room,
            "category": self.category,
            "question": self.question,
            "pro_team_id": self.pro_team_id,
            "con_team_id": self.con_team_id,
            "pro_team_name": self.pro_team_name,
            "con_team_name": self.con_team_name,
            "pro_roles": [r.to_dict() for r in self.pro_roles],
            "con_roles": [r.to_dict() for r in self.con_roles],
        }


@dataclass(slots=True)
class SolverSummary:
    sessions: int
    lower_bound_sessions: int
    objective_value: float
    status: str
    mip_gap: float | None = None
    backend: str = "SciPy MILP / HiGHS"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ScheduleResult:
    debates: list[Debate]
    summary: SolverSummary
    preference_metrics: dict[str, Any] = field(default_factory=dict)

```

## `src/optimizer.py`

```python
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

from .models import (
    Debate,
    Event,
    ParticipantRole,
    QUESTIONS,
    ScheduleResult,
    SolverSummary,
    Team,
)
from .validation import preference_analysis, structural_errors, validate_schedule


class OptimizationError(RuntimeError):
    pass


@dataclass(slots=True)
class _SolveBundle:
    result: object
    edges: list[tuple[int, int, int]]
    x_vars: dict[tuple[int, int, int], int]
    y_vars: dict[tuple[int, int, int, int], int]
    pro_vars: dict[tuple[int, int], int]


class _MilpBuilder:
    def __init__(self) -> None:
        self.c: list[float] = []
        self.lb: list[float] = []
        self.ub: list[float] = []
        self.integrality: list[int] = []
        self.rows: list[dict[int, float]] = []
        self.row_lb: list[float] = []
        self.row_ub: list[float] = []

    def var(
        self,
        *,
        cost: float = 0.0,
        lb: float = 0.0,
        ub: float = 1.0,
        integer: bool = True,
    ) -> int:
        idx = len(self.c)
        self.c.append(float(cost))
        self.lb.append(float(lb))
        self.ub.append(float(ub))
        self.integrality.append(1 if integer else 0)
        return idx

    def constraint(
        self,
        coeffs: dict[int, float] | Iterable[tuple[int, float]],
        *,
        lb: float = -np.inf,
        ub: float = np.inf,
    ) -> None:
        row = dict(coeffs)
        self.rows.append(row)
        self.row_lb.append(float(lb))
        self.row_ub.append(float(ub))

    def solve(self, *, time_limit: float) -> object:
        n_vars = len(self.c)
        if self.rows:
            rr: list[int] = []
            cc: list[int] = []
            vv: list[float] = []
            for r, row in enumerate(self.rows):
                for c, value in row.items():
                    if value:
                        rr.append(r)
                        cc.append(c)
                        vv.append(value)
            matrix = coo_matrix((vv, (rr, cc)), shape=(len(self.rows), n_vars)).tocsr()
            constraints = LinearConstraint(
                matrix,
                np.asarray(self.row_lb, dtype=float),
                np.asarray(self.row_ub, dtype=float),
            )
        else:
            constraints = None

        return milp(
            c=np.asarray(self.c, dtype=float),
            integrality=np.asarray(self.integrality, dtype=np.int8),
            bounds=Bounds(np.asarray(self.lb), np.asarray(self.ub)),
            constraints=constraints,
            options={
                "time_limit": float(time_limit),
                "mip_rel_gap": 0.0,
                "presolve": True,
            },
        )


def theoretical_min_sessions(number_of_teams: int, number_of_rooms: int) -> int:
    if number_of_teams <= 0 or number_of_rooms <= 0:
        return 0
    return max(2, math.ceil(number_of_teams / number_of_rooms))


def _candidate_edges(teams: list[Team]) -> list[tuple[int, int, int]]:
    by_category: dict[str, list[int]] = defaultdict(list)
    for i, team in enumerate(teams):
        by_category[team.category].append(i)

    edges: list[tuple[int, int, int]] = []
    for q in range(2):
        for indices in by_category.values():
            for pos, i in enumerate(indices):
                for j in indices[pos + 1 :]:
                    edges.append((q, i, j))
    return edges


def _weights(teams: list[Team]) -> tuple[int, int, int]:
    # Dynamic dominating weights: one violation at a higher level is always
    # more expensive than the theoretical maximum of all lower levels.
    n = max(1, len(teams))
    low_max = 2 * n  # same-label debates + Question-1-after-Question-2 teams
    strong_weight = low_max + 1
    strong_max = n * strong_weight
    very_strong_weight = strong_max + low_max + 1
    return very_strong_weight, strong_weight, 1


def _build_pairing_model(
    teams: list[Team],
    rooms: int,
    sessions: int,
    *,
    with_soft_objective: bool,
) -> tuple[_MilpBuilder, _SolveBundle]:
    builder = _MilpBuilder()
    edges = _candidate_edges(teams)
    x: dict[tuple[int, int, int], int] = {}
    y: dict[tuple[int, int, int, int], int] = {}
    pro: dict[tuple[int, int], int] = {}

    very_strong, strong, low = _weights(teams)

    # Pair-selection variables.
    for edge in edges:
        q, i, j = edge
        direct_cost = 0.0
        if with_soft_objective:
            if teams[i].school_id == teams[j].school_id:
                direct_cost += very_strong
            if teams[i].label.strip().casefold() == teams[j].label.strip().casefold():
                direct_cost += low
        x[edge] = builder.var(cost=direct_cost)
        for s in range(1, sessions + 1):
            y[(q, i, j, s)] = builder.var()

    # Every team debates exactly once on each question.
    incident_by_team_question: dict[tuple[int, int], list[tuple[int, int, int]]] = defaultdict(list)
    for edge in edges:
        q, i, j = edge
        incident_by_team_question[(i, q)].append(edge)
        incident_by_team_question[(j, q)].append(edge)

    for i in range(len(teams)):
        for q in range(2):
            coeffs = {x[e]: 1.0 for e in incident_by_team_question[(i, q)]}
            builder.constraint(coeffs, lb=1.0, ub=1.0)

    # Each selected debate is assigned to exactly one session.
    for edge in edges:
        q, i, j = edge
        coeffs = {y[(q, i, j, s)]: 1.0 for s in range(1, sessions + 1)}
        coeffs[x[edge]] = -1.0
        builder.constraint(coeffs, lb=0.0, ub=0.0)

    # A team cannot debate twice in the same session.
    for i in range(len(teams)):
        for s in range(1, sessions + 1):
            coeffs: dict[int, float] = {}
            for q in range(2):
                for e in incident_by_team_question[(i, q)]:
                    _, a, b = e
                    coeffs[y[(q, a, b, s)]] = 1.0
            builder.constraint(coeffs, ub=1.0)

    # Session capacity induced by the number of rooms.
    for s in range(1, sessions + 1):
        coeffs = {y[(q, i, j, s)]: 1.0 for q, i, j in edges}
        builder.constraint(coeffs, ub=float(rooms))

    # Side variables. For a selected edge, exactly one endpoint is POUR.
    for i in range(len(teams)):
        for q in range(2):
            pro[(i, q)] = builder.var()

    for edge in edges:
        q, i, j = edge
        # pro_i + pro_j >= x
        builder.constraint(
            {pro[(i, q)]: 1.0, pro[(j, q)]: 1.0, x[edge]: -1.0},
            lb=0.0,
        )
        # pro_i + pro_j <= 2 - x
        builder.constraint(
            {pro[(i, q)]: 1.0, pro[(j, q)]: 1.0, x[edge]: 1.0},
            ub=2.0,
        )

    if with_soft_objective:
        # Repeated opponent across Question 1 and Question 2.
        edge_lookup = {(q, i, j): x[(q, i, j)] for q, i, j in edges}
        unordered_pairs = sorted({(i, j) for _, i, j in edges})
        for i, j in unordered_pairs:
            if (0, i, j) in edge_lookup and (1, i, j) in edge_lookup:
                repeat = builder.var(cost=very_strong)
                builder.constraint(
                    {
                        repeat: 1.0,
                        edge_lookup[(0, i, j)]: -1.0,
                        edge_lookup[(1, i, j)]: -1.0,
                    },
                    lb=-1.0,
                )

        # Same side twice.
        for i in range(len(teams)):
            same_side = builder.var(cost=very_strong)
            # same_side >= p0 + p1 - 1
            builder.constraint(
                {same_side: 1.0, pro[(i, 0)]: -1.0, pro[(i, 1)]: -1.0},
                lb=-1.0,
            )
            # same_side >= 1 - p0 - p1
            builder.constraint(
                {same_side: 1.0, pro[(i, 0)]: 1.0, pro[(i, 1)]: 1.0},
                lb=1.0,
            )

        # Repeated school pair. Penalize only repetitions beyond the first.
        school_pair_edges: dict[tuple[str, str], list[int]] = defaultdict(list)
        for q, i, j in edges:
            if teams[i].school_id == teams[j].school_id:
                continue
            key = tuple(sorted((teams[i].school_id, teams[j].school_id)))
            school_pair_edges[key].append(x[(q, i, j)])

        for vars_for_pair in school_pair_edges.values():
            if len(vars_for_pair) <= 1:
                continue
            excess = builder.var(cost=strong, ub=float(len(vars_for_pair)), integer=True)
            coeffs = {excess: 1.0}
            for var in vars_for_pair:
                coeffs[var] = coeffs.get(var, 0.0) - 1.0
            builder.constraint(coeffs, lb=-1.0)

        # Prefer Question 1 before Question 2 for each team.
        big_m = max(1, sessions - 1)
        for i in range(len(teams)):
            q1_after_q2 = builder.var(cost=low)
            coeffs: dict[int, float] = {q1_after_q2: -float(big_m)}
            for e in incident_by_team_question[(i, 0)]:
                q, a, b = e
                for s in range(1, sessions + 1):
                    coeffs[y[(q, a, b, s)]] = coeffs.get(y[(q, a, b, s)], 0.0) + float(s)
            for e in incident_by_team_question[(i, 1)]:
                q, a, b = e
                for s in range(1, sessions + 1):
                    coeffs[y[(q, a, b, s)]] = coeffs.get(y[(q, a, b, s)], 0.0) - float(s)
            builder.constraint(coeffs, ub=0.0)

    bundle = _SolveBundle(
        result=None,
        edges=edges,
        x_vars=x,
        y_vars=y,
        pro_vars=pro,
    )
    return builder, bundle


def _status_name(status: int) -> str:
    return {
        0: "optimal",
        1: "limite de temps/itérations avec solution réalisable",
        2: "infaisable",
        3: "non borné",
        4: "erreur numérique ou autre erreur du solveur",
    }.get(int(status), f"statut {status}")


def _find_min_sessions(
    teams: list[Team], rooms: int, *, time_limit: float
) -> tuple[int, int]:
    lower = theoretical_min_sessions(len(teams), rooms)
    upper = len(teams)  # one debate per session is always enough structurally

    for sessions in range(lower, upper + 1):
        builder, _ = _build_pairing_model(
            teams, rooms, sessions, with_soft_objective=False
        )
        result = builder.solve(time_limit=time_limit)
        if getattr(result, "x", None) is not None:
            return sessions, lower
        if int(result.status) == 2:
            continue
        raise OptimizationError(
            "Le solveur n’a pas pu démontrer la faisabilité ou l’infaisabilité avec "
            f"{sessions} session(s) : {_status_name(result.status)}."
        )

    raise OptimizationError(
        "Aucun planning respectant toutes les contraintes absolues n’a pu être trouvé."
    )


def _solve_pairings(
    teams: list[Team], rooms: int, sessions: int, *, time_limit: float
) -> _SolveBundle:
    builder, bundle = _build_pairing_model(
        teams, rooms, sessions, with_soft_objective=True
    )
    result = builder.solve(time_limit=time_limit)
    if getattr(result, "x", None) is None:
        raise OptimizationError(
            "Une configuration structurellement faisable a été identifiée, mais le solveur "
            "n’a pas produit de solution optimisée dans la limite autorisée."
        )
    bundle.result = result
    return bundle


def _extract_debates_without_rooms(
    teams: list[Team], bundle: _SolveBundle, sessions: int
) -> list[Debate]:
    values = np.asarray(bundle.result.x)
    debates: list[Debate] = []

    for q, i, j in bundle.edges:
        if values[bundle.x_vars[(q, i, j)]] < 0.5:
            continue

        chosen_session = None
        for s in range(1, sessions + 1):
            if values[bundle.y_vars[(q, i, j, s)]] > 0.5:
                chosen_session = s
                break
        if chosen_session is None:
            raise OptimizationError("Débat sélectionné sans session associée.")

        i_is_pro = values[bundle.pro_vars[(i, q)]] > 0.5
        pro_team = teams[i] if i_is_pro else teams[j]
        con_team = teams[j] if i_is_pro else teams[i]
        debates.append(
            Debate(
                session=chosen_session,
                room=0,
                category=teams[i].category,
                question=QUESTIONS[q],
                pro_team_id=pro_team.id,
                con_team_id=con_team.id,
                pro_team_name=pro_team.display_name,
                con_team_name=con_team.display_name,
            )
        )

    return sorted(debates, key=lambda d: (d.session, d.category, d.question, d.pro_team_name))


def _assign_sessions_and_rooms_exact(
    teams: list[Team],
    debates: list[Debate],
    rooms: int,
    sessions: int,
    *,
    time_limit: float,
) -> None:
    """Jointly optimize sessions and rooms for the already chosen debates.

    Pairings and POUR/CONTRE sides are fixed by the first MILP. This second
    exact MILP is deliberately room-centric: it may move a fixed debate to a
    different session so that category-dedicated room blocks can remain stable.
    """
    builder = _MilpBuilder()

    # slot[d, s, r] = 1 iff debate d is held in session s, room r.
    slot: dict[tuple[int, int, int], int] = {}
    for d_idx in range(len(debates)):
        for session in range(1, sessions + 1):
            for room in range(1, rooms + 1):
                slot[(d_idx, session, room)] = builder.var()

    # Every debate occupies exactly one session/room slot.
    for d_idx in range(len(debates)):
        builder.constraint(
            {
                slot[(d_idx, session, room)]: 1.0
                for session in range(1, sessions + 1)
                for room in range(1, rooms + 1)
            },
            lb=1.0,
            ub=1.0,
        )

    # A room hosts at most one debate per session.
    for session in range(1, sessions + 1):
        for room in range(1, rooms + 1):
            builder.constraint(
                {
                    slot[(d_idx, session, room)]: 1.0
                    for d_idx in range(len(debates))
                },
                ub=1.0,
            )

    # A team cannot debate twice in the same session.
    team_debates: dict[str, list[int]] = defaultdict(list)
    for d_idx, d in enumerate(debates):
        team_debates[d.pro_team_id].append(d_idx)
        team_debates[d.con_team_id].append(d_idx)

    for d_indices in team_debates.values():
        for session in range(1, sessions + 1):
            coeffs: dict[int, float] = {}
            for d_idx in d_indices:
                for room in range(1, rooms + 1):
                    coeffs[slot[(d_idx, session, room)]] = 1.0
            builder.constraint(coeffs, ub=1.0)

    categories = sorted({d.category for d in debates})

    # ------------------------------------------------------------------
    # Strict objective hierarchy for room stability.
    # Questions deliberately do not influence room assignment: a room using
    # both Question 1 and Question 2 is normal and expected.
    # ------------------------------------------------------------------
    lower_total = 0

    # Lowest tier: a team ideally changes room between its two debates.
    max_same_room = len(teams)
    team_room_weight = lower_total + 1
    lower_total += max_same_room * team_room_weight

    # Then: Question 1 should precede Question 2 for each team.
    max_q_order = len(teams)
    q_order_weight = lower_total + 1
    lower_total += max_q_order * q_order_weight

    # Then: spatial zoning. Early room numbers belong preferably to the first
    # category (Secondaire 1), later room numbers to the second category.
    max_zone_distance = len(debates) * max(0, rooms - 1)
    zone_weight = lower_total + 1
    lower_total += max_zone_distance * zone_weight

    # Then: once a mixed room has moved from an earlier category to a later
    # category, do not move it back. Penalizing chronological category
    # inversions makes each mixed room monotone (S1 ... S1, then S2 ... S2),
    # so an unavoidable shared room normally changes category only once.
    category_pairs = len(categories) * max(0, len(categories) - 1) // 2
    max_inversions = rooms * category_pairs * sessions * max(0, sessions - 1) // 2
    inversion_weight = lower_total + 1
    lower_total += max_inversions * inversion_weight

    # Highest tier: minimize the number of rooms that ever host more than one
    # category. One fewer mixed room dominates every possible lower-tier gain.
    mixed_room_weight = lower_total + 1

    # Exact category activity by room/session.
    use_category_session: dict[tuple[str, int, int], int] = {}
    for category in categories:
        matching_debates = [
            d_idx for d_idx, d in enumerate(debates) if d.category == category
        ]
        for room in range(1, rooms + 1):
            for session in range(1, sessions + 1):
                use = builder.var()
                use_category_session[(category, room, session)] = use
                coeffs = {use: 1.0}
                for d_idx in matching_debates:
                    coeffs[slot[(d_idx, session, room)]] = -1.0
                builder.constraint(coeffs, lb=0.0, ub=0.0)

    # Category use over the full event.
    use_category: dict[tuple[str, int], int] = {}
    for category in categories:
        for room in range(1, rooms + 1):
            use = builder.var()
            use_category[(category, room)] = use
            for session in range(1, sessions + 1):
                builder.constraint(
                    {
                        use: 1.0,
                        use_category_session[(category, room, session)]: -1.0,
                    },
                    lb=0.0,
                )

    # Highest priority: number of mixed-category rooms.
    if len(categories) > 1:
        for room in range(1, rooms + 1):
            mixed = builder.var(cost=mixed_room_weight)
            for c1_idx, category_a in enumerate(categories):
                for category_b in categories[c1_idx + 1 :]:
                    builder.constraint(
                        {
                            mixed: 1.0,
                            use_category[(category_a, room)]: -1.0,
                            use_category[(category_b, room)]: -1.0,
                        },
                        lb=-1.0,
                    )

    # Second priority: forbid unnecessary back-and-forth category movement in
    # a mixed room. Categories are ordered naturally: Secondaire 1 before
    # Secondaire 2. A later category followed by an earlier category is an
    # inversion and receives a strong penalty.
    if len(categories) > 1:
        for room in range(1, rooms + 1):
            for later_idx in range(1, len(categories)):
                later_category = categories[later_idx]
                for earlier_idx in range(later_idx):
                    earlier_category = categories[earlier_idx]
                    for early_session in range(1, sessions):
                        for late_session in range(early_session + 1, sessions + 1):
                            inversion = builder.var(cost=inversion_weight)
                            builder.constraint(
                                {
                                    inversion: 1.0,
                                    use_category_session[(later_category, room, early_session)]: -1.0,
                                    use_category_session[(earlier_category, room, late_session)]: -1.0,
                                },
                                lb=-1.0,
                            )

    # Third priority: stable spatial zones. With S1/S2 this pulls S1 toward
    # room 1 and S2 toward the highest room number. If both categories need a
    # shared room, it naturally tends to be a boundary/middle room.
    if len(categories) > 1 and rooms > 1:
        last_category_index = len(categories) - 1
        for category_index, category in enumerate(categories):
            ideal_position = category_index * (rooms - 1) / last_category_index
            for room in range(1, rooms + 1):
                distance = abs((room - 1) - ideal_position)
                if distance == 0:
                    continue
                for session in range(1, sessions + 1):
                    builder.c[use_category_session[(category, room, session)]] += (
                        zone_weight * distance
                    )

    # Fourth priority: Question 1 before Question 2 for each team. Pairings are
    # already fixed, so this only influences the chronological placement.
    debate_question_index = {
        d_idx: 0 if d.question == QUESTIONS[0] else 1
        for d_idx, d in enumerate(debates)
    }
    big_m = max(1, sessions - 1)
    for team_id, d_indices in team_debates.items():
        if len(d_indices) != 2:
            continue
        q1_indices = [d for d in d_indices if debate_question_index[d] == 0]
        q2_indices = [d for d in d_indices if debate_question_index[d] == 1]
        if len(q1_indices) != 1 or len(q2_indices) != 1:
            continue
        q1_idx, q2_idx = q1_indices[0], q2_indices[0]
        q1_after_q2 = builder.var(cost=q_order_weight)
        coeffs: dict[int, float] = {q1_after_q2: -float(big_m)}
        for session in range(1, sessions + 1):
            for room in range(1, rooms + 1):
                coeffs[slot[(q1_idx, session, room)]] = float(session)
                coeffs[slot[(q2_idx, session, room)]] = -float(session)
        builder.constraint(coeffs, ub=0.0)

    # Fifth priority: a team should change rooms between its two debates, but
    # never at the cost of avoidable category mixing or extra category changes.
    for d_indices in team_debates.values():
        if len(d_indices) != 2:
            continue
        a, b = d_indices
        for room in range(1, rooms + 1):
            use_a = builder.var()
            use_b = builder.var()
            builder.constraint(
                {
                    use_a: 1.0,
                    **{
                        slot[(a, session, room)]: -1.0
                        for session in range(1, sessions + 1)
                    },
                },
                lb=0.0,
                ub=0.0,
            )
            builder.constraint(
                {
                    use_b: 1.0,
                    **{
                        slot[(b, session, room)]: -1.0
                        for session in range(1, sessions + 1)
                    },
                },
                lb=0.0,
                ub=0.0,
            )
            same_room = builder.var(cost=team_room_weight)
            builder.constraint(
                {same_room: 1.0, use_a: -1.0, use_b: -1.0},
                lb=-1.0,
            )

    result = builder.solve(time_limit=time_limit)
    if getattr(result, "x", None) is None:
        raise OptimizationError(
            "Impossible d’affecter conjointement les débats aux sessions et aux salles."
        )

    values = np.asarray(result.x)
    for d_idx, debate in enumerate(debates):
        chosen = [
            (session, room)
            for session in range(1, sessions + 1)
            for room in range(1, rooms + 1)
            if values[slot[(d_idx, session, room)]] > 0.5
        ]
        if len(chosen) != 1:
            raise OptimizationError(
                "Affectation de session/salle incohérente produite par le solveur."
            )
        debate.session, debate.room = chosen[0]

    debates.sort(key=lambda d: (d.session, d.room))

def _assign_participant_roles(teams: list[Team], debates: list[Debate]) -> None:
    by_id = {t.id: t for t in teams}
    team_debates: dict[str, list[Debate]] = defaultdict(list)
    for debate in debates:
        team_debates[debate.pro_team_id].append(debate)
        team_debates[debate.con_team_id].append(debate)

    for team_id, ds in team_debates.items():
        team = by_id[team_id]
        ordered = sorted(ds, key=lambda d: (d.session, d.room))
        for appearance, debate in enumerate(ordered):
            if appearance == 0:
                p1_pos, p2_pos = 1, 2
            else:
                p1_pos, p2_pos = 2, 1

            side = "POUR" if debate.pro_team_id == team_id else "CONTRE"
            roles = [
                ParticipantRole(1, team.participant_name(1), side, p1_pos),
                ParticipantRole(2, team.participant_name(2), side, p2_pos),
            ]
            roles.sort(key=lambda role: role.position)
            if side == "POUR":
                debate.pro_roles = roles
            else:
                debate.con_roles = roles


def generate_schedule(
    event: Event,
    teams: list[Team],
    *,
    time_limit: float = 30.0,
) -> ScheduleResult:
    errors = structural_errors(event, teams)
    if errors:
        raise ValueError("\n".join(errors))

    sessions, lower_bound = _find_min_sessions(
        teams, event.number_of_rooms, time_limit=time_limit
    )
    bundle = _solve_pairings(
        teams, event.number_of_rooms, sessions, time_limit=time_limit
    )
    debates = _extract_debates_without_rooms(teams, bundle, sessions)
    _assign_sessions_and_rooms_exact(
        teams,
        debates,
        event.number_of_rooms,
        sessions,
        time_limit=time_limit,
    )
    _assign_participant_roles(teams, debates)

    report = validate_schedule(event, teams, debates)
    if not report.valid:
        raise OptimizationError(
            "La validation indépendante a rejeté le planning :\n- "
            + "\n- ".join(report.errors)
        )

    result = bundle.result
    gap = getattr(result, "mip_gap", None)
    status = _status_name(result.status)
    summary = SolverSummary(
        sessions=sessions,
        lower_bound_sessions=lower_bound,
        objective_value=float(result.fun) if result.fun is not None else 0.0,
        status=status,
        mip_gap=float(gap) if gap is not None and np.isfinite(gap) else None,
    )
    return ScheduleResult(
        debates=debates,
        summary=summary,
        preference_metrics=preference_analysis(teams, debates),
    )

```

## `src/validation.py`

```python
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .models import Debate, Event, QUESTIONS, Team


@dataclass(slots=True)
class ValidationReport:
    valid: bool
    absolute_checks: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    successes: list[str] = field(default_factory=list)



def structural_errors(event: Event, teams: list[Team]) -> list[str]:
    errors: list[str] = []

    if event.number_of_rooms < 1:
        errors.append("Le nombre de salles doit être supérieur ou égal à 1.")
    if not event.categories:
        errors.append("Au moins une catégorie doit être sélectionnée.")
    if not teams:
        errors.append("Aucune équipe n’a été ajoutée.")

    known_categories = set(event.categories)
    unknown = sorted({t.category for t in teams if t.category not in known_categories})
    if unknown:
        errors.append(
            "Certaines équipes appartiennent à une catégorie absente de l’événement : "
            + ", ".join(unknown)
            + "."
        )

    counts = Counter(t.category for t in teams)
    for category in event.categories:
        n = counts.get(category, 0)
        if n < 2:
            plural = "équipe" if n == 1 else "équipes"
            errors.append(
                f"La catégorie {category} compte {n} {plural}. Il faut au moins 2 équipes pour organiser un débat."
            )
        elif n % 2:
            errors.append(
                f"La catégorie {category} compte {n} équipes. Le nombre d’équipes doit être pair afin que "
                "chaque équipe puisse participer à deux débats en face-à-face."
            )

    duplicate_ids = [team_id for team_id, n in Counter(t.id for t in teams).items() if n > 1]
    if duplicate_ids:
        errors.append("Des identifiants d’équipes sont dupliqués dans les données.")

    return errors



def validate_schedule(event: Event, teams: list[Team], debates: list[Debate]) -> ValidationReport:
    report = ValidationReport(valid=True)
    by_id = {t.id: t for t in teams}
    team_debates: dict[str, list[Debate]] = defaultdict(list)

    expected_debates = len(teams)
    if len(debates) != expected_debates:
        report.errors.append(
            f"Le planning contient {len(debates)} débats au lieu de {expected_debates}."
        )

    room_session_seen: set[tuple[int, int]] = set()
    for d in debates:
        if d.question not in QUESTIONS:
            report.errors.append(
                f"Session {d.session}, salle {d.room} : question inconnue « {d.question} »."
            )
        if d.pro_team_id == d.con_team_id:
            report.errors.append(
                f"Session {d.session}, salle {d.room} : une équipe ne peut pas débattre contre elle-même."
            )
        if d.pro_team_id not in by_id or d.con_team_id not in by_id:
            report.errors.append(
                f"Session {d.session}, salle {d.room} : une équipe référencée n’existe pas."
            )
            continue

        pro = by_id[d.pro_team_id]
        con = by_id[d.con_team_id]
        if pro.category != con.category or d.category != pro.category:
            report.errors.append(
                f"Session {d.session}, salle {d.room} : catégories incohérentes entre les deux équipes."
            )
        if not 1 <= d.room <= event.number_of_rooms:
            report.errors.append(
                f"Session {d.session} : la salle {d.room} est hors de la plage 1–{event.number_of_rooms}."
            )
        key = (d.session, d.room)
        if key in room_session_seen:
            report.errors.append(
                f"Session {d.session}, salle {d.room} : plusieurs débats sont planifiés simultanément."
            )
        room_session_seen.add(key)
        team_debates[d.pro_team_id].append(d)
        team_debates[d.con_team_id].append(d)

    for team in teams:
        ds = sorted(team_debates.get(team.id, []), key=lambda d: (d.session, d.room))
        if len(ds) != 2:
            report.errors.append(
                f"{team.display_name} participe à {len(ds)} débat(s) au lieu de 2."
            )
            continue

        sessions = [d.session for d in ds]
        if len(set(sessions)) != 2:
            report.errors.append(
                f"{team.display_name} participe à deux débats dans la même session."
            )

        questions = Counter(d.question for d in ds)
        if questions.get(QUESTIONS[0], 0) != 1 or questions.get(QUESTIONS[1], 0) != 1:
            report.errors.append(
                f"{team.display_name} ne débat pas exactement une fois sur chaque question."
            )

        positions: dict[int, list[int]] = {1: [], 2: []}
        for d in ds:
            roles = d.pro_roles if d.pro_team_id == team.id else d.con_roles
            if len(roles) != 2:
                report.errors.append(
                    f"{team.display_name} n’a pas exactement deux rôles individuels au débat de la session {d.session}."
                )
                continue
            for role in roles:
                positions.setdefault(role.participant_index, []).append(role.position)

        if positions.get(1) != [1, 2] or positions.get(2) != [2, 1]:
            report.errors.append(
                f"La rotation 1 ↔ 2 n’est pas respectée pour {team.display_name}."
            )

    report.valid = not report.errors
    if report.valid:
        report.absolute_checks.extend(
            [
                "Toutes les équipes participent à exactement deux débats.",
                "Toutes les équipes débattent exactement une fois sur Question 1 et une fois sur Question 2.",
                "Aucune équipe ne participe à deux débats dans la même session.",
                "Tous les débats opposent deux équipes de la même catégorie sur la même question.",
                "Chaque salle accueille au maximum un débat par session.",
                "Toutes les rotations individuelles 1 ↔ 2 sont respectées.",
            ]
        )
    return report



def preference_analysis(teams: list[Team], debates: list[Debate]) -> dict[str, list[str] | int]:
    by_id = {t.id: t for t in teams}
    team_opponents: dict[str, list[str]] = defaultdict(list)
    team_sides: dict[str, list[str]] = defaultdict(list)
    team_rooms: dict[str, list[int]] = defaultdict(list)
    school_pairs: Counter[tuple[str, str]] = Counter()
    same_school: list[str] = []
    same_label: list[str] = []

    for d in debates:
        a = by_id[d.pro_team_id]
        b = by_id[d.con_team_id]
        team_opponents[a.id].append(b.id)
        team_opponents[b.id].append(a.id)
        team_sides[a.id].append("POUR")
        team_sides[b.id].append("CONTRE")
        team_rooms[a.id].append(d.room)
        team_rooms[b.id].append(d.room)

        if a.school_id == b.school_id:
            same_school.append(
                f"Session {d.session}, salle {d.room} : {a.display_name} contre {b.display_name}."
            )
        else:
            pair = tuple(sorted((a.school_name, b.school_name)))
            school_pairs[pair] += 1

        if a.label.strip().casefold() == b.label.strip().casefold():
            same_label.append(
                f"Session {d.session}, salle {d.room} : {a.display_name} contre {b.display_name}."
            )

    repeated_opponents: list[str] = []
    seen_pairs: set[tuple[str, str]] = set()
    for team_id, opponents in team_opponents.items():
        for opponent_id, count in Counter(opponents).items():
            pair = tuple(sorted((team_id, opponent_id)))
            if count > 1 and pair not in seen_pairs:
                seen_pairs.add(pair)
                repeated_opponents.append(
                    f"{by_id[pair[0]].display_name} et {by_id[pair[1]].display_name} s’affrontent deux fois."
                )

    same_side = [
        by_id[team_id].display_name
        for team_id, sides in team_sides.items()
        if len(sides) == 2 and sides[0] == sides[1]
    ]
    same_room = [
        by_id[team_id].display_name
        for team_id, rooms in team_rooms.items()
        if len(rooms) == 2 and rooms[0] == rooms[1]
    ]
    repeated_school_pairs = [
        f"{a} ↔ {b} : {count} confrontations."
        for (a, b), count in sorted(school_pairs.items())
        if count > 1
    ]

    room_categories: dict[int, set[str]] = defaultdict(set)
    for d in debates:
        room_categories[d.room].add(d.category)

    mixed_category_rooms = [
        f"Salle {room} accueille plusieurs catégories : {', '.join(sorted(cats))}."
        for room, cats in sorted(room_categories.items())
        if len(cats) > 1
    ]

    # Count category changes between consecutive uses of the same room. Empty
    # sessions do not reset the room: S1 -> empty -> S2 is still one category
    # change from an operational point of view.
    debates_by_room: dict[int, list[Debate]] = defaultdict(list)
    for d in debates:
        debates_by_room[d.room].append(d)

    category_switches: list[str] = []
    for room, room_debates in sorted(debates_by_room.items()):
        ordered = sorted(room_debates, key=lambda d: d.session)
        for previous, current in zip(ordered, ordered[1:]):
            if previous.category != current.category:
                category_switches.append(
                    f"Salle {room} : {previous.category} (session {previous.session}) → "
                    f"{current.category} (session {current.session})."
                )

    return {
        "repeated_opponents": repeated_opponents,
        "same_school": same_school,
        "same_side": same_side,
        "repeated_school_pairs": repeated_school_pairs,
        "same_room": same_room,
        "same_label": same_label,
        "mixed_category_rooms": mixed_category_rooms,
        "category_switches": category_switches,
    }

```

## `src/database.py`

```python
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import Event, School, Team

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "app.db"


def _connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                categories_json TEXT NOT NULL,
                number_of_rooms INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS schools (
                id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS teams (
                id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                school_id TEXT NOT NULL,
                school_name TEXT NOT NULL,
                category TEXT NOT NULL,
                label TEXT NOT NULL,
                participant_1 TEXT NOT NULL DEFAULT '',
                participant_2 TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
                FOREIGN KEY(school_id) REFERENCES schools(id) ON DELETE CASCADE
            );
            """
        )


def save_event(
    event: Event,
    schools: list[School],
    teams: list[Team],
    db_path: Path = DB_PATH,
) -> None:
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO events(id, name, categories_json, number_of_rooms, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                categories_json=excluded.categories_json,
                number_of_rooms=excluded.number_of_rooms,
                updated_at=excluded.updated_at
            """,
            (
                event.id,
                event.name,
                json.dumps(event.categories, ensure_ascii=False),
                event.number_of_rooms,
                now,
            ),
        )
        conn.execute("DELETE FROM teams WHERE event_id = ?", (event.id,))
        conn.execute("DELETE FROM schools WHERE event_id = ?", (event.id,))
        conn.executemany(
            "INSERT INTO schools(id, event_id, name, category) VALUES (?, ?, ?, ?)",
            [(s.id, s.event_id, s.name, s.category) for s in schools],
        )
        conn.executemany(
            """
            INSERT INTO teams(
                id, event_id, school_id, school_name, category, label, participant_1, participant_2
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    t.id,
                    t.event_id,
                    t.school_id,
                    t.school_name,
                    t.category,
                    t.label,
                    t.participant_1,
                    t.participant_2,
                )
                for t in teams
            ],
        )


def list_events(db_path: Path = DB_PATH) -> list[dict[str, str]]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, name, updated_at FROM events ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def load_event(
    event_id: str, db_path: Path = DB_PATH
) -> tuple[Event, list[School], list[Team]]:
    init_db(db_path)
    with _connect(db_path) as conn:
        event_row = conn.execute(
            "SELECT * FROM events WHERE id = ?", (event_id,)
        ).fetchone()
        if event_row is None:
            raise KeyError(f"Événement introuvable : {event_id}")
        school_rows = conn.execute(
            "SELECT * FROM schools WHERE event_id = ? ORDER BY name, category", (event_id,)
        ).fetchall()
        team_rows = conn.execute(
            "SELECT * FROM teams WHERE event_id = ? ORDER BY school_name, label", (event_id,)
        ).fetchall()

    event = Event(
        id=event_row["id"],
        name=event_row["name"],
        categories=json.loads(event_row["categories_json"]),
        number_of_rooms=int(event_row["number_of_rooms"]),
    )
    schools = [
        School(
            id=row["id"],
            event_id=row["event_id"],
            name=row["name"],
            category=row["category"],
        )
        for row in school_rows
    ]
    teams = [
        Team(
            id=row["id"],
            event_id=row["event_id"],
            school_id=row["school_id"],
            school_name=row["school_name"],
            category=row["category"],
            label=row["label"],
            participant_1=row["participant_1"],
            participant_2=row["participant_2"],
        )
        for row in team_rows
    ]
    return event, schools, teams


def delete_event(event_id: str, db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))

```

## `src/utils.py`

```python
from __future__ import annotations

import string
import uuid
from collections import Counter

from .models import School, Team


def new_id() -> str:
    return str(uuid.uuid4())


def team_label(index: int) -> str:
    """A, B, ..., Z, AA, AB, ..."""
    if index < 0:
        raise ValueError("index must be non-negative")
    label = ""
    n = index + 1
    while n:
        n, rem = divmod(n - 1, 26)
        label = string.ascii_uppercase[rem] + label
    return label


def add_school_with_teams(
    *,
    event_id: str,
    school_name: str,
    category: str,
    number_of_teams: int,
) -> tuple[School, list[Team]]:
    school = School(
        id=new_id(),
        event_id=event_id,
        name=school_name.strip(),
        category=category,
    )
    teams = [
        Team(
            id=new_id(),
            event_id=event_id,
            school_id=school.id,
            school_name=school.name,
            category=category,
            label=team_label(i),
        )
        for i in range(number_of_teams)
    ]
    return school, teams


def category_counts(teams: list[Team]) -> Counter[str]:
    return Counter(team.category for team in teams)

```

## `tests/test_optimizer.py`

```python
from __future__ import annotations

import pytest

from src.models import Event, School, Team
from src.optimizer import generate_schedule, theoretical_min_sessions
from src.validation import structural_errors, validate_schedule


def make_case(
    category_schools: dict[str, list[int]], rooms: int
) -> tuple[Event, list[School], list[Team]]:
    event = Event(
        id="event-test",
        name="Finale test",
        categories=list(category_schools),
        number_of_rooms=rooms,
    )
    schools: list[School] = []
    teams: list[Team] = []
    for c_idx, (category, school_sizes) in enumerate(category_schools.items()):
        for s_idx, size in enumerate(school_sizes):
            school_id = f"school-{c_idx}-{s_idx}"
            school_name = f"École {c_idx + 1}.{s_idx + 1}"
            schools.append(School(school_id, event.id, school_name, category))
            for t_idx in range(size):
                teams.append(
                    Team(
                        id=f"team-{c_idx}-{s_idx}-{t_idx}",
                        event_id=event.id,
                        school_id=school_id,
                        school_name=school_name,
                        category=category,
                        label=chr(ord("A") + t_idx),
                        participant_1=f"P1-{c_idx}-{s_idx}-{t_idx}",
                        participant_2=f"P2-{c_idx}-{s_idx}-{t_idx}",
                    )
                )
    return event, schools, teams


def assert_valid(event: Event, teams: list[Team], result) -> None:
    report = validate_schedule(event, teams, result.debates)
    assert report.valid, report.errors
    assert len(result.debates) == len(teams)
    assert result.summary.sessions == theoretical_min_sessions(
        len(teams), event.number_of_rooms
    )


def test_single_category_8_teams() -> None:
    event, _, teams = make_case({"Secondaire 1": [2, 2, 2, 2]}, rooms=3)
    result = generate_schedule(event, teams, time_limit=10)
    assert_valid(event, teams, result)
    assert result.summary.sessions == 3
    assert result.preference_metrics["repeated_opponents"] == []
    assert result.preference_metrics["same_school"] == []
    assert result.preference_metrics["same_side"] == []


def test_single_category_10_teams_with_few_rooms() -> None:
    event, _, teams = make_case({"Secondaire 1": [2, 2, 2, 2, 2]}, rooms=2)
    result = generate_schedule(event, teams, time_limit=10)
    assert_valid(event, teams, result)
    assert result.summary.sessions == 5


def test_two_categories_simultaneously() -> None:
    event, _, teams = make_case(
        {"Secondaire 1": [2, 2, 2], "Secondaire 2": [2, 2]}, rooms=3
    )
    result = generate_schedule(event, teams, time_limit=10)
    assert_valid(event, teams, result)
    categories = {d.category for d in result.debates}
    assert categories == {"Secondaire 1", "Secondaire 2"}


def test_multiple_teams_from_same_school_avoids_internal_when_possible() -> None:
    event, _, teams = make_case({"Secondaire 1": [4, 2, 2]}, rooms=4)
    result = generate_schedule(event, teams, time_limit=10)
    assert_valid(event, teams, result)
    assert result.preference_metrics["same_school"] == []


def test_odd_team_count_is_blocked_before_optimization() -> None:
    event, _, teams = make_case({"Secondaire 1": [3, 2, 2, 2]}, rooms=4)
    errors = structural_errors(event, teams)
    assert any("9 équipes" in error and "pair" in error for error in errors)
    with pytest.raises(ValueError):
        generate_schedule(event, teams, time_limit=5)


def test_preferences_can_be_reported_when_unavoidable() -> None:
    event, _, teams = make_case({"Secondaire 1": [4]}, rooms=2)
    result = generate_schedule(event, teams, time_limit=10)
    assert_valid(event, teams, result)
    assert len(result.preference_metrics["same_school"]) == 4


def test_rooms_stay_category_dedicated_when_possible() -> None:
    event, _, teams = make_case(
        {"Secondaire 1": [2, 2, 2], "Secondaire 2": [2, 2]}, rooms=3
    )
    result = generate_schedule(event, teams, time_limit=10)
    assert_valid(event, teams, result)
    assert result.preference_metrics["mixed_category_rooms"] == []
    assert result.preference_metrics["category_switches"] == []

    room_categories: dict[int, set[str]] = {}
    for debate in result.debates:
        room_categories.setdefault(debate.room, set()).add(debate.category)
    assert room_categories[1] == {"Secondaire 1"}
    assert room_categories[3] == {"Secondaire 2"}


def test_unavoidable_shared_room_changes_category_only_once() -> None:
    event, _, teams = make_case(
        {
            "Secondaire 1": [2, 2, 2, 2],
            "Secondaire 2": [2, 2, 2, 2],
        },
        rooms=3,
    )
    result = generate_schedule(event, teams, time_limit=15)
    assert_valid(event, teams, result)

    # With 8 teams in each category and only 3 rooms, one boundary room must
    # be shared. The optimized layout keeps room 1 dedicated to S1, room 3
    # dedicated to S2, and makes room 2 switch at most once from S1 to S2.
    mixed_rooms = {
        debate.room
        for debate in result.debates
        if len({d.category for d in result.debates if d.room == debate.room}) > 1
    }
    assert mixed_rooms == {2}
    assert len(result.preference_metrics["category_switches"]) == 1

    room_2_categories = [
        d.category
        for d in sorted(result.debates, key=lambda d: (d.session, d.room))
        if d.room == 2
    ]
    seen_secondary_2 = False
    for category in room_2_categories:
        if category == "Secondaire 2":
            seen_secondary_2 = True
        if seen_secondary_2:
            assert category != "Secondaire 1"


def test_room_question_mix_is_not_reported_as_problem() -> None:
    event, _, teams = make_case({"Secondaire 1": [2, 2, 2, 2]}, rooms=2)
    result = generate_schedule(event, teams, time_limit=10)
    assert_valid(event, teams, result)
    assert "mixed_question_rooms" not in result.preference_metrics

```

## `requirements.txt`

```text
streamlit>=1.41,<2
pandas>=2.2,<3
scipy>=1.13,<2
numpy>=1.26,<3
pytest>=8,<9

```
