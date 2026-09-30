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


def _front_loaded_session_targets(
    number_of_teams: int, number_of_rooms: int, sessions: int
) -> list[int]:
    """Return the required number of debates in each session.

    There are exactly ``number_of_teams`` debates in the event because every
    team debates twice. A session can never host more than half the teams, even
    if more physical rooms are available. Within that structural limit, all
    avoidable empty room slots are pushed to the final session.
    """
    if sessions <= 0:
        return []
    max_parallel = min(number_of_rooms, number_of_teams // 2)
    if max_parallel <= 0:
        return [0] * sessions

    remaining = number_of_teams
    targets: list[int] = []
    for _ in range(sessions):
        debates_now = min(max_parallel, remaining)
        targets.append(debates_now)
        remaining -= debates_now
    return targets


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


def _weights(teams: list[Team]) -> tuple[int, int, int, int]:
    # Dynamic dominating weights. The hierarchy is deliberately explicit:
    # 1) avoid debates inside the same school whenever possible;
    # 2) avoid repeating the same school pairing (and especially the exact
    #    same opponent) before optimizing side alternation;
    # 3) alternate POUR/CONTRE;
    # 4) keep same-label and chronological preferences as tie-breakers.
    n = max(1, len(teams))

    low_weight = 1
    low_max = 2 * n  # same-label debates + Question-1-after-Question-2 teams

    side_weight = low_max + 1
    side_max = n * side_weight

    school_repeat_weight = low_max + side_max + 1
    # At most n school-pair excesses and n exact-opponent repetitions need to
    # be dominated by the top tier.
    school_repeat_max = 2 * n * school_repeat_weight

    same_school_weight = low_max + side_max + school_repeat_max + 1
    return same_school_weight, school_repeat_weight, side_weight, low_weight


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

    same_school_weight, school_repeat_weight, side_weight, low = _weights(teams)

    # Pair-selection variables.
    for edge in edges:
        q, i, j = edge
        direct_cost = 0.0
        if with_soft_objective:
            if teams[i].school_id == teams[j].school_id:
                direct_cost += same_school_weight
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

    # Front-load the programme: all avoidable spare-room capacity belongs to
    # the final session. This is a hard operational rule, not a preference.
    session_targets = _front_loaded_session_targets(len(teams), rooms, sessions)
    for s in range(1, sessions + 1):
        coeffs = {y[(q, i, j, s)]: 1.0 for q, i, j in edges}
        target = float(session_targets[s - 1])
        builder.constraint(coeffs, lb=target, ub=target)

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
                repeat = builder.var(cost=school_repeat_weight)
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
            same_side = builder.var(cost=side_weight)
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
            excess = builder.var(
                cost=school_repeat_weight,
                ub=float(len(vars_for_pair)),
                integer=True,
            )
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
    exact MILP may move a fixed debate to another session. Its operational
    priorities are deliberately explicit:

    1. keep both categories active in as many sessions as possible;
    2. minimize real S1/S2 changes in each room, including across an empty gap;
    3. keep category sharing concentrated on as few rooms as possible;
    4. anchor Secondary 1 to the first rooms and Secondary 2 to the last rooms;
    5. keep all avoidable spare capacity in the final session.

    Importantly, occupied rooms do *not* have to be consecutive. With five
    rooms, one S1 debate and one S2 debate should naturally use rooms 1 and 5,
    rather than rooms 1 and 2. This greatly improves room-category stability.
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

    # Hard session occupancy targets. The first sessions contain as many
    # debates as structurally possible; all avoidable spare capacity is pushed
    # to the final session. Which physical room is left empty is deliberately
    # *not* fixed here, so category zones can remain stable.
    session_targets = _front_loaded_session_targets(len(teams), rooms, sessions)
    for session in range(1, sessions + 1):
        builder.constraint(
            {
                slot[(d_idx, session, room)]: 1.0
                for d_idx in range(len(debates))
                for room in range(1, rooms + 1)
            },
            lb=float(session_targets[session - 1]),
            ub=float(session_targets[session - 1]),
        )

    categories = sorted({d.category for d in debates})

    # ------------------------------------------------------------------
    # Strict lexicographic-style objective hierarchy through dominating
    # integer weights. Questions do not influence the choice of room.
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

    # Then: prefer S1 toward low room numbers and S2 toward high room numbers.
    max_zone_distance = len(debates) * max(0, rooms - 1)
    zone_weight = lower_total + 1
    lower_total += max_zone_distance * zone_weight

    # Then: avoid chronological reversals such as S2 -> ... -> S1 in one room.
    category_pairs = len(categories) * max(0, len(categories) - 1) // 2
    max_inversions = rooms * category_pairs * sessions * max(0, sessions - 1) // 2
    inversion_weight = lower_total + 1
    lower_total += max_inversions * inversion_weight

    # Then: concentrate unavoidable category sharing on as few rooms as possible.
    max_mixed_rooms = rooms if len(categories) > 1 else 0
    mixed_room_weight = lower_total + 1
    lower_total += max_mixed_rooms * mixed_room_weight

    # Then: minimize actual category switches between two consecutive *uses* of
    # a room. Empty sessions do not hide a switch: S1 -> empty -> S2 counts as
    # one operational change, matching the independent analysis.
    max_category_switches = rooms * max(0, sessions - 1)
    category_switch_weight = lower_total + 1
    lower_total += max_category_switches * category_switch_weight

    # Highest tier: maximize category presence across the day. This prevents a
    # layout with all S1 debates first and all S2 debates later when the two
    # categories can run in parallel. One missing category/session dominates
    # every possible room-stability or tie-breaker gain below it.
    max_missing_category_sessions = len(categories) * sessions
    category_presence_weight = lower_total + 1
    lower_total += max_missing_category_sessions * category_presence_weight

    # Exact category activity by room/session.
    use_category_session: dict[tuple[str, int, int], int] = {}
    debates_by_category: dict[str, list[int]] = {
        category: [
            d_idx for d_idx, d in enumerate(debates) if d.category == category
        ]
        for category in categories
    }
    for category in categories:
        matching_debates = debates_by_category[category]
        for room in range(1, rooms + 1):
            for session in range(1, sessions + 1):
                use = builder.var()
                use_category_session[(category, room, session)] = use
                coeffs = {use: 1.0}
                for d_idx in matching_debates:
                    coeffs[slot[(d_idx, session, room)]] = -1.0
                builder.constraint(coeffs, lb=0.0, ub=0.0)

    # Category presence by session. ``active`` is exactly 1 iff at least one
    # debate of that category is scheduled in the session. We minimize the
    # complementary ``inactive`` variables at the highest objective tier.
    active_category_session: dict[tuple[str, int], int] = {}
    for category in categories:
        max_debates_in_session = max(1, len(debates_by_category[category]))
        for session in range(1, sessions + 1):
            active = builder.var()
            inactive = builder.var(cost=category_presence_weight)
            active_category_session[(category, session)] = active
            builder.constraint({active: 1.0, inactive: 1.0}, lb=1.0, ub=1.0)

            count_coeffs = {
                use_category_session[(category, room, session)]: 1.0
                for room in range(1, rooms + 1)
            }
            # active <= category debate count in the session
            coeffs = dict(count_coeffs)
            coeffs[active] = -1.0
            builder.constraint(coeffs, lb=0.0)
            # category debate count <= M * active
            coeffs = dict(count_coeffs)
            coeffs[active] = -float(max_debates_in_session)
            builder.constraint(coeffs, ub=0.0)

    # Spatial anchoring. With S1/S2, S1 grows from room 1 upward while S2 grows
    # from the highest room downward. Empty rooms may remain in the middle.
    # Example with five rooms and one debate per category: rooms 1 and 5.
    if len(categories) == 1:
        category = categories[0]
        for session in range(1, sessions + 1):
            for room in range(1, rooms):
                builder.constraint(
                    {
                        use_category_session[(category, room + 1, session)]: 1.0,
                        use_category_session[(category, room, session)]: -1.0,
                    },
                    ub=0.0,
                )
    elif len(categories) == 2:
        early_category, late_category = categories
        for session in range(1, sessions + 1):
            # S1/earlier category = prefix from room 1.
            for room in range(1, rooms):
                builder.constraint(
                    {
                        use_category_session[(early_category, room + 1, session)]: 1.0,
                        use_category_session[(early_category, room, session)]: -1.0,
                    },
                    ub=0.0,
                )
            # S2/later category = suffix toward the highest room.
            for room in range(1, rooms):
                builder.constraint(
                    {
                        use_category_session[(late_category, room, session)]: 1.0,
                        use_category_session[(late_category, room + 1, session)]: -1.0,
                    },
                    ub=0.0,
                )
    elif len(categories) > 2:
        # Defensive fallback for any future extra categories: retain strict
        # left-to-right category ordering, without assuming the current UI.
        for session in range(1, sessions + 1):
            for later_idx in range(1, len(categories)):
                later_category = categories[later_idx]
                for earlier_idx in range(later_idx):
                    earlier_category = categories[earlier_idx]
                    for low_room in range(1, rooms):
                        for high_room in range(low_room + 1, rooms + 1):
                            builder.constraint(
                                {
                                    use_category_session[(later_category, low_room, session)]: 1.0,
                                    use_category_session[(earlier_category, high_room, session)]: 1.0,
                                },
                                ub=1.0,
                            )

    # Exact category use over the full event (logical OR over sessions).
    use_category: dict[tuple[str, int], int] = {}
    for category in categories:
        for room in range(1, rooms + 1):
            use = builder.var()
            use_category[(category, room)] = use
            session_vars = [
                use_category_session[(category, room, session)]
                for session in range(1, sessions + 1)
            ]
            for session_var in session_vars:
                builder.constraint({use: 1.0, session_var: -1.0}, lb=0.0)
            coeffs = {use: 1.0}
            for session_var in session_vars:
                coeffs[session_var] = -1.0
            builder.constraint(coeffs, ub=0.0)

    # Count real category switches between consecutive uses of each room,
    # including across one or more empty sessions.
    if len(categories) > 1:
        for room in range(1, rooms + 1):
            for early_session in range(1, sessions):
                for late_session in range(early_session + 1, sessions + 1):
                    for category_a in categories:
                        for category_b in categories:
                            if category_a == category_b:
                                continue
                            switch = builder.var(cost=category_switch_weight)
                            coeffs: dict[int, float] = {
                                switch: 1.0,
                                use_category_session[(category_a, room, early_session)]: -1.0,
                                use_category_session[(category_b, room, late_session)]: -1.0,
                            }
                            # If any intermediate session uses this room, then
                            # (early, late) are not consecutive uses and this
                            # particular switch variable is not forced.
                            for middle_session in range(early_session + 1, late_session):
                                for middle_category in categories:
                                    middle_var = use_category_session[
                                        (middle_category, room, middle_session)
                                    ]
                                    coeffs[middle_var] = coeffs.get(middle_var, 0.0) + 1.0
                            builder.constraint(coeffs, lb=-1.0)

    # Minimize the number of rooms that ever host more than one category.
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

    # Avoid unnecessary chronological backtracking between categories in one
    # room (e.g. S2 in an early session followed by S1 later).
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

    # Stable spatial zones as a lower-level tie-breaker.
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

    # Question 1 before Question 2 for each team. Pairings are already fixed;
    # this only influences chronology.
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

    # A team should change rooms between its two debates when this does not
    # compromise the higher operational priorities above.
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
