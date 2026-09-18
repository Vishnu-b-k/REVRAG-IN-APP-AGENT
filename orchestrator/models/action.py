"""Action / response models — what the backend sends back to Android."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Allowed action types — shared contract §4.2."""

    TAP = "tap"
    SCROLL = "scroll"
    TYPE_TEXT = "type_text"
    BACK = "back"
    NULL = "null"  # exploration complete / no action


class ScreenElement(BaseModel):
    """Structured element returned in the ingest-screen response."""

    id: str = Field(..., description="Unique element identifier for this session")
    role: str = Field(..., description="Semantic role: button, text_input, label, image, etc.")
    label: str = Field(..., description="Human-readable label")
    bounds: list[int] = Field(..., description="[x, y, w, h] bounds")
    actions: list[str] = Field(default_factory=list, description="Possible actions on this element")


class CandidateAction(BaseModel):
    """One possible action the model considered."""

    type: ActionType
    target_element_id: Optional[str] = None
    value: Optional[str] = None
    reason: str = ""
    confidence: float = Field(0.0, ge=0.0, le=1.0)


class NextAction(BaseModel):
    """The single selected action for Android to execute."""

    type: ActionType
    target_element_id: Optional[str] = None
    value: Optional[str] = None
    reason: str = ""
    confidence: float = Field(0.0, ge=0.0, le=1.0)


class IngestScreenResponse(BaseModel):
    """POST /ingest-screen response body — shared contract §4.1."""

    screen_id: str = Field(..., description="Logical screen identifier")
    state_id: str = Field(..., description="Unique state identifier for this observation")
    is_new_screen: bool = Field(..., description="True if this screen was not seen before")
    description: str = Field("", description="Natural-language description of the screen")
    elements: list[ScreenElement] = Field(default_factory=list)
    candidate_actions: list[CandidateAction] = Field(default_factory=list)
    next_action: NextAction
