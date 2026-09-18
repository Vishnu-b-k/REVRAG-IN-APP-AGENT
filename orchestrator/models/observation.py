"""Observation request models — what Android sends to the backend."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class UIElement(BaseModel):
    """Single node from the Android accessibility tree."""

    class_name: str = Field(..., description="Android widget class name")
    text: Optional[str] = Field(None, description="Visible text content")
    content_description: Optional[str] = Field(None, description="Accessibility content description")
    bounds: list[int] = Field(..., description="[left, top, right, bottom] pixel bounds")
    clickable: bool = False
    focusable: bool = False
    editable: bool = False
    enabled: bool = True
    selected: bool = False
    checked: Optional[bool] = None
    children: list["UIElement"] = Field(default_factory=list)


class UITree(BaseModel):
    """Full accessibility tree for one screen capture."""

    package_name: str = Field(..., description="App package name")
    activity_name: Optional[str] = Field(None, description="Current activity class")
    root: UIElement = Field(..., description="Root node of the UI tree")


class ObservationRequest(BaseModel):
    """POST /ingest-screen request body — shared contract §4.1."""

    session_id: str = Field(..., min_length=1, description="Exploration session identifier")
    step: int = Field(..., ge=0, description="Monotonic step counter")
    screenshot_b64: str = Field(..., min_length=1, description="Base64-encoded PNG screenshot")
    ui_tree: UITree = Field(..., description="Accessibility tree snapshot")
    previous_state_id: Optional[str] = Field(None, description="State ID from the prior step")
