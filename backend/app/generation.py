"""Generation pipeline v2 — timeline plans (scenes + layers + keyframes).

Stages:
  1. _llm_brief   — interpret the creative brief (fast).
  2. _llm_plan    — draft a full version-2 plan; validated by _validate_v2 with
                    automatic retries feeding validator problems back to the LLM.
  3. _local_spec_v2 — deterministic fallback (no API key), emits v2 plans too.

Validator problems from _lint_spec_v2 are surfaced to the LLM so it can self-correct
(rejected scene layouts, unsafe zones, missing in-animations, repeated layouts).
"""
from __future__ import annotations
import copy, json, math, os, re
from typing import Any
import httpx
from .models import ProjectSpec, GenerateRequest, AnimStage
from .styles import STYLE_IDS, STYLES, ALLOWED_PRESETS, TRANSITION_TYPES

ASPECT_SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}
MAX_SCENE_SECONDS = 5.0  # pace: never longer without an internal visual event

# ---------------------------------------------------------------------------
# Shared coercion helpers
# ---------------------------------------------------------------------------
def _bounded(value: Any, low: float, high: float, default: float) -> float:
    try: number = float(value)
    except (TypeError, ValueError): return default
    if not math.isfinite(number): return default
    return max(low, min(high, number))

def _hex(value: Any) -> str:
    return value if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value) else "#0B1020"

# ---------------------------------------------------------------------------
# Stage 1 — brief interpretation
# ---------------------------------------------------------------------------
BRIEF_PROMPT = """Stage 1 — interpret a motion-graphics creative brief. Return JSON only:
{"working_title": string, "video_purpose": string, "target_audience": string,
 "visual_style": string, "duration_seconds": number, "aspect_ratio": "16:9"|"9:16"|"1:1",
 "palette": [3-4 hex strings], "language": BCP47 tag ("fa" for Persian),
 "narration_style": string, "typography_direction": string, "transition_mood": string,
 "scene_count": number (3-6), "hook_emphasis": string}
Extract what the user actually asked for; do not write a storyboard yet. Preserve
Persian/mixed-language requirements. Be concise and numeric-safe (duration 5–60)."""

# ---------------------------------------------------------------------------
# Stage 2 — v2 plan drafting (with full preset vocabulary injected)
# ---------------------------------------------------------------------------
def plan_prompt() -> str:
    return (f"Stage 2 — write a full version-2 animation plan as JSON only, using ONLY these animation presets (never invent others): {json.dumps(ALLOWED_PRESETS)}.\n"
            'Schema: {"version": 2, "title": string, "prompt": string, "language": BCP47 tag, "meta": {"fps": int, "width": int, "height": int, "duration": float, "style": one of ['
            + ", ".join(f'"{s}"' for s in STYLE_IDS) + ']}, "audio": {"voiceover": str, "music": str, "sfx": [{"t": num, "type": "whoosh"|"pop"|"click"|"ding"|"impact"}...]},\n'
            '"scenes": [{"id", "start", "duration" (0.5–' + str(MAX_SCENE_SECONDS) + '), "background": {"type": "animated-gradient"|"color"|"grid"|"particles"|"image-kenburns", "colors": [hex...]}, "camera": {"move": "static"|"push-in"|"pan-left"|"shake"|"orbit", "intensity": 0–1},\n'
            '"layers": [{"id", "type": "text"|"image"|"shape"|"icon"|"lottie"|"video"|"chart"|"caption", "content", "start", "end",\n'
            '"position": {"x": 0-1, "y": 0-1}, "animation": {"in": {"preset", "duration", "delay"}, "loop": {"preset", "amplitude"?, "speed"?}, "out": {"preset", "duration"}},\n'
            '"style": {color, fontSize, fontWeight, ...}}...], "transition_out": {"type": one of ' + ", ".join(f'"{t}"' for t in TRANSITION_TYPES) + ', "duration": 0.2-0.5}}]}\n\n'
            "Rules (enforce strictly):\n"
            "1) Every layer MUST have animation.in with a preset. Loop on the main text/icon, exit on everything.\n"
            "2) Every scene MUST have an animated-gradient or particles/grid background + a non-static camera (push-in/shake) — never plain color.\n"
            "3) Pacing: scenes 0.5–5s; a visual event every 0.5–1.5s; layers staggered (stagger: true for text).\n"
            "4) Safe zones: 9:16 → keep text y ≥ 0.4 and x ≥ 0.1; 16:9 → y ≥ 0.15.\n"
            "5) Vary: never repeat the same transition twice in a row, vary layout between scenes, vary entrance presets.\n"
            "6) Hook: first layer in scene 0 must animate in at frame 0 with a punchy preset.\n"
            "7) Write short punchy text (≤7 words per line), for the ear.\n"
            "8) Give each scene visual_purpose (it has NO elements key — visuals come from layers).\n")

