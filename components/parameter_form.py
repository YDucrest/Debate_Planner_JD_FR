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
