from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

QUESTION_1 = "Question 1"
QUESTION_2 = "Question 2"
QUESTIONS = (QUESTION_1, QUESTION_2)


@dataclass(slots=True)
class Event:
    id: str
    name: str
    categories: list[str]
    number_of_rooms: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class School:
    id: str
    event_id: str
    name: str
    category: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Team:
    id: str
    event_id: str
    school_id: str
    school_name: str
    category: str
    label: str
    participant_1: str = ""
    participant_2: str = ""

    @property
    def display_name(self) -> str:
        return f"{self.school_name} – Équipe {self.label}"

    def participant_name(self, index: int) -> str:
        if index == 1:
            return self.participant_1.strip() or "Participant 1"
        if index == 2:
            return self.participant_2.strip() or "Participant 2"
        raise ValueError("Participant index must be 1 or 2.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ParticipantRole:
    participant_index: int
    participant_name: str
    side: str
    position: int

    @property
    def role_name(self) -> str:
        return f"{self.side} {self.position}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Debate:
    session: int
    room: int
    category: str
    question: str
    pro_team_id: str
    con_team_id: str
    pro_team_name: str
    con_team_name: str
    pro_roles: list[ParticipantRole] = field(default_factory=list)
    con_roles: list[ParticipantRole] = field(default_factory=list)

    def team_ids(self) -> tuple[str, str]:
        return self.pro_team_id, self.con_team_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "session": self.session,
            "room": self.room,
            "category": self.category,
            "question": self.question,
            "pro_team_id": self.pro_team_id,
            "con_team_id": self.con_team_id,
            "pro_team_name": self.pro_team_name,
            "con_team_name": self.con_team_name,
            "pro_roles": [r.to_dict() for r in self.pro_roles],
            "con_roles": [r.to_dict() for r in self.con_roles],
        }


@dataclass(slots=True)
class SolverSummary:
    sessions: int
    lower_bound_sessions: int
    objective_value: float
    status: str
    mip_gap: float | None = None
    backend: str = "SciPy MILP / HiGHS"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ScheduleResult:
    debates: list[Debate]
    summary: SolverSummary
    preference_metrics: dict[str, Any] = field(default_factory=dict)
