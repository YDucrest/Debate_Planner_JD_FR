from __future__ import annotations

from collections import Counter
from html import escape

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
            info_col, delete_col = st.columns([8.5, 1])
            with info_col:
                st.markdown(f"**{school.name}**")
                st.caption(
                    f"{len(school_teams)} équipe(s) · {_team_labels(school_teams)}"
                )
            with delete_col:
                if st.button(
                    "✕",
                    key=f"delete_school_{school.id}",
                    help=f"Retirer {school.name}",
                    use_container_width=True,
                ):
                    schools[:] = [s for s in schools if s.id != school.id]
                    teams[:] = [t for t in teams if t.school_id != school.id]
                    st.session_state.schedule_result = None
                    st.rerun()


def _render_participant_inputs(teams: list[Team]) -> bool:
    """Render simple participant fields grouped by school."""
    changed = False
    schools: dict[tuple[str, str], list[Team]] = {}
    for team in teams:
        schools.setdefault((team.category, team.school_name), []).append(team)

    st.markdown("#### Noms des participant·es")
    st.caption(
        "Optionnel. Ouvrez un établissement puis saisissez simplement les deux personnes de chaque équipe."
    )

    for (category, school_name), school_teams in schools.items():
        filled = sum(
            1
            for team in school_teams
            if team.participant_1.strip() and team.participant_2.strip()
        )
        with st.expander(
            f"{school_name} · {category} · {filled}/{len(school_teams)} équipe(s) complétée(s)",
            expanded=False,
        ):
            header_team, header_p1, header_p2 = st.columns([0.9, 2.25, 2.25])
            with header_team:
                st.markdown('<div class="participant-grid-heading">Équipe</div>', unsafe_allow_html=True)
            with header_p1:
                st.markdown('<div class="participant-grid-heading">Participant·e 1</div>', unsafe_allow_html=True)
            with header_p2:
                st.markdown('<div class="participant-grid-heading">Participant·e 2</div>', unsafe_allow_html=True)

            for team in sorted(school_teams, key=lambda item: item.label):
                label_col, p1_col, p2_col = st.columns(
                    [0.9, 2.25, 2.25],
                    vertical_alignment="center",
                )
                with label_col:
                    st.markdown(
                        f'<div class="participant-team-label">Équipe {escape(team.label)}</div>',
                        unsafe_allow_html=True,
                    )
                with p1_col:
                    p1 = st.text_input(
                        f"Participant·e 1 — équipe {team.label}",
                        value=team.participant_1,
                        placeholder="Prénom Nom",
                        key=f"participant_1_{team.id}",
                        label_visibility="collapsed",
                    )
                with p2_col:
                    p2 = st.text_input(
                        f"Participant·e 2 — équipe {team.label}",
                        value=team.participant_2,
                        placeholder="Prénom Nom",
                        key=f"participant_2_{team.id}",
                        label_visibility="collapsed",
                    )

                if p1 != team.participant_1 or p2 != team.participant_2:
                    team.participant_1 = p1
                    team.participant_2 = p2
                    changed = True

    return changed


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
        title_col, option_col = st.columns([2.7, 1.3])
        with title_col:
            st.markdown("#### Établissements inscrits")
            st.caption("Vérifiez la liste avant de passer aux salles.")
        with option_col:
            detailed_mode = st.toggle(
                "Saisir les participant·es",
                value=detailed_mode,
                help="Optionnel : permet d’afficher ensuite la rotation des rôles avec les noms.",
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
            st.divider()
            changed = _render_participant_inputs(teams) or changed

    return schools, teams, detailed_mode, changed
