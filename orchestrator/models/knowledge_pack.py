"""Knowledge Pack schema models — shared contract §4.3."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class FormField(BaseModel):
    """A single form input field on a screen."""

    id: str
    label: str
    input_type: str = "text"  # text, number, date, dropdown, checkbox, etc.
    required: bool = False
    placeholder: Optional[str] = None


class DesignTokens(BaseModel):
    """Visual design information extracted for a screen."""

    dominant_colors: list[str] = Field(default_factory=list, description="Hex colour codes")
    background_color: Optional[str] = None
    foreground_color: Optional[str] = None
    font_styles: list[str] = Field(default_factory=list, description="Typography notes")
    spacing_pattern: Optional[str] = None
    component_types: list[str] = Field(default_factory=list)
    mode: Optional[str] = None  # "light" | "dark"
    tone: Optional[str] = None  # e.g. "professional", "playful"


class Screen(BaseModel):
    """One discovered screen in the knowledge pack."""

    id: str = Field(..., description="Stable logical screen ID")
    fingerprint: str = Field("", description="Canonical structural fingerprint")
    name: str = Field(..., description="Short human name for the screen")
    purpose: str = Field("", description="What this screen is for")
    screenshot_url: Optional[str] = Field(None, description="Path or URL to the screenshot")
    elements: list[dict[str, Any]] = Field(default_factory=list)
    forms: list[FormField] = Field(default_factory=list)
    design_tokens: DesignTokens = Field(default_factory=DesignTokens)


class Transition(BaseModel):
    """A navigation edge between two screens."""

    from_screen: str = Field(..., alias="from", description="Source screen ID")
    to_screen: str = Field(..., alias="to", description="Target screen ID")
    action: dict[str, Any] = Field(default_factory=dict, description="Action that caused the transition")

    model_config = {"populate_by_name": True}


class Journey(BaseModel):
    """A named sequence of transitions forming a user flow."""

    name: str
    steps: list[str] = Field(default_factory=list, description="Ordered list of screen IDs")


class GlobalDesignSystem(BaseModel):
    """Cross-screen aggregated design tokens."""

    color_palette: list[str] = Field(default_factory=list)
    spacing_values: list[str] = Field(default_factory=list)
    recurring_components: list[str] = Field(default_factory=list)
    typography_hierarchy: list[str] = Field(default_factory=list)
    tone: Optional[str] = None
    mode: Optional[str] = None


class ScanMetadata(BaseModel):
    """Statistics about the exploration run."""

    total_steps: int = 0
    screens_discovered: int = 0
    transitions_discovered: int = 0
    duplicates_merged: int = 0
    exploration_duration_seconds: float = 0.0
    pack_size_bytes: int = 0


class KnowledgePack(BaseModel):
    """Top-level knowledge pack — shared contract §4.3."""

    schema_version: str = "1.0"
    app_metadata: dict[str, Any] = Field(default_factory=dict)
    screens: list[Screen] = Field(default_factory=list)
    transitions: list[Transition] = Field(default_factory=list)
    journeys: list[Journey] = Field(default_factory=list)
    global_design_system: GlobalDesignSystem = Field(default_factory=GlobalDesignSystem)
    scan_metadata: ScanMetadata = Field(default_factory=ScanMetadata)
