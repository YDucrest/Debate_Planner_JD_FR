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
                if st.button("Sauvegarder", width="stretch"):
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
                    if st.button("Charger", width="stretch"):
                        loaded_event, loaded_schools, loaded_teams = load_event(
                            options[selected_label]
                        )
                        return loaded_event, loaded_schools, loaded_teams, True, True
                else:
                    st.caption("Aucun événement sauvegardé pour le moment.")

    changed = previous_name != event.name or previous_categories != event.categories
    return event, schools, teams, False, changed
