// Animation primitive library for motion-gen (version-2 schema).
// Pure, deterministic, frame-driven utilities: easing curves + springs + the
// full preset registry (entrances / loops / emphasis / exits). Presets are
// selected by name from the schema and executed by the renderer.
import { spring } from 'remotion';
import type { AnimPreset } from '../../src/types';

// ---------------------------------------------------------------------------
// Easing curves (never linear for UI motion)
// ---------------------------------------------------------------------------
export const easing = {
  linear: (t: number) => t,
  easeInQuad: (t: number) => t * t,
  easeOutQuad: (t: number) => t * (2 - t),
  easeInCubic: (t: number) => t ** 3,
  easeOutCubic: (t: number) => 1 - (1 - t) ** 3,
  easeInQuart: (t: number) => t ** 4,
  easeOutQuart: (t: number) => 1 - (1 - t) ** 4,
  easeInQuint: (t: number) => t ** 5,
  easeOutQuint: (t: number) => 1 - (1 - t) ** 5,
  easeInSine: (t: number) => 1 - Math.cos((t * Math.PI) / 2),
  easeOutSine: (t: number) => Math.sin((t * Math.PI) / 2),
  easeInExpo: (t: number) => (t === 0 ? 0 : 2 ** (10 * t - 10)),
  easeOutExpo: (t: number) => t === 1 ? 1 : 1 - 2 ** (-10 * t),
  easeInBack: (t: number, overshoot = 1.5): number => {
    const c3 = overshoot + 1;
    return t === 0 ? 0 : t * t * ((c3 + 1) * t - c3);
  },
  easeOutBack: (t: number, overshoot = 1.5): number => {
    if (t >= 1) return 1;
    const c1 = 1.70158;
    const c3 = c1 + 1;
    const n = t - 1;
    return 1 - ((n * c3 + c1) * n + 1); // matches easeInBack at 1
  },
  easeInElastic: (t: number): number => {
    if (t <= 0) return 0;
    if (t >= 1) return 1;
    return 2 ** (-10 * t) * Math.sin((t * 10 - 0.75) * (2 * Math.PI) / 3);
  },
  easeOutElastic: (t: number): number => {
    if (t <= 0) return 0;
    if (t >= 1) return 1;
    return 1 - 2 ** (-10 * t) * Math.sin((t * 10 - 0.75) * (2 * Math.PI) / 3);
  },
  easeOutBounce: (t: number): number => {
    if (t < 1 / 2.75) return 7.5625 * t * t;
    if (t < 2 / 2.75) { const n = t - 1.5 / 2.75; return 7.5625 * n * n + 0.75; }
    if (t < 2.5 / 2.75) { const n = t - 2.25 / 2.75; return 7.5625 * n * n + 0.9375; }
    const n = t - 2.625 / 2.75;
    return 7.5625 * n * n + 0.984375;
  },
};

export const clamp01 = (v: number): number => Math.max(0, Math.min(1, v));
export const mapT = (v: number, lo: number, hi: number): number => (lo === hi ? lo : (v - lo) / (hi - lo));
export const range = (p: number, to: number, from = 0): number => mapT(clamp01(p), 0, 1) * (to - from) + from;

// ---------------------------------------------------------------------------
// Springs (damping/stiffness) — drives "pop-bounce" & friends
// ---------------------------------------------------------------------------
export interface SpringCfg { stiffness?: number; damping?: number; mass?: number; }
export const DEFAULT_SPRING: Required<SpringCfg> = { stiffness: 160, damping: 22, mass: 0.8 };

/** Remotion spring → progress in [0, 1]. */
export function springProgress(opts: {
  frame: number; fps: number; cfg?: SpringCfg;
  overshoot?: number;
}): number {
  const { frame, fps, cfg = {}, overshoot = 1.7 } = opts;
  const start = spring({ frame, fps, config: { ...DEFAULT_SPRING, ...cfg } });
  return clamp01(start);
}

