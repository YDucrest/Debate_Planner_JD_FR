from __future__ import annotations

from collections import defaultdict
from html import escape

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
                # Always keep a 3-column grid so the final card never stretches
                # across the full page when the room count is not a multiple of 3.
                columns = st.columns(3)
                for idx, room in enumerate(chunk):
                    with columns[idx]:
                        st.markdown(
                            _debate_card(room, by_room.get(room)),
                            unsafe_allow_html=True,
                        )


def _render_table(result: ScheduleResult) -> None:
    rows: list[str] = []
    for d in sorted(result.debates, key=lambda item: (item.session, item.room)):
        category_class = "s1" if d.category == "Secondaire 1" else "s2"
        pro_roles = escape(_roles_text(d, "POUR"))
        con_roles = escape(_roles_text(d, "CONTRE"))
        rows.append(
            f'<tr>'
            f'<td><span class="table-session">S{d.session}</span></td>'
            f'<td><span class="table-room">{d.room}</span></td>'
            f'<td><span class="yes-category-chip {category_class}">{escape(d.category)}</span></td>'
            f'<td><span class="table-question">{escape(d.question)}</span></td>'
            f'<td><div class="table-team">{escape(d.pro_team_name)}</div>'
            f'<div class="table-role">{pro_roles}</div></td>'
            f'<td><div class="table-team">{escape(d.con_team_name)}</div>'
            f'<div class="table-role">{con_roles}</div></td>'
            f'</tr>'
        )

    table_html = (
        '<div class="schedule-table-shell">'
        '<table class="schedule-table">'
        '<thead><tr>'
        '<th>Session</th>'
        '<th>Salle</th>'
        '<th>Catégorie</th>'
        '<th>Question</th>'
        '<th>POUR</th>'
        '<th>CONTRE</th>'
        '</tr></thead>'
        '<tbody>'
        + "".join(rows)
        + '</tbody></table></div>'
    )

    # Use Streamlit's native HTML renderer instead of Markdown.
    # Markdown can reinterpret indented <tr> blocks as plain text, which is
    # why the complete view previously displayed raw HTML tags.
    st.html(table_html)


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
