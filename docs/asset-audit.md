# Asset library audit

## What exists

- **Stack:** React 18 + TypeScript + Vite frontend, Zustand state, Python/FastAPI + Pydantic API.
- **Animation/rendering:** declarative project JSON is validated by Pydantic; a React/SVG composition is rendered frame-by-frame with **Remotion**, Chromium, and FFmpeg. Rendering is isolated in a Node worker. The editor and renderer share the `ProjectSpec` types.
- **Current visual assets:** no dedicated asset directory or registry. `lucide-react` is installed as an icon dependency; current generated scenes use a small palette, typographic layers, a few Unicode glyphs, and hardcoded radial gradients/grid overlays in `renderer/src/Composition.tsx`. The renderer has six entrance animations and four transitions.
- **Current typography:** DM Sans, Manrope, and Vazirmatn through `@fontsource` packages.
- **AI access:** `backend/app/generation.py` optionally calls an OpenAI-compatible API in two stages (brief interpretation and storyboard), then deterministically composes and validates JSON. Its prompts describe only four transitions and do not mention an asset registry. The local generator likewise has four fixed palette choices. There is no asset-query API.
- **Audio:** narration is a text field only; there is no audio playback/rendering pipeline, so bundled SFX/music do not fit the current product.

## Gaps and implementation direction

The asset set, discovery mechanism, design guidance, visual review surface, and validation are all missing. Preserve the current Remotion + SVG/CSS architecture: add a local metadata registry and deterministic search helper, reusable SVG/JSON assets, motion/palette/font catalogs, a registry-backed API and gallery, and renderer-compatible examples. Do not add an audio pipeline or rely on a new renderer. Since the current project schema only accepts a small set of motion values, expose the expanded preset catalog as discovery metadata and progressively support the compatible preset subset in rendering rather than silently emitting unsupported project values.

## Library delivery summary (this task)

- Expanded the asset registry to **1,969 entries**: 1,200 Lucide icons + 108 Simple Icons brand vectors, 60 primitives, 45 patterned backgrounds, 32 overlays, 100 Twemoji stickers, 20 device/UI frames, 50 Lottie examples, 45 WOFF2 font families, 15 font pairings, 59 palettes + 118 gradients, 32 text-animation recipes, 30 transitions, 20 easing/spring presets, 18 effect recipes, and 32 composition templates.
- Added a manifest-backed API and Python `search_assets` / `get_asset` / `list_categories` helpers. The AI storyboard prompt receives relevant search results, and generated scenes now include deterministic, typed SVG icon/background references resolved by the Remotion worker.
- Added `/assets` for interactive categorized browsing and five real Remotion MP4 output examples. Added Pexels/Pixabay photo+video and Unsplash photo search adapters; audio remains intentionally unsupported because the app has no audio track/playback/render path.
- Asset paths, metadata, IDs, and license-family documentation are checked by `scripts/validate_assets.py`. The remaining deliberate gap is broader deterministic rendering for the expanded motion recipe catalog; unsupported recipe names are not emitted into validated project JSON.
