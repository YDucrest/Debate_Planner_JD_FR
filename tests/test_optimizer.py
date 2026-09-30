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


def test_rooms_follow_s1_low_s2_high_zones_in_each_session() -> None:
    event, _, teams = make_case(
        {"Secondaire 1": [2, 2, 2], "Secondaire 2": [2, 2]}, rooms=3
    )
    result = generate_schedule(event, teams, time_limit=15)
    assert_valid(event, teams, result)

    for session in range(1, result.summary.sessions + 1):
        session_debates = [d for d in result.debates if d.session == session]
        s1_rooms = sorted(d.room for d in session_debates if d.category == "Secondaire 1")
        s2_rooms = sorted(d.room for d in session_debates if d.category == "Secondaire 2")

        if s1_rooms:
            assert s1_rooms == list(range(1, len(s1_rooms) + 1))
        if s2_rooms:
            assert s2_rooms == list(
                range(event.number_of_rooms - len(s2_rooms) + 1, event.number_of_rooms + 1)
            )
        if s1_rooms and s2_rooms:
            assert max(s1_rooms) < min(s2_rooms)


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


def test_school_pair_is_not_repeated_when_avoidable() -> None:
    event, _, teams = make_case(
        {"Secondaire 1": [2, 2, 2, 2, 2]},
        rooms=3,
    )
    result = generate_schedule(event, teams, time_limit=15)
    assert_valid(event, teams, result)
    assert result.preference_metrics["repeated_school_pairs"] == []


def test_spare_rooms_are_pushed_to_the_last_session() -> None:
    event, _, teams = make_case(
        {"Secondaire 1": [2, 2, 2, 2, 2]},
        rooms=3,
    )
    result = generate_schedule(event, teams, time_limit=15)
    assert_valid(event, teams, result)

    occupancy = [
        sum(1 for debate in result.debates if debate.session == session)
        for session in range(1, result.summary.sessions + 1)
    ]
    assert occupancy == [3, 3, 3, 1]


def test_categories_use_opposite_room_edges_with_middle_gaps_allowed() -> None:
    event, _, teams = make_case(
        {
            "Secondaire 1": [2, 2],
            "Secondaire 2": [2, 2],
        },
        rooms=5,
    )
    result = generate_schedule(event, teams, time_limit=20)
    assert_valid(event, teams, result)

    # Four debates can run in parallel with eight teams, so one physical room
    # is structurally unused. It should remain between the category zones:
    # S1 in rooms 1-2 and S2 in rooms 4-5, not rooms 1-4.
    for session in range(1, result.summary.sessions + 1):
        session_debates = [d for d in result.debates if d.session == session]
        assert sorted(d.room for d in session_debates) == [1, 2, 4, 5]
        assert sorted(
            d.room for d in session_debates if d.category == "Secondaire 1"
        ) == [1, 2]
        assert sorted(
            d.room for d in session_debates if d.category == "Secondaire 2"
        ) == [4, 5]


def test_all_avoidable_empty_rooms_are_in_final_session() -> None:
    event, _, teams = make_case(
        {
            "Secondaire 1": [2, 2, 2, 2, 2],
            "Secondaire 2": [2, 2, 2],
        },
        rooms=5,
    )
    result = generate_schedule(event, teams, time_limit=20)
    assert_valid(event, teams, result)

    occupancy = [
        sum(1 for debate in result.debates if debate.session == session)
        for session in range(1, result.summary.sessions + 1)
    ]
    assert occupancy[:-1] == [event.number_of_rooms] * (len(occupancy) - 1)
    assert occupancy[-1] <= event.number_of_rooms


def test_category_switches_are_minimized_across_sessions() -> None:
    event, _, teams = make_case(
        {
            "Secondaire 1": [2, 2, 2, 2],
            "Secondaire 2": [2, 2, 2, 2],
        },
        rooms=5,
    )
    result = generate_schedule(event, teams, time_limit=20)
    assert_valid(event, teams, result)

    # Count actual S1/S2 changes between consecutive occupied sessions in each
    # room. The compact 5/5/5/1 layout requires category sharing, but the
    # optimizer must keep the moving boundary as stable as possible.
    actual_switches = 0
    for room in range(1, event.number_of_rooms + 1):
        by_session = {
            d.session: d.category for d in result.debates if d.room == room
        }
        for session in range(1, result.summary.sessions):
            a = by_session.get(session)
            b = by_session.get(session + 1)
            if a is not None and b is not None and a != b:
                actual_switches += 1

    # The analysis helper should report the same number of switches, and this
    # symmetric case can be arranged with only one category change overall.
    assert actual_switches == len(result.preference_metrics["category_switches"])
    assert actual_switches <= 1


def test_both_categories_run_in_parallel_whenever_capacity_allows() -> None:
    event, _, teams = make_case(
        {
            "Secondaire 1": [2, 2, 2, 2],
            "Secondaire 2": [2, 2, 2, 2],
        },
        rooms=5,
    )
    result = generate_schedule(event, teams, time_limit=25)
    assert_valid(event, teams, result)

    occupancy = {
        session: [d for d in result.debates if d.session == session]
        for session in range(1, result.summary.sessions + 1)
    }
    # The front-loaded target is 5/5/5/1. In every session that can physically
    # host at least two debates, both levels should be represented.
    for session, debates in occupancy.items():
        if len(debates) >= 2:
            assert {d.category for d in debates} == {"Secondaire 1", "Secondaire 2"}


def test_room_switch_count_includes_empty_gaps_and_is_kept_low() -> None:
    event, _, teams = make_case(
        {
            "Secondaire 1": [2, 2, 2],
            "Secondaire 2": [2, 2, 2],
        },
        rooms=5,
    )
    result = generate_schedule(event, teams, time_limit=25)
    assert_valid(event, teams, result)

    # This case requires the S1/S2 boundary to move, but the optimized layout
    # can do so with a single operational room-category change overall. The
    # independent analysis counts changes even when a room is empty in between.
    assert len(result.preference_metrics["category_switches"]) <= 1
