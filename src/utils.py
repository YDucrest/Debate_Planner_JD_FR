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
