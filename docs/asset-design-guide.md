# Motion Studio asset design guide

The library is local and indexed by `assets/manifest.json`. The API exposes `GET /api/assets/search?q=...&category=...&tags=...&mood=...&limit=...`, `GET /api/assets/categories`, and `GET /api/assets/{id}`. Search before inventing a decorative graphic. Search results are metadata-first; the file URL returned from the detail endpoint is under `/asset-files/`.

## Composition rules

- **One idea per frame.** Establish a focal point, then one support detail. Keep generous negative space: aim for 8–12% safe margins and avoid placing important copy at the very edge.
- **Hierarchy:** one title (largest), one explanation (roughly 35–45% of title size), and one small label or proof point. Use a 1.2–1.3 type scale for related levels; cap a scene at two font families and three weights.
- **Motion hierarchy:** lead with the message, follow with proof, then allow ambient decoration. Stagger related lines by 40–80 ms; avoid animating every layer at equal strength.
- **Contrast and palette:** select one named palette and keep its neutrals as the canvas/text foundation. Use one accent consistently. Check small text at WCAG AA contrast; palette endpoints are a starting point, not a substitute for checking actual rendered colors.
- **Background layering:** combine one soft gradient or pattern, then at most one low-opacity grain/texture overlay. Keep texture subtle behind copy. Never use multiple high-frequency patterns under small type.
- **Vector artwork:** use `currentColor` icons and shapes for precise recoloring. Keep icon size and stroke weight consistent within a scene. Stickers are illustrative accents, not substitutes for product screenshots.
- **Timing:** entrance 0.35–0.7 s; text stagger 0.04–0.08 s; transition 0.45–0.8 s; hold a key headline for at least 1.2 s after it settles; exit 0.25–0.5 s. For a 15–20 s social piece, allow 3–5 distinct beats and a clear final CTA.
- **Aspect ratios:** 16:9 landscape supports title + proof side-by-side; 9:16 uses a single centered column with generous top/bottom safe zones; 1:1 should keep titles shorter and imagery central; 4:5 social crops should preserve a central 80% safe area.
- **Fonts:** use bundled DM Sans / Manrope for general Latin UI, Vazirmatn for Persian/RTL. Pair a display family with a quiet body family from `assets/catalogs/font-pairings.json`; unbundled catalog fonts require an explicit licensed font download before use.
- **Motion safety:** the current project schema supports `rise`, `scale`, `drift`, `pulse`, `reveal`, `none` and `fade`, `wipe`, `zoom`, `cut`. The broader catalogs are discovery/reference recipes; do not emit unsupported schema values into project JSON.

## Recommended pairings

The curated set of 15 pairings is in `assets/catalogs/font-pairings.json`. Reliable defaults: DM Sans + DM Serif Display (product/editorial), Space Grotesk + Space Mono (technology/data), Oswald + Inter (campaign headline/body), Vazirmatn + DM Sans (Persian/Latin), and Quicksand + Lato (friendly social).

## Scene recipes

1. **Tech product launch:** `midnight-violet` palette + `mesh-violet` + `film-grain-fine`; Space Grotesk/DM Sans; short eyebrow, rising hero title, a single `mockup-laptop-dashboard`, then a crisp CTA. Use `snappy` easing and a wipe or clean fade.
2. **Social quote reel:** `soft-lavender` + `paper-speckle`; DM Serif Display + DM Sans; quote in three staggered lines, one `sparkle` illustration and author label; slow crossfade-like fade with a 1.5 s hold.
3. **Data stat explainer:** `blueprint` palette + `grid-fine`; Inter + IBM Plex Mono; `stat-kpi-trio`, `animated-bar-chart`, and `rolling-counter`; `quart-out` entrance, then deliberate pause for reading.
4. **Premium product reveal:** `copper-night` + `radial-glow` + `vignette-soft`; Manrope + Fraunces; single large product area, restrained title, orbit motif, slow zoom and generous negative space.
5. **Creator subscribe CTA:** `candy-shop` + `dots-small`; Outfit + Nunito; `subscribe-button`, `notification-toast`, sticker `confetti`; `bouncy` only on the CTA, keep the copy still long enough to read.
6. **Wellness habit story:** `forest-moss` + `wave-horizontal`; DM Sans + Lora; `leaf` and `sun` illustrations, three short benefit beats, `spring-soft`; soft fade between beats.
7. **Fintech proof point:** `carbon-cobalt` + `grid-perspective`; Inter + Roboto Mono; one `stat-kpi-single`, `animated-line-chart`, clear units and source label; `circ-out` and restrained `snappy` transitions.
8. **Travel teaser:** `sunset-hour` + `aurora-mist`; Manrope + Playfair Display; `globe`, `paper-plane`, and `mountain` stickers; diagonal wipe into a destination title, warm grain kept subtle.
9. **Event title card:** `neon-tokyo` + `starfield-sparse`; Bebas Neue + DM Sans; a single oversized title, date label, `confetti-burst` only at the end; high-energy but short entrance.
10. **Editorial announcement:** `monochrome-paper` + `paper-crease`; DM Serif Display + DM Sans; clear headline, single body line, `underline-swoosh`; slow reveal and no decorative clutter.
11. **App feature walkthrough:** `ocean-signal` + `dots-small`; Plus Jakarta Sans + IBM Plex Mono; `mockup-phone-dashboard`, three numbered callouts, `slide-mask-left`; keep the phone within 9:16 safe margins.
12. **Community milestone:** `festival` + `bokeh-circles`; Nunito + Space Grotesk; `trophy`, `heart`, one rolling counter, `ribbon-streamers`; bounce the number once, hold the result.

## Current renderer integration boundary

Generated scene specifications now support typed SVG icon (`asset_id`) and background (`background_asset`) references. The Remotion worker resolves only registry IDs and embeds recolored SVG data—model text is never interpreted as a path or executed. Generated projects select these vector assets alongside scene text. The broad motion catalogs are discoverable recipes; only the established transition/entrance values are serialized until matching deterministic renderers are implemented for each additional preset.
