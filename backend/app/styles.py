"""Visual style presets — Python mirror of renderer/src/styles.ts.

Each style defines design tokens (palette, fonts, radius, animation
personality) plus the preset vocabulary the LLM may choose from
(renderer/src/animations.ts) and the transition set. Keep in sync with the
TypeScript file.
"""
from __future__ import annotations

STYLES: dict[str, dict] = {
    "bold-kinetic": {
        "name": "Bold Kinetic",
        "description": "High-contrast, huge type, punchy springs and bold entrances — built for short-form speed.",
        "palette": ["#0B1020", "#F8FAFC", "#7C5CFC", "#21D4A7"],
        "fonts": {"headline": "Manrope, sans-serif", "body": "Manrope, sans-serif"},
        "radius": 12,
        "defaultIn": "pop-bounce",
        "defaultLoop": "float",
        "defaultBackground": "animated-gradient",
        "transitions": ["whip-pan", "flash-cut", "morph", "zoom-through"],
    },
    "clean-explainer": {
        "name": "Clean Explainer",
        "description": "Soft shapes, smooth easing, icons and mask reveals — clear, unhurried, trustworthy.",
        "palette": ["#F8F5F2", "#1B2735", "#4A7A9A", "#B8C3D6"],
        "fonts": {"headline": "DM Sans, sans-serif", "body": "Manrope, sans-serif"},
        "radius": 16,
        "defaultIn": "fade-up",
        "defaultLoop": "breathing-scale",
        "defaultBackground": "animated-gradient",
        "transitions": ["cross-zoom", "slide-push", "morph", "flash-cut"],
    },
    "neon-cyber": {
        "name": "Neon Cyber",
        "description": "Glow, glitch, rotating grid — electric blues and violets with kinetic typography.",
        "palette": ["#050B17", "#A78BFA", "#2DF5C4", "#00F5FF"],
        "fonts": {"headline": "Manrope, sans-serif", "body": "Manrope, sans-serif"},
        "radius": 6,
        "defaultIn": "glitch-in",
        "defaultLoop": "slow-rotate",
        "defaultBackground": "grid",
        "transitions": ["glitch", "morph", "flash-cut", "whip-pan"],
    },
    "editorial-minimal": {
        "name": "Editorial Minimal",
        "description": "Serif-leaning display, mask reveals, subtle motion, generous whitespace.",
        "palette": ["#FAFAF8", "#1A1A1A", "#3C3C3C", "#9C9C9C"],
        "fonts": {"headline": "Playfair Display, serif", "body": "Manrope, sans-serif"},
        "radius": 20,
        "defaultIn": "mask-reveal",
        "defaultLoop": "shimmer",
        "defaultBackground": "color",
        "transitions": ["morph", "cross-zoom", "shape-wipe"],
    },
    "playful-sticker": {
        "name": "Playful Sticker",
        "description": "Bouncy springs, emoji symbols, hand-drawn strokes, sticker badges — friendly and loud.",
        "palette": ["#FFF1D2", "#FF9E6D", "#5CD9A5", "#9CC6FF"],
        "fonts": {"headline": "Manrope, sans-serif", "body": "Manrope, sans-serif"},
        "radius": 20,
        "defaultIn": "elastic-drop",
        "defaultLoop": "wiggle",
        "defaultBackground": "particles",
        "transitions": ["whip-pan", "flash-cut", "cross-zoom"],
    },
}

STYLE_IDS = list(STYLES)

# Preset vocabulary (mirrors renderer/src/animations.ts). LLM-facing list.
ALLOWED_PRESETS = [
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

TRANSITION_TYPES = ["whip-pan", "zoom-through", "glitch", "slide-push", "shape-wipe", "flash-cut", "morph", "cross-zoom"]


def get_style(style_id: str) -> dict:
    return STYLES.get(style_id) or STYLES["bold-kinetic"]
