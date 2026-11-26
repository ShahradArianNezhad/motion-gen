// Scene transition library. Each preset: (progress 0→1) → transform/filter effect.
import { easing } from './animations';
import type { TransitionType, ProjectSpec } from '../../src/types';
import { getStyle } from './styles';

export interface TransitionEffect {
  opacity: number;
  dx: number; dy: number; scale: number; rotate: number;
  blur: number;
  clip: number;             // 0 → 1 reveal progress
  rgbSplit: number;         // horizontal channel offset in px (glitch)
  color: string | null;
}
export const NO_TRANSITION: TransitionEffect = { opacity: 1, dx: 0, dy: 0, scale: 1, rotate: 0, blur: 0, clip: 0, rgbSplit: 0, color: null };

type Fx = (p: number, ctx: { width: number; height: number; frame: number; fps: number }) => TransitionEffect;

const presets: Record<string, Fx> = {
  // Fast whip — directional sweep with blur
  'whip-pan': (p, ctx) => ({
    opacity: easing.easeOutCubic(p), dx: Math.sin(p * Math.PI * 3) * ctx.width * 0.12, dy: 0,
    scale: 1, rotate: 0, blur: Math.max(0, (1 - p) * 16), clip: 0, rgbSplit: 0, color: null,
  }),
  'zoom-through': (p) => ({
    opacity: easing.easeOutExpo(p), scale: easing.easeOutExpo(p) * 1.06, dx: 0, dy: 0,
    rotate: 0, blur: 0, clip: 0, rgbSplit: 0, color: null,
  }),
  glitch: (p, ctx) => ({
    opacity: p, dx: Math.sin(ctx.frame * 0.9) * 8 * Math.abs(1 - p), dy: 0,
    scale: 1, rotate: 0, blur: 0, clip: 0,
    rgbSplit: p > 0.1 && p < 0.3 ? Math.sin((ctx.frame % ctx.fps)) * 4 : 0, color: null,
  }),
  'slide-push': (p) => ({
    opacity: easing.easeOutExpo(p), dx: -easing.easeOutExpo(p) * 15, scale: 1, dy: 0,
    rotate: 0, blur: 0, clip: 0, rgbSplit: 0, color: null,
  }),
  'shape-wipe': (p) => ({
    opacity: easing.easeOutCubic(p), scale: 1, dx: 0, dy: 0, rotate: 0, blur: 0,
    clip: easing.easeOutCubic(p), color: null, rgbSplit: 0,
  }),
  'flash-cut': (p) => ({
    opacity: p >= 0.999 ? 1 : 0, dx: 0, dy: 0, scale: 1, rotate: 0, blur: 0, clip: 0, rgbSplit: 0, color: null,
  }),
  morph: (p) => ({
    opacity: easing.easeOutCubic(p), scale: easing.easeOutBack(p, 1.1), dx: 0, dy: 0, rotate: 0,
    blur: 0, clip: 0, rgbSplit: 0, color: null,
  }),
  'cross-zoom': (p) => ({
    opacity: easing.easeOutExpo(p), scale: easing.easeOutExpo(p) * 1.08, dx: 0, dy: 0, rotate: 0,
    blur: Math.max(0, (1 - p) * 10), clip: 0, rgbSplit: 0, color: null,
  }),
};

/** Execute a transition preset. Unknown → instant cut. */
export function execTransition(type: string, p: number, ctx: { width: number; height: number; frame: number; fps: number }): TransitionEffect {
  const fx = presets[type] || presets['flash-cut'];
  return fx(clamp(p, 0, 1), ctx);
}
function clamp(v: number, lo: number, hi: number) { return v < lo ? lo : v > hi ? hi : v; }

/** Pick a transition for a scene from the style's set, varying on prev and index. */
export function pickTransition(opts: { styleTransitions: TransitionType[]; prev?: string; seed: number }): TransitionType {
  const set = opts.styleTransitions && opts.styleTransitions.length ? opts.styleTransitions : (['flash-cut', 'morph'] as TransitionType[]);
  if (set.length === 1) return set[0];
  let pick = set[opts.seed % set.length];
  if (opts.prev && pick === opts.prev && set.length > 1) {
    pick = set[(opts.seed + 1) % set.length];
  }
  return pick;
}

export { getStyle };
