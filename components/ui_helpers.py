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

        p, .stCaption { color: var(--yes-muted); }
        label,
        [data-testid="stWidgetLabel"] p {
            color: var(--yes-ink) !important;
            font-weight: 650 !important;
        }

        /* Readability: keep form text dark on light surfaces */
        input, textarea,
        div[data-baseweb="select"] *,
        div[data-baseweb="input"] *,
        div[data-testid="stNumberInput"] * {
            color: var(--yes-ink) !important;
        }
        input::placeholder, textarea::placeholder {
            color: #80949B !important;
            opacity: 1 !important;
        }
        input:disabled, textarea:disabled {
            -webkit-text-fill-color: #526A73 !important;
            color: #526A73 !important;
            opacity: 1 !important;
        }

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
            border-color: #BFD2D7 !important;
            background: #FFFFFF !important;
        }
        div[data-baseweb="input"] > div:focus-within,
        div[data-baseweb="select"] > div:focus-within {
            border-color: var(--yes-cyan) !important;
            box-shadow: 0 0 0 2px rgba(0,160,174,.10) !important;
        }

        /* Buttons: only YES colors, with strong text contrast. */
        div.stButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            border-radius: 11px;
            min-height: 2.75rem;
            font-weight: 750;
            border: 1px solid #BFD4D9;
            background: #FFFFFF;
            color: var(--yes-petrol) !important;
            transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
        }
        div.stButton > button p,
        div.stButton > button span,
        div[data-testid="stFormSubmitButton"] > button p,
        div[data-testid="stFormSubmitButton"] > button span {
            color: inherit !important;
            font-weight: inherit !important;
        }
        div.stButton > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            border-color: var(--yes-cyan);
            background: var(--yes-soft-2);
            color: var(--yes-ink) !important;
        }
        div.stButton > button:focus-visible,
        div[data-testid="stFormSubmitButton"] > button:focus-visible {
            outline: 3px solid rgba(0,160,174,.18) !important;
            outline-offset: 2px;
        }
        div.stButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, var(--yes-petrol), var(--yes-cyan));
            border: 0;
            color: #FFFFFF !important;
            box-shadow: 0 7px 16px rgba(0,160,174,.16);
        }
        div.stButton > button[kind="primary"] p,
        div.stButton > button[kind="primary"] span,
        div[data-testid="stFormSubmitButton"] > button[kind="primary"] p,
        div[data-testid="stFormSubmitButton"] > button[kind="primary"] span {
            color: #FFFFFF !important;
        }
        div.stButton > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
            background: linear-gradient(135deg, var(--yes-ink), var(--yes-cyan-dark));
            transform: translateY(-1px);
            box-shadow: 0 9px 20px rgba(0,160,174,.19);
        }
        div.stButton > button:disabled,
        div[data-testid="stFormSubmitButton"] > button:disabled {
            background: #EDF4F6 !important;
            border-color: var(--yes-border) !important;
            color: #607982 !important;
            opacity: 1 !important;
        }

        /* Alerts: all semantic states stay inside the YES palette. */
        div[data-testid="stAlert"] {
            border-radius: 12px;
            border: 1px solid #B8DFE3 !important;
            background: #F1FAFB !important;
            color: var(--yes-ink) !important;
        }
        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] div,
        div[data-testid="stAlert"] span {
            color: var(--yes-ink) !important;
        }
        div[data-testid="stAlert"] svg {
            color: var(--yes-cyan-dark) !important;
            fill: var(--yes-cyan-dark) !important;
        }
        [data-testid="stSpinner"] svg {
            color: var(--yes-cyan) !important;
        }

        /* Dropdowns and interactive options */
        div[data-baseweb="popover"],
        div[data-baseweb="menu"] {
            color: var(--yes-ink) !important;
        }
        div[role="option"] {
            color: var(--yes-ink) !important;
        }
        div[role="option"][aria-selected="true"],
        div[role="option"]:hover {
            background: var(--yes-soft) !important;
            color: var(--yes-ink) !important;
        }
        input[type="radio"], input[type="checkbox"] {
            accent-color: var(--yes-cyan) !important;
        }
        button[role="switch"][aria-checked="true"],
        div[role="switch"][aria-checked="true"] {
            background: var(--yes-cyan) !important;
        }

        /* Choice controls: selected states are subtle, not solid blocks. */
        div[role="radiogroup"] {
            gap: 6px;
        }
        div[role="radiogroup"] label {
            border: 1px solid var(--yes-border);
            background: #FFFFFF;
            border-radius: 10px;
            padding: 7px 10px;
            transition: background .12s ease, border-color .12s ease, box-shadow .12s ease;
        }
        div[role="radiogroup"] label:hover {
            background: var(--yes-soft-2);
            border-color: #B8D9DE;
        }
        div[role="radiogroup"] label:has(input:checked) {
            background: var(--yes-soft);
            border-color: var(--yes-cyan);
            box-shadow: inset 0 0 0 1px rgba(0,160,174,.10);
        }
        div[role="radiogroup"] label:has(input:checked) p,
        div[role="radiogroup"] label:has(input:checked) span {
            color: var(--yes-ink) !important;
            font-weight: 750 !important;
        }

        /* Tabs: discreet underline selection instead of a large turquoise panel. */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background: transparent;
            padding: 0 2px;
            border-bottom: 1px solid var(--yes-border);
            overflow-x: auto;
        }
        .stTabs [data-baseweb="tab"] {
            min-height: 2.65rem;
            border-radius: 8px 8px 0 0;
            padding-left: 14px;
            padding-right: 14px;
            color: var(--yes-muted) !important;
            font-weight: 680;
            white-space: nowrap;
            border-bottom: 3px solid transparent;
            background: transparent !important;
        }
        .stTabs [aria-selected="true"] {
            background: #FFFFFF !important;
            color: var(--yes-petrol) !important;
            border-bottom-color: var(--yes-cyan) !important;
            box-shadow: none !important;
        }
        .stTabs [aria-selected="true"] p,
        .stTabs [aria-selected="true"] span {
            color: var(--yes-petrol) !important;
            font-weight: 780 !important;
        }
        .stTabs [aria-selected="false"]:hover {
            background: var(--yes-soft-2) !important;
            color: var(--yes-ink) !important;
        }
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: var(--yes-cyan) !important;
            height: 2px !important;
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
            min-height: 205px;
            box-shadow: 0 5px 14px rgba(23,54,66,.035);
        }
        .debate-card.s1 { border-top: 4px solid var(--yes-cyan); }
        .debate-card.s2 { border-top: 4px solid var(--yes-petrol); }
        .debate-card.empty {
            background: #FAFCFC;
            border-style: dashed;
            min-height: 205px;
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
            font-weight:680;
            line-height:1.3;
            font-size:.88rem;
            overflow-wrap:anywhere;
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

        .participant-grid-heading {
            color: var(--yes-petrol);
            font-size: .74rem;
            font-weight: 800;
            letter-spacing: .025em;
            margin: 2px 0 5px 2px;
        }
        .participant-team-label {
            min-height: 2.75rem;
            display: flex;
            align-items: center;
            color: var(--yes-ink);
            font-weight: 800;
            background: var(--yes-soft-2);
            border: 1px solid var(--yes-border);
            border-radius: 10px;
            padding: 0 11px;
            box-sizing: border-box;
        }

        /* Complete schedule table */
        .schedule-table-shell {
            border: 1px solid var(--yes-border);
            border-radius: 15px;
            overflow: auto;
            background: #FFFFFF;
            box-shadow: 0 5px 18px rgba(23,54,66,.04);
        }
        .schedule-table {
            width: 100%;
            min-width: 900px;
            border-collapse: separate;
            border-spacing: 0;
            color: var(--yes-ink);
            font-size: .84rem;
        }
        .schedule-table thead th {
            position: sticky;
            top: 0;
            z-index: 1;
            background: #F2F8F9;
            color: var(--yes-petrol);
            text-align: left;
            font-size: .70rem;
            font-weight: 850;
            letter-spacing: .045em;
            text-transform: uppercase;
            padding: 11px 12px;
            border-bottom: 1px solid #D3E4E7;
            white-space: nowrap;
        }
        .schedule-table tbody td {
            padding: 11px 12px;
            vertical-align: top;
            border-bottom: 1px solid #E7F0F2;
            background: #FFFFFF;
        }
        .schedule-table tbody tr:last-child td {
            border-bottom: 0;
        }
        .schedule-table tbody tr:hover td {
            background: #F7FBFB;
        }
        .table-session,
        .table-room {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 34px;
            height: 28px;
            border-radius: 8px;
            font-weight: 820;
        }
        .table-session {
            background: var(--yes-soft);
            color: var(--yes-petrol);
        }
        .table-room {
            background: #EEF4F6;
            color: var(--yes-ink);
        }
        .table-question {
            color: var(--yes-ink);
            font-weight: 680;
            white-space: nowrap;
        }
        .table-team {
            color: var(--yes-ink);
            font-weight: 760;
            line-height: 1.25;
        }
        .table-role {
            color: var(--yes-muted);
            font-size: .73rem;
            line-height: 1.35;
            margin-top: 3px;
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
            st.image(str(logo), width="stretch")
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