ALLOWED_LAYER_TYPES = {"text", "image", "shape", "icon", "lottie", "video", "chart", "caption"}

def _normalize_stage(stage: Any, default_preset: str) -> dict[str, Any] | None:
    """Normalize an animation stage (in/loop/out) from any LLM shape.

    Accepts dicts, bare preset strings, or None. Clamps numeric fields to the
    AnimStage bounds and falls back to ``default_preset`` for unknown presets.
    Returns None when the stage is absent (only valid for loop/out).
    """
    if stage is None:
        return None
    if isinstance(stage, str):
        stage = {"preset": stage}
    if not isinstance(stage, dict):
        return None
    preset = stage.get("preset")
    if preset not in ALLOWED_PRESETS:
        preset = default_preset
    normalized: dict[str, Any] = {"preset": preset}
    for key, low, high in (("duration", 0, 5), ("delay", 0, 5), ("amplitude", 0, 100), ("speed", 0, 100)):
        if stage.get(key) is not None:
            normalized[key] = _bounded(stage.get(key), low, high, 0.5 if key == "duration" else 0)
    # Preserve any extra renderer params the model allows through.
    for key, value in stage.items():
        if key not in normalized and key != "preset":
            normalized[key] = value
    return normalized

# ---------------------------------------------------------------------------
# Auto-repair pass (deterministic preflight)
# ---------------------------------------------------------------------------
def _repair_v2(raw: dict[str, Any], aspect_ratio: str | None = None,
               prompt_fallback: str | None = None, title_fallback: str | None = None) -> dict[str, Any]:
    candidate = copy.deepcopy(raw) if isinstance(raw, dict) else {}
    # Required top-level fields (ProjectSpec has no defaults for these).
    candidate["version"] = 2
    if not str(candidate.get("title") or "").strip():
        candidate["title"] = title_fallback or "Motion story"
    if not str(candidate.get("prompt") or "").strip():
        candidate["prompt"] = prompt_fallback or str(candidate.get("title") or "Motion story")
    if not isinstance(candidate.get("language"), str) or not candidate["language"].strip():
        candidate["language"] = "en"
    if not isinstance(candidate.get("audio"), dict):
        candidate["audio"] = {}
    meta = candidate.get("meta") if isinstance(candidate.get("meta"), dict) else {}
    style = meta.get("style") if isinstance(meta.get("style"), str) else "bold-kinetic"
    meta.setdefault("fps", 30); meta["fps"] = int(_bounded(meta.get("fps"), 24, 60, 30))
    meta.setdefault("duration", 0.0); meta["duration"] = _bounded(meta.get("duration"), 0, 600, 0.0)
    if aspect_ratio:
        requested_aspect = aspect_ratio
    else:
        requested_aspect = str(meta.get("aspect_ratio") or "")
        if requested_aspect not in ASPECT_SIZES:
            try:
                old_width, old_height = int(meta.get("width", 1920)), int(meta.get("height", 1080))
                requested_aspect = "9:16" if old_height > old_width else "1:1" if old_width == old_height else "16:9"
            except (TypeError, ValueError):
                requested_aspect = "16:9"
    if requested_aspect not in ASPECT_SIZES:
        requested_aspect = "16:9"
    w, h = ASPECT_SIZES[requested_aspect]
    # The requested aspect ratio wins over whatever the LLM guessed.
    meta["width"] = w; meta["height"] = h
    meta["aspect_ratio"] = requested_aspect
    meta["style"] = style if style in STYLE_IDS else "bold-kinetic"
    candidate["meta"] = meta
    scenes = candidate.get("scenes") if isinstance(candidate.get("scenes"), list) else []
    candidate["scenes"] = scenes[:20]
    if not candidate["scenes"]:
        candidate["scenes"] = [{"id": "scene-1", "duration": 4, "layers": []}]
    start = 0.0
    for i, scene in enumerate(candidate["scenes"]):
        if not isinstance(scene, dict): scene = {}; candidate["scenes"][i] = scene
        scene["id"] = str(scene.get("id") or f"scene-{i+1}")
        scene["duration"] = _bounded(scene.get("duration"), 0.5, MAX_SCENE_SECONDS, 3)
        scene["start"] = start; start += scene["duration"]
        bg = scene.get("background") if isinstance(scene.get("background"), dict) else {}
        bg_colors = [c for c in (bg.get("colors") or []) if isinstance(c, str)][:3]
        if not bg_colors:
            bg_colors = STYLES[meta["style"]]["palette"][:3]
        scene["background"] = {"type": str(bg.get("type") or "animated-gradient"), "colors": bg_colors}
        cam = scene.get("camera") if isinstance(scene.get("camera"), dict) else {}
        scene["camera"] = {"move": str(cam.get("move") or "push-in"), "intensity": _bounded(cam.get("intensity"), 0, 1, 0.6)}
        # Accept "elements" as an alias for "layers" (a common LLM slip).
        if not isinstance(scene.get("layers"), list) and isinstance(scene.get("elements"), list):
            scene["layers"] = scene["elements"]
        layers = scene.get("layers") if isinstance(scene.get("layers"), list) else []
        scene["layers"] = layers[:40]
        if not scene["layers"]:
            scene["layers"] = [{"id": f"{scene['id']}-layer-1", "type": "text", "content": "Motion story",
                                "start": 0, "end": scene["duration"], "position": {"x": 0.5, "y": 0.42}}]
        for li, layer in enumerate(scene["layers"]):
            if not isinstance(layer, dict): layer = {}; scene["layers"][li] = layer
            layer["id"] = str(layer.get("id") or f"{scene['id']}-layer-{li+1}")
            layer_type = str(layer.get("type") or "text")
            layer["type"] = layer_type if layer_type in ALLOWED_LAYER_TYPES else "text"
            layer["content"] = str(layer.get("content") or "")[:200]
            layer["start"] = _bounded(layer.get("start", 0), 0, scene["duration"], 0.0)
            layer["end"] = _bounded(layer.get("end", scene["duration"]), layer["start"], scene["duration"], scene["duration"])
            pos = layer.get("position") if isinstance(layer.get("position"), dict) else {}
            layer["position"] = {"x": _bounded(pos.get("x", 0.5), 0, 1, 0.5), "y": _bounded(pos.get("y", 0.5), 0, 1, 0.5)}
            anim = layer.get("animation") if isinstance(layer.get("animation"), dict) else {}
            layer["animation"] = anim
        # Every layer must have an entrance; loop/out presets are validated too.
        for layer in scene["layers"]:
            anim = layer["animation"]
            in_stage = anim.get("in_") or anim.get("in")
            anim["in_"] = _normalize_stage(in_stage, "pop-bounce") or {"preset": "pop-bounce", "duration": 0.5}
            anim.pop("in", None)
            loop_stage = _normalize_stage(anim.get("loop"), "float")
            if loop_stage is not None:
                anim["loop"] = loop_stage
            else:
                anim.pop("loop", None)
            out_stage = _normalize_stage(anim.get("out"), "slide-out")
            if out_stage is not None:
                anim["out"] = out_stage
            else:
                anim.pop("out", None)
        t = scene.get("transition_out") if isinstance(scene.get("transition_out"), dict) else None
        if t is None or str(t.get("type")) not in TRANSITION_TYPES:
            t = {"type": "morph", "duration": 0.3}
            scene["transition_out"] = t
        t.setdefault("duration", 0.3)
    return candidate

