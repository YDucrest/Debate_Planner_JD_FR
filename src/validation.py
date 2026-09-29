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
