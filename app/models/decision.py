from enum import Enum

from pydantic import BaseModel


class DecisionType(str, Enum):
    RESPOND = "respond"
    ASK = "ask"
    ESCALATE = "escalate"


class IncidentDecision(BaseModel):
    decision: DecisionType
    message: str