# ---------------------------------------------------------------------------
# Validator + linter (auto-fixes; collects problems for LLM retry)
# ---------------------------------------------------------------------------
def _lint_v2(spec: ProjectSpec) -> list[str]:
    problems: list[str] = []
    seen_layouts: list[tuple] = []
    for scene in spec.scenes:
        if scene.duration > MAX_SCENE_SECONDS + 0.01:
            problems.append(f"Scene '{scene.id}' is {scene.duration:.1f}s — cap at 5s without internal events.")
        if scene.background.type in ("color", "none") and not (scene.background.colors or []):
            problems.append(f"Scene '{scene.id}' has a plain static background — use animated-gradient/particles/grid.")
        if scene.camera.move in ("static", "none") and scene.duration >= 3:
            problems.append(f"Scene '{scene.id}' is static — add push-in/shake camera motion.")
        # layout repetition
        sig = tuple((l.position["x"], l.position["y"]) for l in scene.layers)
        if sig in seen_layouts:
            problems.append(f"Scene '{scene.id}' repeats the layout of an earlier scene.")
        seen_layouts.append(sig)
        # safe zones (9:16 conservative; text y kept out of bottom 20%)
        min_y = 0.38
        if spec.meta.width < spec.meta.height:
            for l in scene.layers:
                if l.type == "text" and l.position["y"] < min_y:
                    problems.append(f"Layer '{l.id}' sits in the 9:16 unsafe zone (y={l.position['y']:.2f} < {min_y}).")
    return problems

