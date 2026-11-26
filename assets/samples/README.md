# Rendered sample stories

These small MP4s were rendered through `renderer/render.mjs` (Remotion + bundled Chromium) at reduced preview scale from the specs in this folder. They exercise the actual typed icon/background references and scene transition pipeline.

- `tech-product-launch.mp4` — landscape launch, rocket SVG, mesh/grid background.
- `social-quote-reel.mp4` — vertical quote, sparkle mark, patterned background.
- `data-stat-explainer.mp4` — landscape KPI, chart icon, high-contrast palette.
- `cinematic-product-reveal.mp4` — restrained premium title, warm accents.
- `creator-community-cta.mp4` — square CTA, heart icon and bright palette.

Regenerate with `python scripts/render_asset_samples.py` after installing Node dependencies. The MP4s are intentionally lightweight review renders, not final-resolution exports.