/** Stagger helper: yields a 0→1 appear progress for index/total with a 30–80 ms offset per unit. */
export function staggeredProgress(opts: {
  index: number; total: number; offsetMs?: number; frame: number; fps: number;
}): number {
  const { index, total, offsetMs = 60, frame, fps } = opts;
  const offsetFrames = (offsetMs / 1000) * fps;
  const idx = Math.max(0, Math.min(total - 1, index));
  const stagger = idx * offsetFrames;
  return clamp01((frame - stagger) / (fps * 0.25));
}

// ---------------------------------------------------------------------------
// Preset execution engine
// ---------------------------------------------------------------------------
export interface ExecCtx { fps: number; frame: number; }
export interface ExecResult {
  opacity: number;
  dx: number; dy: number; scale: number; rotate: number;
  extra: Record<string, number>;
}
export interface ExecParams { progress: number; params?: Record<string, number>; ctx: ExecCtx; }

export type PresetBehavior = (e: ExecParams) => ExecResult;

const ENTRANCE_RESULTS: ExecResult = { opacity: 0, dx: 0, dy: 0, scale: 1, rotate: 0, extra: {} };

// --- Entrances -------------------------------------------------------------
const presetEntrances: Record<string, PresetBehavior> = {
  'pop-bounce': ({ progress, ctx }) => {
    const s = easing.easeOutBack(progress, 1.7);
    return { opacity: s, dx: 0, dy: 0, scale: 1 + (s - 1) * 0.2, rotate: 0, extra: {} };
  },
  'slide-in': ({ progress, params }) => {
    const dx = params?.dx ?? 30, dy = params?.dy ?? 0;
    const e = easing.easeOutBack(progress);
    return { opacity: e, dx: (1 - e) * dx, dy: (1 - e) * dy, scale: 1, rotate: 0, extra: {} };
  },
  'scale-from-zero': ({ progress }) => ({
    opacity: easing.easeOutBack(progress), scale: easing.easeOutBack(progress, 1.05),
    dx: 0, dy: 0, rotate: 0, extra: {},
  }),
  'fade-up': ({ progress }) => ({
    opacity: easing.easeOutCubic(progress), dy: (1 - easing.easeOutCubic(progress)) * 30,
    dx: 0, scale: 1, rotate: 0, extra: {},
  }),
  'mask-reveal': ({ progress }) => ({
    opacity: 1, dx: 0, dy: 0, scale: 1, rotate: 0, extra: { reveal: progress },
  }),
  'rotate-in': ({ progress }) => ({
    opacity: progress, rotate: easing.easeOutBack(progress, -18), dx: 0, dy: 0, scale: 1, extra: {},
  }),
  'flip-3d': ({ progress }) => ({
    opacity: progress, rotate: easing.easeOutBack(progress, 0) * 90, dx: 0, dy: 0, scale: 1,
    extra: { flip: easing.easeOutBack(progress, 0) },
  }),
  'blur-to-sharp': ({ progress }) => ({
    opacity: progress, dx: 0, dy: 0, scale: 1, rotate: 0, extra: { blur: Math.max(0, (1 - progress) * 12) },
  }),
  'glitch-in': ({ progress, ctx }) => {
    const shake = Math.sin(ctx.frame * 12.9898) * (1 - progress) * 12;
    return { opacity: progress, dx: shake, dy: Math.sin(ctx.frame * 3.7) * 3 * (1 - progress), scale: 1 + (1 - progress) * 0.02, rotate: 0, extra: { glitch: progress > 0.7 ? (Math.sin(ctx.frame * 9.7) * 6) : 0 } };
  },
  'typewriter': ({ progress, params }) => ({
    opacity: 1, dx: 0, dy: 0, scale: 1, rotate: 0, extra: { charCount: (params?.charLength ?? 0) * clamp01(progress) },
  }),
  'elastic-drop': ({ progress, ctx }) => {
    const springP = springProgress({ frame: ctx.frame, fps: ctx.fps, cfg: { damping: 12, stiffness: 80, mass: 0.9 } });
    return { opacity: progress, dy: -(1 - springP) * 30, scale: 1 + (1 - springP) * 0.15, dx: 0, rotate: 0, extra: { spring: springP } };
  },
  'whip-in': ({ progress }) => ({
    opacity: progress,
    dx: progress < 0.35 ? Math.sin(progress * Math.PI * 4) * 18 : 0,
    dy: progress < 0.35 ? Math.cos(progress * Math.PI * 3) * 14 : 0,
    scale: easing.easeOutBack(progress, 2), rotate: 0, extra: {},
  }),
  'color-sweep': ({ progress }) => ({
    opacity: progress, dx: 0, dy: 0, scale: 1, rotate: 0,
    extra: { sweep: easing.easeOutCubic(progress) },
  }),
};

