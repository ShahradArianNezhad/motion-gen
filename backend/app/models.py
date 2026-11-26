from __future__ import annotations
import re
from typing import Literal
from pydantic import BaseModel, Field, field_validator

HEX6 = re.compile(r"#[0-9a-fA-F]{6}")
LayerType = Literal["text", "image", "shape", "icon", "lottie", "video", "chart", "caption"]
AnimPreset = Literal[
    # Entrances
    "pop-bounce", "slide-in", "scale-from-zero", "fade-up", "mask-reveal", "rotate-in",
    "flip-3d", "blur-to-sharp", "glitch-in", "typewriter", "elastic-drop", "whip-in", "color-sweep",
    # Loop / ambient
    "float", "pulse", "wiggle", "slow-rotate", "shimmer", "parallax-drift", "breathing-scale", "leaf-drift",
    # Emphasis
    "shake", "highlight-sweep", "underline-draw", "color-flash", "scale-punch", "draw-on",
    "circle-draw-on", "arrow-draw-on",
    # Exits
    "slide-out", "scale-down", "fade", "mask-wipe-out", "shatter", "whip-out",
]
TransitionType = Literal[
    "whip-pan", "zoom-through", "glitch", "slide-push",
    "shape-wipe", "flash-cut", "morph", "cross-zoom",
]

def _bounded(value, low, high, default):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    import math
    if not math.isfinite(number):
        return default
    return max(low, min(high, number))

class AnimStage(BaseModel):
    preset: AnimPreset | None = None
    duration: float | None = Field(default=None, ge=0, le=5)
    delay: float | None = Field(default=None, ge=0, le=5)
    amplitude: float | None = Field(default=None, ge=0, le=100)
    speed: float | None = Field(default=None, ge=0, le=100)
    model_config = {"extra": "allow"}

class LayerAnim(BaseModel):
    in_: AnimStage | None = Field(default=None, alias="in")
    loop: AnimStage | None = None
    out: AnimStage | None = None
    stagger: bool = False

    model_config = {"populate_by_name": True}

class Layer(BaseModel):
    id: str
    type: LayerType
    content: str = ""
    start: float = Field(ge=0, le=120)
    end: float = Field(ge=0, le=120)
    position: dict = Field(default_factory=lambda: {"x": 0.5, "y": 0.5})
    animation: LayerAnim = Field(default_factory=LayerAnim)
    style: dict = Field(default_factory=dict)

    @field_validator("position")
    @classmethod
    def valid_position(cls, v):
        v = dict(v or {})
        v["x"] = _bounded(v.get("x", 0.5), 0, 1, 0.5)
        v["y"] = _bounded(v.get("y", 0.5), 0, 1, 0.5)
        return v

    @field_validator("start", "end", mode="before")
    @classmethod
    def clamp_bounds(cls, v):
        return _bounded(v, 0, 120, 0.0)

    @property
    def duration(self):
        return max(0.0, self.end - self.start)

class BackgroundSpec(BaseModel):
    type: str = "color"
    model_config = {"extra": "allow"}

class CameraSpec(BaseModel):
    move: str = "static"
    intensity: float = 0.0
    model_config = {"extra": "allow"}

class Transition(BaseModel):
    type: TransitionType = "flash-cut"
    duration: float | None = Field(default=None, ge=0.1, le=1.0)

    @field_validator("duration", mode="before")
    @classmethod
    def clamp_duration(cls, v):
        return _bounded(v, 0.1, 1.0, 0.4) if v is not None else None

class Scene(BaseModel):
    id: str
    start: float = 0.0
    duration: float = Field(default=5, ge=0.5, le=5)
    background: BackgroundSpec = Field(default_factory=BackgroundSpec)
    camera: CameraSpec = Field(default_factory=CameraSpec)
    layers: list[Layer] = Field(min_length=1, max_length=40)
    transition_out: Transition | None = None

    @field_validator("duration", mode="before")
    @classmethod
    def clamp_duration(cls, v):
        return _bounded(v, 0.5, 5, 3)

    @field_validator("start", mode="before")
    @classmethod
    def clamp_start(cls, v):
        return _bounded(v, 0, 120, 0)

class Meta(BaseModel):
    fps: int = Field(default=30, ge=24, le=60)
    width: int = 1920
    height: int = 1080
    duration: float = Field(default=0, ge=0, le=600)
    style: str = "bold-kinetic"
    aspect_ratio: str = "16:9"
    model_config = {"extra": "allow"}

class ProjectSpec(BaseModel):
    version: Literal[2] = 2
    title: str
    prompt: str
    language: str = "en"
    meta: Meta = Field(default_factory=Meta)
    audio: dict = Field(default_factory=dict)
    scenes: list[Scene] = Field(min_length=1, max_length=30)

    @field_validator("title")
    @classmethod
    def valid_title(cls, v):
        v = str(v).strip()
        if not v:
            raise ValueError("Project must have a title")
        return v[:200]

    @property
    def duration(self) -> float:
        return self.scenes[-1].start + self.scenes[-1].duration if self.scenes else 0.0

class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=8, max_length=4000)
    duration: int = Field(default=20, ge=8, le=120)
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = "16:9"

class EditRequest(BaseModel):
    project_id: str
    command: str = Field(min_length=3, max_length=1000)
    selected_element_id: str | None = None