def _auto_fix_v2(spec: ProjectSpec) -> list[str]:
    changes: list[str] = []
    seen_layouts: list[tuple] = []
    for i, scene in enumerate(spec.scenes):
        if scene.background.type == "color" and not scene.background.colors:
            scene.background.type = "animated-gradient"
            scene.background.colors = STYLES[spec.meta.style]["palette"][:3]
            changes.append(f"Scene {i+1}: replaced plain background with animated-gradient")
        if scene.camera.move in ("static", "none") and scene.duration >= 3:
            scene.camera.move = "push-in"; scene.camera.intensity = 0.6
            changes.append(f"Scene {i+1}: added push-in camera")
        if scene.duration > MAX_SCENE_SECONDS:
            scene.duration = MAX_SCENE_SECONDS
            changes.append(f"Scene {i+1}: capped duration at {MAX_SCENE_SECONDS}s")
        for layer in scene.layers:
            if layer.animation.in_ is None:
                layer.animation.in_ = AnimStage(preset="pop-bounce", duration=0.5)
                changes.append(f"Scene {i+1} layer '{layer.id}': added pop-bounce entrance")
            if spec.meta.width < spec.meta.height:
                if layer.type == "text" and layer.position["y"] < 0.38:
                    layer.position["y"] = 0.38
                    changes.append(f"Scene {i+1} layer '{layer.id}': moved text out of the 9:16 unsafe zone")
        # Vary repeated layouts so the linter cannot loop forever on them.
        sig = tuple((l.position["x"], l.position["y"]) for l in scene.layers)
        if sig in seen_layouts:
            original = [(l.position["x"], l.position["y"]) for l in scene.layers]
            # Try deterministic small offsets until the whole signature is unique.
            for attempt in range(1, 31):
                for layer, (x, y) in zip(scene.layers, original):
                    layer.position["x"] = 0.1 + ((x - 0.1 + attempt * 0.037) % 0.8)
                    layer.position["y"] = 0.2 + ((y - 0.2 + attempt * 0.029) % 0.65)
                sig = tuple((l.position["x"], l.position["y"]) for l in scene.layers)
                if sig not in seen_layouts:
                    break
            changes.append(f"Scene {i+1}: varied repeated layout")
        seen_layouts.append(sig)
    return changes

def validate_with_correction(raw: dict[str, Any], max_retries: int = 2,
                             aspect_ratio: str | None = None,
                             prompt_fallback: str | None = None,
                             title_fallback: str | None = None) -> tuple[ProjectSpec, list[str]]:
    """Validate v2 spec; auto-fix common issues; returns (spec, problems).

    Raises ValueError carrying the lint problems (or the Pydantic error text)
    so the LLM retry loop can feed concrete feedback back to the model.
    """
    candidate = _repair_v2(raw, aspect_ratio=aspect_ratio,
                           prompt_fallback=prompt_fallback, title_fallback=title_fallback)
    last_problems: list[str] = []
    for _ in range(max_retries + 1):
        try:
            spec = ProjectSpec.model_validate(candidate)
        except Exception as exc:
            raise ValueError(f"v2 animation plan failed schema validation: {exc}") from exc
        fixed = _auto_fix_v2(spec)
        problems = _lint_v2(spec)
        if not problems:
            return spec, fixed
        last_problems = problems
        # re-dump (auto fixes) and let model_validate re-run
        candidate = spec.model_dump(by_alias=True)
        fixed.extend(problems)
    raise ValueError(f"v2 animation plan could not be validated: {'; '.join(last_problems)}")

