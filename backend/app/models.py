from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

Transition = Literal["fade", "wipe", "zoom", "cut"]
ElementKind = Literal["headline", "body", "metric", "icon", "shape", "label"]
AnimationKind = Literal["rise", "scale", "drift", "pulse", "reveal", "none"]

class Element(BaseModel):
    id: str
    kind: ElementKind = "body"
    text: str = ""
    x: float = Field(default=50, ge=0, le=100)
    y: float = Field(default=50, ge=0, le=100)
    width: float = Field(default=60, ge=1, le=100)
    color: str = "#F8FAFC"
    font_size: int = Field(default=32, ge=10, le=160)
    weight: int = Field(default=500, ge=300, le=900)
    animation: AnimationKind = "rise"
    delay: float = Field(default=0, ge=0, le=20)
    accent: str | None = None

    @field_validator("color", "accent")
    @classmethod
    def valid_color(cls, value):
        if value is not None and not __import__("re").fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError("Colors must be six-digit hex values")
        return value

    @model_validator(mode="after")
    def stay_inside_canvas(self):
        if self.x-self.width/2 < 0 or self.x+self.width/2 > 100:
            raise ValueError("Element exceeds horizontal canvas bounds")
        return self

class Scene(BaseModel):
    id: str
    title: str
    duration: float = Field(ge=1, le=60)
    description: str
    narration: str = ""
    transition: Transition = "fade"
    background: str = "#0B1020"
    elements: list[Element] = Field(min_length=1, max_length=12)

    @field_validator("background")
    @classmethod
    def valid_background(cls, value):
        if not __import__("re").fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError("Background must be a six-digit hex value")
        return value

class ProjectSpec(BaseModel):
    title: str
    prompt: str
    language: str = "en"
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = "16:9"
    fps: int = Field(default=30, ge=24, le=60)
    width: int = 1920
    height: int = 1080
    palette: list[str] = Field(default_factory=lambda: ["#0B1020", "#7C5CFC", "#21D4A7"])
    scenes: list[Scene] = Field(min_length=2, max_length=12)

    @model_validator(mode="after")
    def validate_timeline(self):
        expected = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}[self.aspect_ratio]
        self.width, self.height = expected
        total = sum(scene.duration for scene in self.scenes)
        if total > 120:
            raise ValueError("Total duration cannot exceed 120 seconds")
        return self

    @property
    def duration(self) -> float:
        return sum(scene.duration for scene in self.scenes)

class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=8, max_length=4000)
    duration: int = Field(default=20, ge=8, le=120)
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = "16:9"

class EditRequest(BaseModel):
    project_id: str
    command: str = Field(min_length=3, max_length=1000)
    selected_element_id: str | None = None