// --- Loops / ambient -------------------------------------------------------
const presetLoops: Record<string, PresetBehavior> = {
  float: ({ progress, params, ctx }) => ({
    opacity: 1, dx: 0, dy: Math.sin(ctx.frame / ctx.fps * 1.6) * (params?.amplitude ?? 12), scale: 1, rotate: 0, extra: {},
  }),
  pulse: ({ progress, params, ctx }) => ({
    opacity: 1, dx: 0, dy: 0, scale: 1 + (params?.amplitude ?? 0.04) * Math.sin((ctx.frame / ctx.fps) * 1.5), rotate: 0, extra: {},
  }),
  wiggle: ({ progress, params, ctx }) => ({
    opacity: 1, dx: Math.sin(ctx.frame / ctx.fps * 6) * (params?.amplitude ?? 4), dy: Math.cos(ctx.frame / ctx.fps * 5) * (params?.amplitude ?? 4), scale: 1, rotate: 0, extra: {},
  }),
  'slow-rotate': ({ progress, params, ctx }) => ({
    opacity: 1, dx: 0, dy: 0, scale: 1, rotate: (ctx.frame / ctx.fps) * (params?.speed ?? 0.3), extra: {},
  }),
  shimmer: ({ progress, params, ctx }) => {
    const t = (ctx.frame % ctx.fps) / ctx.fps;
    const sweep = t < 0.5 ? t * 2 : 2 - t * 2;
    return { opacity: 1, dx: 0, dy: 0, scale: 1, rotate: 0, extra: { shimmer: sweep * (params?.amplitude ?? 1) } };
  },
  'parallax-drift': ({ progress, params, ctx }) => ({
    opacity: 1,
    dx: Math.sin((ctx.frame / ctx.fps) * 0.35) * (params?.speed ?? 10),
    dy: Math.cos((ctx.frame / ctx.fps) * 0.3) * (params?.speed ?? 8),
    scale: 1, rotate: 0, extra: {},
  }),
  'breathing-scale': ({ progress, params, ctx }) => ({
    opacity: 1, dx: 0, dy: 0, scale: 1 + (params?.amplitude ?? 0.015) * Math.sin((ctx.frame / ctx.fps) * 1.2), rotate: 0, extra: {},
  }),
  'leaf-drift': ({ progress, ctx }) => ({
    opacity: 1, dx: Math.sin((ctx.frame / ctx.fps) * 0.8 + progress) * 12, dy: Math.sin((ctx.frame / ctx.fps) * 0.5) * 6,
    scale: 1 + Math.sin((ctx.frame / ctx.fps) * 0.9) * 0.02, rotate: Math.sin((ctx.frame / ctx.fps) * 0.3) * 3, extra: {},
  }),
};

