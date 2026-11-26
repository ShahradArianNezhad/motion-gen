// Visual style presets (design tokens) — 5-6 styles, each defining palette,
// font pair, entrance/loop/transition sets, and default background type.
import type { ProjectSpec, TransitionType } from '../../src/types';

export interface StylePreset {
  name: string;
  description: string;
  palette: string[];
  fonts: { headline: string; body: string };
  radius: number;
  defaultIn: string;           // preset name from animations.ts
  defaultLoop: string;
  defaultBackground: string;   // 'animated-gradient' | 'color' | 'grid' | 'particles'
  transitions: TransitionType[];
  shadow?: string;
}

export const STYLES: Record<string, StylePreset> = {
  'bold-kinetic': {
    name: 'Bold Kinetic',
    description: 'High-contrast, huge type, punchy springs and bold entrances — built for short-form speed.',
    palette: ['#0B1020', '#F8FAFC', '#7C5CFC', '#21D4A7'],
    fonts: { headline: 'Manrope, sans-serif', body: 'Manrope, sans-serif' },
    radius: 12,
    defaultIn: 'pop-bounce',
    defaultLoop: 'float',
    defaultBackground: 'animated-gradient',
    transitions: ['whip-pan', 'flash-cut', 'morph', 'zoom-through'],
  },
  'clean-explainer': {
    name: 'Clean Explainer',
    description: 'Soft shapes, smooth easing, icons and mask reveals — clear, unhurried, trustworthy.',
    palette: ['#F8F5F2', '#1B2735', '#4A7A9A', '#B8C3D6'],
    fonts: { headline: 'DM Sans, sans-serif', body: 'Manrope, sans-serif' },
    radius: 16,
    defaultIn: 'fade-up',
    defaultLoop: 'breathing-scale',
    defaultBackground: 'animated-gradient',
    transitions: ['cross-zoom', 'slide-push', 'morph', 'flash-cut'],
  },
  'neon-cyber': {
    name: 'Neon Cyber',
    description: 'Glow, glitch, rotating grid — electric blues and violets with kinetic typography.',
    palette: ['#050B17', '#A78BFA', '#2DF5C4', '#00F5FF'],
    fonts: { headline: 'Manrope, sans-serif', body: 'Manrope, sans-serif' },
    radius: 6,
    defaultIn: 'glitch-in',
    defaultLoop: 'slow-rotate',
    defaultBackground: 'grid',
    transitions: ['glitch', 'morph', 'flash-cut', 'whip-pan'],
  },
  'editorial-minimal': {
    name: 'Editorial Minimal',
    description: 'Serif-leaning display, mask reveals, subtle motion, generous whitespace.',
    palette: ['#FAFAF8', '#1A1A1A', '#3C3C3C', '#9C9C9C'],
    fonts: { headline: 'Playfair Display, serif', body: 'Manrope, sans-serif' },
    radius: 20,
    defaultIn: 'mask-reveal',
    defaultLoop: 'shimmer',
    defaultBackground: 'color',
    transitions: ['morph', 'cross-zoom', 'shape-wipe'],
  },
  'playful-sticker': {
    name: 'Playful Sticker',
    description: 'Bouncy springs, emoji symbols, hand-drawn strokes, sticker badges — friendly and loud.',
    palette: ['#FFF1D2', '#FF9E6D', '#5CD9A5', '#9CC6FF'],
    fonts: { headline: 'Manrope, sans-serif', body: 'Manrope, sans-serif' },
    radius: 20,
    defaultIn: 'elastic-drop',
    defaultLoop: 'wiggle',
    defaultBackground: 'particles',
    transitions: ['whip-pan', 'flash-cut', 'cross-zoom'],
  },
};

export const STYLE_IDS = Object.keys(STYLES);

export function getStyle(spec: ProjectSpec): StylePreset {
  return STYLES[spec.meta?.style] || STYLES['bold-kinetic'];
}

export function getPalette(spec: ProjectSpec): string[] {
  const style = getStyle(spec);
  return [...style.palette, ...(spec.scenes[0]?.background.colors as string[] || [])];
}