# ---------------------------------------------------------------------------
# Stage 2 retry loop — validate with LLM feedback
# ---------------------------------------------------------------------------
async def _chat_json(client: httpx.AsyncClient, base: str, key: str, model: str, system: str, user: str) -> dict[str, Any]:
    response = await client.post(f"{base}/chat/completions", headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "temperature": 0.45, "response_format": {"type": "json_object"},
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
    response.raise_for_status()
    return json.loads(response.json()["choices"][0]["message"]["content"])

async def _llm_plan(brief: dict[str, Any], req: GenerateRequest, problems: list[str], attempt: int) -> dict[str, Any]:
    key = os.getenv("LLM_API_KEY")
    base = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    user = (f"Interpreted brief: {json.dumps(brief, ensure_ascii=False)}. "
            f"Create a {req.duration}s v2 plan for aspect ratio {req.aspect_ratio}.")
    if problems:
        user += f"\n\nVALIDATOR PROBLEMS (fix these in the new plan): {json.dumps(problems, ensure_ascii=False)}"
    async with httpx.AsyncClient(timeout=60) as client:
        return await _chat_json(client, base, key or "", model, plan_prompt(), user)

async def _llm_brief(req: GenerateRequest) -> dict[str, Any]:
    key = os.getenv("LLM_API_KEY")
    base = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    async with httpx.AsyncClient(timeout=45) as client:
        return await _chat_json(client, base, key or "", model, BRIEF_PROMPT,
                                f"User brief: {req.prompt}. Runtime {req.duration}s, aspect {req.aspect_ratio}.")

async def _llm_spec_v2(req: GenerateRequest) -> tuple[dict[str, Any], list[str]]:
    brief = await _llm_brief(req)
    problems: list[str] = []
    for attempt in range(3):
        try:
            raw = await _llm_plan(brief, req, problems, attempt)
        except Exception as exc:
            problems = [f"LLM output was not parseable JSON ({type(exc).__name__}); retry"]
            continue
        try:
            spec, fixes = validate_with_correction(raw, max_retries=0,
                                                   aspect_ratio=req.aspect_ratio,
                                                   prompt_fallback=req.prompt,
                                                   title_fallback=str(brief.get("working_title") or "Motion story"))
            return spec.model_dump(by_alias=True), (fixes or [])
        except Exception as exc:
            # Feed the concrete validator problems back so the model can self-correct.
            problems = [str(exc)[:2000]]
    raise RuntimeError(f"The v2 plan could not be validated after 3 attempts. Last problems: {'; '.join(problems)[:2000]}")

# ---------------------------------------------------------------------------
# Local deterministic generator (v2)
# ---------------------------------------------------------------------------
def _kf_local_scene(idx: int, prompt_kind: str, req: GenerateRequest, style: dict) -> dict[str, Any]:
    """Local scene builder: gradient bg, camera, stagger, in/loop/out presets."""
    colors = style["palette"]
    scenes_data = [
        ("s1", 0.0, "Hook. Your next move, fast.", "animated-gradient", "push-in"),
        ("s2", 0.0, "Live numbers. True at a glance.", "particles", "shake"),
        ("s3", 0.0, "Try it now — no setup.", "grid", "push-in"),
        ("s4", 0.0, "A story built to move. Start here.", "animated-gradient", "orbit"),
    ]
    s_id, s_start, s_title, s_bg, s_cam = scenes_data[idx % 4]
    layers: list[dict[str, Any]] = []
    headline = {"headline": "Hook. Your next move, fast.", "metric": "Live numbers. True at a glance.",
                "caption": "Try it now — no setup.", "body": "A story built to move. Start here."}.get(prompt_kind, s_title)
    layers.append({"id": f"{s_id}-h1", "type": "text", "content": s_title,
                   "start": 0.0, "end": 4.0, "position": {"x": 0.5, "y": 0.42},
                   "animation": {"in_": {"preset": "pop-bounce", "duration": 0.5},
                                 "loop": {"preset": "float", "amplitude": 8},
                                 "out": {"preset": "slide-out", "duration": 0.3}, "stagger": True},
                   "style": {"color": colors[0], "fontSize": 96, "fontWeight": 800}})
    if idx == 1:
        layers.append({"id": f"{s_id}-m1", "type": "text", "content": "3×",
                       "start": 0.3, "end": 4.0, "position": {"x": 0.5, "y": 0.6},
                       "animation": {"in_": {"preset": "scale-punch", "duration": 0.6},
                                     "loop": {"preset": "pulse", "amplitude": 0.05}},
                       "style": {"color": colors[2], "fontSize": 90}})
        layers.append({"id": f"{s_id}-t1", "type": "text", "content": "Faster. Smarter. More control.",
                       "start": 1.0, "end": 3.5, "position": {"x": 0.5, "y": 0.73},
                       "animation": {"in_": {"preset": "slide-in", "duration": 0.4, "delay": 0.3}},
                       "style": {"color": colors[1], "fontSize": 36}})
    if idx == 2:
        layers.append({"id": f"{s_id}-s1", "type": "shape", "start": 0.4, "end": 3.8, "position": {"x": 0.5, "y": 0.58},
                       "animation": {"in_": {"preset": "underline-draw", "duration": 0.5}}, "style": {}})
        layers.append({"id": f"{s_id}-c1", "type": "text", "content": "CTA",
                       "start": 0.9, "end": 3.2, "position": {"x": 0.5, "y": 0.8},
                       "animation": {"in_": {"preset": "fade-up", "duration": 0.3}, "out": {"preset": "whip-out", "duration": 0.2}},
                       "style": {"color": colors[2], "fontSize": 46}})
    if idx == 3:
        layers.append({"id": f"{s_id}-l1", "type": "text", "content": "Built by you, trusted by all.",
                       "start": 0.2, "end": 3.8, "position": {"x": 0.5, "y": 0.65},
                       "animation": {"in_": {"preset": "elastic-drop", "duration": 0.5},
                                     "loop": {"preset": "breathing-scale", "amplitude": 0.01}},
                       "style": {"color": colors[3], "fontSize": 52}})
    return {"id": s_id, "start": 0.0, "duration": 4.5,
            "background": {"type": s_bg, "colors": colors[:3]},
            "camera": {"move": s_cam, "intensity": 0.55},
            "layers": layers,
            "transition_out": {"type": "whip-pan", "duration": 0.4}}

def _local_spec_v2(req: GenerateRequest) -> dict[str, Any]:
    style = STYLES["bold-kinetic"]
    n_scenes = 4
    per_scene = _bounded(req.duration / n_scenes, 4, MAX_SCENE_SECONDS, 5)
    total = per_scene * n_scenes
    scenes = []
    for i in range(n_scenes):
        scene = _kf_local_scene(i, "headline", req, style)
        scene["duration"] = per_scene
        scene["start"] = per_scene * i
        scenes.append(scene)
    return {"version": 2, "title": "Motion story", "prompt": req.prompt, "language": "en",
            "meta": {"fps": 30, "width": ASPECT_SIZES[req.aspect_ratio][0], "height": ASPECT_SIZES[req.aspect_ratio][1],
                     "duration": round(total, 2), "style": "bold-kinetic"},
            "audio": {}, "scenes": scenes}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def generate_project(req: GenerateRequest) -> tuple[ProjectSpec, str]:
    key = os.getenv("LLM_API_KEY")
    provider = "llm"
    if key:
        try:
            raw, _fixes = await _llm_spec_v2(req)
        except Exception:
            # Keep the generation flow usable when the provider is unavailable
            # or returns an unusable plan; the deterministic generator is offline-safe.
            raw, provider = _local_spec_v2(req), "local"
    else:
        raw, provider = _local_spec_v2(req), "local"
    try:
        spec, _problems = validate_with_correction(raw, max_retries=1, aspect_ratio=req.aspect_ratio,
                                                   prompt_fallback=req.prompt)
    except Exception as exc:
        if provider == "llm":
            raise RuntimeError(f"The v2 plan failed preflight validation after one correction. Try again or adjust the brief. Details: {exc}") from exc
        raise
    return spec, provider