// --- Emphasis ---------------------------------------------------------------
const presetEmphasis: Record<string, PresetBehavior> = {
  shake: ({ progress, params, ctx }) => {
    const decay = easing.easeOutQuad(progress);
    return { opacity: 1, dx: Math.sin(ctx.frame * 0.09) * 14 * decay, dy: Math.cos(ctx.frame * 0.07) * 10 * decay, scale: 1, rotate: 0, extra: {} };
  },
  'highlight-sweep': ({ progress, ctx }) => ({
    opacity: 1, dx: 0, dy: 0, scale: 1, rotate: 0, extra: { sweep: progress },
  }),
  'underline-draw': ({ progress }) => ({
    opacity: 1, dx: 0, dy: 0, scale: 1, rotate: 0, extra: { stroke: progress },
  }),
  'color-flash': ({ progress, ctx }) => ({
    opacity: progress + Math.sin(ctx.frame * 0.4) * (1 - progress) * 0.3, dx: 0, dy: 0, scale: 1, rotate: 0, extra: { flash: progress > 0.1 && progress < 0.25 ? 1 - Math.abs(2 * ((ctx.frame / ctx.fps) % 1)) : 0 },
  }),
  'scale-punch': ({ progress, ctx }) => {
    const t = (ctx.frame / ctx.fps) % 1;
    const punch = progress > 0.05 ? 1 - Math.abs(2 * t) : 0;
    return { opacity: 1, dx: 0, dy: 0, scale: 1 + punch * 0.18, rotate: 0, extra: { punch } };
  },
  'draw-on': ({ progress }) => ({
    opacity: 1, dx: 0, dy: 0, scale: 1, rotate: 0, extra: { stroke: clamp01(progress) },
  }),
  'circle-draw-on': ({ progress, ctx }) => {
    const p = clamp01(progress + Math.sin((ctx.frame / ctx.fps) * 0.3) * 0.04);
    return { opacity: 1, dx: 0, dy: 0, scale: 1, rotate: 0, extra: { stroke: p, radius: p * 0.5 } };
  },
  'arrow-draw-on': ({ progress }) => ({
    opacity: 1, dx: 0, dy: 0, scale: 1, rotate: 0, extra: { stroke: clamp01(progress), length: clamp01(progress) },
  }),
};

// --- Exits ------------------------------------------------------------------
const presetExits: Record<string, PresetBehavior> = {
  'slide-out': ({ progress }) => ({
    opacity: 1 - progress, dx: progress * 30, dy: 0, scale: 1, rotate: 0, extra: {},
  }),
  'scale-down': ({ progress }) => ({ opacity: 1 - progress, dx: 0, dy: 0, scale: 1 - progress, rotate: 0, extra: {} }),
  fade: ({ progress }) => ({ opacity: 1 - progress, dx: 0, dy: 0, scale: 1, rotate: 0, extra: {} }),
  'mask-wipe-out': ({ progress }) => ({
    opacity: 1 - progress, dx: 0, dy: 0, scale: 1, rotate: 0, extra: { reveal: 1 - progress },
  }),
  shatter: ({ progress, ctx }) => ({
    opacity: 1 - progress, dx: Math.sin(ctx.frame * 0.09) * 20 * progress, dy: Math.cos(ctx.frame * 0.07) * 18 * progress,
    scale: 1 - progress * 0.5, rotate: Math.sin(ctx.frame * 0.05) * 12 * progress, extra: {},
  }),
  'whip-out': ({ progress, ctx }) => ({
    opacity: 1 - progress, dx: Math.cos(ctx.frame * 0.15) * 40 * progress, dy: 0, scale: 1 + (1 - progress) * 0.15, rotate: 0, extra: {},
  }),
};

// ---------------------------------------------------------------------------
// Registry dispatch
// ---------------------------------------------------------------------------
const PRESET_GROUPS: [Record<string, PresetBehavior>, ...Array<Record<string, PresetBehavior>>] = [presetEntrances, presetLoops, presetEmphasis, presetExits];

export function isPreset(name: unknown): name is AnimPreset {
  return typeof name === 'string' && PRESET_GROUPS.some((g) => name in g);
}

/** Execute a named preset for progress ∈ [0,1] (0 = stage start, 1 = stage end). */
export function execPreset(preset: string, e: ExecParams): ExecResult {
  for (const group of PRESET_GROUPS) {
    const behavior = (group as Record<string, PresetBehavior>)[preset];
    if (behavior) return behavior(e);
  }
  return ENTRANCE_RESULTS; // unknown → no movement
}

/** Progress along a stage with delay, clamped to 0..1. */
export function stageProgress(opts: {
  frame: number; fps: number; delay?: number; duration?: number;
}): number {
  const { frame, fps, delay = 0, duration = 0.4 } = opts;
  const through = (frame - delay * fps) / (duration * fps);
  return clamp01(through);
}

export { easing as motionEasing };
