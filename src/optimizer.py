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

    # Keep occupancy front-loaded. Session labels are operational rather than
    # semantic, so an earlier session should never contain fewer debates than
    # the following one. This pushes spare rooms toward the end of the event.
    for session in range(1, sessions):
        coeffs: dict[int, float] = {}
        for d_idx in range(len(debates)):
            for room in range(1, rooms + 1):
                coeffs[slot[(d_idx, session, room)]] = 1.0
                coeffs[slot[(d_idx, session + 1, room)]] = -1.0
        builder.constraint(coeffs, lb=0.0)

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

    # Then: minimize the number of rooms that ever host more than one category.
    # This remains important, but it is deliberately below session compaction:
    # a mixed S1/S2 boundary room is preferable to leaving avoidable holes in
    # early sessions.
    mixed_room_weight = lower_total + 1
    max_mixed_rooms = rooms if len(categories) > 1 else 0
    lower_total += max_mixed_rooms * mixed_room_weight

    # Highest tier: compact debates into the earliest sessions. A one-unit
    # reduction in the summed session indices dominates every possible gain in
    # room-category stability and all lower tie-breakers.
    session_packing_weight = lower_total + 1
    for d_idx in range(len(debates)):
        for session in range(1, sessions + 1):
            if session == 1:
                continue
            for room in range(1, rooms + 1):
                builder.c[slot[(d_idx, session, room)]] += (
                    session_packing_weight * (session - 1)
                )

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

    # Next priority after session packing: number of mixed-category rooms.
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
