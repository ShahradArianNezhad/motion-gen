# Adding new animation presets

Presets are the vocabulary the LLM plans with and the renderer executes. Everything lives in one TypeScript file, `renderer/src/animations.ts`, plus its Python mirror for the LLM prompt/validator (`backend/app/styles.py`).

## 1. Add the behavior to `renderer/src/animations.ts`

A preset is a function in one of four registries, keyed by its name:

```ts
presetEntrances: Record<string, PresetBehavior>
presetLoops:     Record<string, PresetBehavior>
presetEmphasis:  Record<string, PresetBehavior>
presetExits:     Record<string, PresetBehavior>
```

Implement with the built-ins first:

```ts
export type PresetBehavior = (e: ExecParams) => ExecResult;

// e.g. entrance
const presetMyIn: PresetBehavior = ({ progress, ctx }) => ({
  opacity: easing.easeOutBack(progress),            // movement: dx, dy, scale, rotate
  dx: easing.easeOutExpo(progress) * 20, dy: 0, scale: 1, rotate: 0,
  extra: { myFlag: progress },                      // bespoke outputs, see below
});
```

`ExecResult` fields: `opacity`, `dx`, `dy`, `scale`, `rotate`, `extra`. Use `execPreset` to dispatch by name:

```ts
execPreset('my-in', { progress: 0.5, ctx: { fps, frame } })
```

Helper utilities available:

- `easing.*` — never linear; `easeOutBack/Expo/Bounce`, `easeOutBack(t, overshoot)`, `easeInBack`, etc.
- `springProgress({ frame, fps, config })` — Remotion `spring` in [0, 1].
- `staggeredProgress({ index, total, offsetMs, frame, fps })` — 30–80 ms stagger for per-char/word reveals.
- `clamp01`, `range`.

The `extra` bag carries preset-specific numbers that components read, e.g. `typewriter` returns `charCount`, `mask-reveal` returns `reveal`, `draw-on` returns `stroke`. If you need a brand-new custom signal, return it from `extra` and consume it in `renderer/src/Composition.tsx`.

Stagger note: for text layers, `KineticText` already consumes `extra.charCount` (typewriter) and `layer.animation.stagger` (per-char appears) — so a typewriter preset needs only `charCount`.

## 2. Add the name to `src/types.ts` (`AnimPreset`)

```ts
export type AnimPreset = 'pop-bounce' | 'my-in' | ...;
```

## 3. Add it to the Python mirror (`backend/app/styles.py`)

`ALLOWED_PRESETS` is the list the LLM prompt injects and the validator accepts. Append the new preset:

```python
ALLOWED_PRESETS.append("my-in")
```

(Optional: add `"my-in"` to a style's `transitions` or adjust `"defaultIn"`.)

## 4. Consumers in `renderer/src/Composition.tsx`

Entrances/exits/loops run through `execPreset`; exits run when `frame > layer.end - outDuration`. Styles (fonts, colors, radii, transitions) come from `renderer/src/styles.ts` (`STYLES`, `getStyle`, `getPalette`) — add a new style by extending that file and pointing `meta.style` at it.

## 5. Regenerate

```bash
npm run build && npm run render examples/reel-example.json exports/out.mp4 mp4
```

Quick checklist when adding a preset: name in TS registry + `AnimPreset` + `ALLOWED_PRESETS`, deterministic on frame (no `Date`), and tested by rendering once.
