// Version-2 composition: timeline + layers + keyframes.
import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import type { ProjectSpec, Scene, Layer } from '../../src/types';
import { execPreset, stageProgress, clamp01 } from './animations';
import { getPalette, getStyle } from './styles';
import { execTransition, pickTransition, NO_TRANSITION } from './transitions';

const pct = (v: number) => `${Math.round(v * 100)}%`;
const palette = (spec: ProjectSpec): string[] => getPalette(spec);

// ---------------------------------------------------------------------------
// Scene background — animated gradients / grid / particles
// ---------------------------------------------------------------------------
function AnimatedGradient({ scene, spec, frame }: { scene: Scene; spec: ProjectSpec; frame: number }) {
  const colors = (scene.background.colors as string[]) || palette(spec).slice(0, 3);
  const t = frame / 4;
  const mix = (a: string, b: string, x: number) => {
    const ha = parseInt(a.slice(1), 16), hb = parseInt(b.slice(1), 16);
    const c = (x: number) => Math.round(255 * (ha >> (x * 8 & 24) & 0xff) * (1 - x) + hb * x);
    const r = ((ha >> 16) & 255), g = ((ha >> 8) & 255), bl = (ha & 255);
    const r2 = ((hb >> 16) & 255), g2 = ((hb >> 8) & 255), b2 = (hb & 255);
    const ch = (v1: number, v2: number) => `${Math.round(v1 + (v2 - v1) * x).toString(16).padStart(2, '0')}`;
    return `#${ch(r, r2)}${ch(g, g2)}${ch(bl, b2)}`;
  };
  const stops = [0, 0.5, 1].map((x) => `${mix(colors[0], colors[1] || colors[0], x)} ${((x + Math.sin(t + x * Math.PI) * 0.18) * 100).toFixed(1)}%`);
  return (
    <AbsoluteFill
      style={{
        backgroundImage: `linear-gradient(135deg, ${stops.join(', ')})`,
        opacity: scene.background.opacity != null ? scene.background.opacity as number : 0.9,
      }}
    />
  );
}

function BackgroundGrid({ scene, spec, frame }: { scene: Scene; spec: ProjectSpec; frame: number }) {
  const color = (scene.background.gridColor as string) || palette(spec)[1] || '#7C5CFC';
  const t = frame / fpsSafe(spec);
  const lines = Array.from({ length: 8 }, (_, i) => {
    const s = Math.sin(i * 0.9 + t * 0.6) * 50;
    return i === 0 || i === 7;
  });
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      <div
        style={{
          position: 'absolute', inset: 0,
          backgroundSize: '30% 30%',
          opacity: 0.35,
          backgroundImage: `linear-gradient(90deg, ${color}30 1px, transparent 1px), linear-gradient(${color}30 1px, transparent 1px)`,
          backgroundPosition: `${Math.sin(t) * 10}px ${Math.cos(t * 0.7) * 8}px`,
        }}
      />
    </AbsoluteFill>
  );
}
function fpsSafe(spec: ProjectSpec) { return spec.meta?.fps || 30; }

// ---------------------------------------------------------------------------
// Layers — in_ / loop / out
// ---------------------------------------------------------------------------
interface LayerProps { layer: Layer; frame: number; fps: number; spec: ProjectSpec; exitProg?: number }

function KineticText({ layer, frame, fps, spec, exitProg }: LayerProps) {
  const { in_, loop, out } = layer.animation;
  const inProg = stageProgress({ frame, fps, delay: in_?.delay ?? 0, duration: in_?.duration ?? 0.5 });
  const inResult = execPreset(in_?.preset ?? 'pop-bounce', { progress: inProg, ctx: { fps, frame } });
  const loopResult = loop
    ? execPreset(loop.preset ?? 'float', { progress: 1, params: { amplitude: loop.amplitude ?? 8 }, ctx: { fps, frame } })
    : { opacity: 1, dx: 0, dy: 0, scale: 1, rotate: 0, extra: {} };
  const text = layer.content ?? '';
  const base: React.CSSProperties = {
    position: 'absolute',
    left: pct(layer.position.x),
    top: pct(layer.position.y),
    transform: `translate(-50%, -50%) translate(${inResult.dx}px, ${inResult.dy}px) scale(${inResult.scale}) rotate(${inResult.rotate}deg)`,
    opacity: clamp01((exitProg ?? 1) * inResult.opacity * (loopResult.opacity ?? 1)),
    color: (layer.style?.color as string) || '#F8FAFC',
    fontSize: (layer.style?.fontSize as number) || 40,
    fontWeight: (layer.style?.fontWeight as number) || 700,
    fontFamily: (layer.style?.fontFamily as string) || 'Manrope, sans-serif',
    letterSpacing: (layer.style?.letterSpacing as string) || '-0.02em',
    whiteSpace: 'pre-wrap',
    overflowWrap: 'anywhere',
    userSelect: 'none',
  };

  // Typewriter + mask-reveal + stagger (character by character)
  const chars = text.split('');
  const reveal = clamp01(inResult.extra['reveal'] ?? 1);
  const showChars = (i: number): number => {
    if (i >= chars.length * reveal) return 0;
    return i + 1;
  };
  if (chars.length && (typeof inResult.extra['charCount'] === 'number' || in_?.preset === 'mask-reveal' || layer.animation.stagger)) {
    return (
      <div style={base}>
        {chars.map((ch, i) => (
          <span
            key={i}
            style={{
              opacity: clamp01(showChars(i)),
              transition: 'opacity .06s ease-out',
            }}
          >
            {ch}
          </span>
        ))}
      </div>
    );
  }

  return <div style={base}>{text}</div>;
}

function IconLayer({ layer, frame, fps, spec, exitProg }: LayerProps) {
  const { in_ } = layer.animation;
  const inProg = stageProgress({ frame, fps, delay: in_?.delay ?? 0, duration: in_?.duration ?? 0.4 });
  const r = execPreset(in_?.preset ?? 'elastic-drop', { progress: inProg, ctx: { fps, frame } });
  return (
    <div
      style={{
        position: 'absolute',
        left: pct(layer.position.x), top: pct(layer.position.y),
        transform: `translate(-50%, -50%) translate(${r.dx}px, ${r.dy}px) scale(${r.scale}) rotate(${r.rotate}deg)`,
        opacity: (exitProg ?? 1) * r.opacity,
        color: (layer.style?.color as string) || (palette(spec)[1] as string),
        fontSize: (layer.style?.fontSize as number) || 60,
        textShadow: `0 0 30px ${((layer.style?.color as string) || '#fff')}60`,
      }}
    >
      {layer.content || '✦'}
    </div>
  );
}

function ShapeLayer({ layer, frame, fps, spec, exitProg }: LayerProps) {
  const { in_ } = layer.animation;
  const inProg = stageProgress({ frame, fps, delay: in_?.delay ?? 0, duration: in_?.duration ?? 0.4 });
  const r = execPreset(in_?.preset ?? 'pop-bounce', { progress: inProg, ctx: { fps, frame } });
  const color = (layer.style?.color as string) || palette(spec)[2] || '#7C5CFC';
  return (
    <div style={{ position: 'absolute', left: pct(layer.position.x), top: pct(layer.position.y), transform: `translate(-50%, -50%) scale(${r.scale}) rotate(${r.rotate}deg)`, opacity: (exitProg ?? 1) * r.opacity }}>
      <div style={{ width: (layer.style?.width as number) || 90, height: (layer.style?.width as number) || 90, border: `2px solid ${color}`, borderRadius: (layer.style?.borderRadius as number) ?? 20, boxShadow: `0 0 30px ${color}40`, transform: `rotate(${Math.sin(frame / fps * 2) * 8}deg)` }} />
    </div>
  );
}

function LayerRenderer({ layer, frame, fps, spec, exitProg }: LayerProps) {
  switch (layer.type) {
    case 'text':
    case 'caption': return <KineticText layer={layer} frame={frame} fps={fps} spec={spec} exitProg={exitProg} />;
    case 'icon': return <IconLayer layer={layer} frame={frame} fps={fps} spec={spec} exitProg={exitProg} />;
    case 'shape': return <ShapeLayer layer={layer} frame={frame} fps={fps} spec={spec} exitProg={exitProg} />;
    default:
      return (
        <div style={{ position: 'absolute', left: pct(layer.position.x), top: pct(layer.position.y), opacity: exitProg ?? 1 }}>
          <div style={{ width: 120, height: 70, borderRadius: 12, background: palette(spec)[1], border: `1px solid ${palette(spec)[2] || palette(spec)[1]}` }} />
        </div>
      );
  }
}

// ---------------------------------------------------------------------------
// Scene — background + camera + layers
// ---------------------------------------------------------------------------
function Particles({ frame, fps, spec, n = 6 }: { frame: number; fps: number; spec: ProjectSpec; n?: number }) {
  const p = palette(spec).slice(1);
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      {Array.from({ length: n }, (_, i) => {
        const t = (frame + i * 17) / fps;
        const x = ((Math.sin(t * 0.7 + i) + 1) / 2) * 100;
        const y = ((Math.cos(t * 0.5 + i * 2.3) + 1) / 2) * 100;
        const size = 40 + 60 * Math.abs(Math.sin((frame + i * 13) / fps * 0.8));
        return <div key={i} style={{ position: 'absolute', left: `${x}%`, top: `${y}%`, width: size, height: size, borderRadius: '50%', background: p[i % p.length], filter: 'blur(22px)', opacity: 0.35 }} />;
      })}
    </AbsoluteFill>
  );
}

function GrainOverlay({ frame }: { frame: number }) {
  return (
    <AbsoluteFill style={{ pointerEvents: 'none', opacity: 0.05 }}>
      <div style={{ position: 'absolute', inset: 0, backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect width='100%25' height='100%25' fill='%23000'/%3E%3C/svg%3E")` }} />
      <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(ellipse at 30% 20%, rgba(120,80,255,.2), transparent 60%), radial-gradient(ellipse at 80% 80%, rgba(33,212,167,.15), transparent 55%)` }} />
    </AbsoluteFill>
  );
}

function SceneBackground({ scene, frame, fps, spec }: { scene: Scene; frame: number; fps: number; spec: ProjectSpec }) {
  const type = (scene.background?.type as string) || 'color';
  switch (type) {
    case 'animated-gradient':
      return <AnimatedGradient scene={scene} spec={spec} frame={frame} />;
    case 'grid':
      return <BackgroundGrid scene={scene} spec={spec} frame={frame} />;
    case 'particles':
      return <Particles frame={frame} fps={fps} spec={spec} />;
    case 'image-kenburns':
      return (
        <AbsoluteFill style={{ overflow: 'hidden' }}>
          <div style={{ position: 'absolute', inset: 0, background: palette(spec)[0], transform: `scale(${1.15 + frame / (fps * 12)})`, transformOrigin: 'center', filter: 'blur(30px)' }} />
          <div style={{ position: 'absolute', inset: '-8%', background: palette(spec)[0], transform: `scale(${1 + frame / (fps * 20)})` }} />
        </AbsoluteFill>
      );
    default:
      return <AnimatedGradient scene={scene} spec={spec} frame={frame} />;
  }
}

function SceneRenderer({ scene, frame, fps, spec, enter, exit }: {
  scene: Scene; frame: number; fps: number; spec: ProjectSpec; enter: number; exit: number;
}) {
  const durFrames = Math.max(1, Math.round(scene.duration * fps));
  const f = clamp01(Math.min(frame, durFrames));
  const cam = scene.camera || { move: 'static', intensity: 0 };
  let camera: string = 'none';
  if (cam.move === 'push-in') camera = `scale(${1 + cam.intensity * (f / (fps * 8))})`;
  else if (cam.move === 'orbit') camera = `rotate(${Math.sin(f / fps * 0.25) * cam.intensity * 3}deg)`;
  else if (cam.move === 'pan-left') camera = `translateX(${Math.sin((f / fps) * 0.5) * cam.intensity}px)`;
  else if (cam.move === 'shake') camera = `translate(${Math.sin(f * 0.09) * cam.intensity}px, ${Math.cos(f * 0.07) * cam.intensity}px)`;

  const layers = scene.layers.filter((l) => f >= l.start * fps && f <= l.end * fps);
  return (
    <AbsoluteFill style={{ background: (scene.background as any).color || palette(spec)[0], overflow: 'hidden', opacity: enter * exit }}>
      <SceneBackground scene={scene} frame={f} fps={fps} spec={spec} />
      <GrainOverlay frame={f} />
      <div style={{ position: 'absolute', inset: 0, transform: camera, transformOrigin: 'center' }}>
        {layers.map((l) => <LayerRenderer key={l.id} layer={l} frame={f} fps={fps} spec={spec} />)}
      </div>
    </AbsoluteFill>
  );
}

// ---------------------------------------------------------------------------
// Top level
// ---------------------------------------------------------------------------
export function StudioComposition({ spec }: { spec: ProjectSpec }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  let index = 0;
  let sceneFrame = 0;
  let sceneStart = 0;
  let prev: Scene | null = null;
  let prevStart = 0;
  let prevFrame = 0;
  let prevExit = 0;
  let curEnter = 1;

  for (let i = 0; i < spec.scenes.length; i++) {
    const s = spec.scenes[i];
    const dur = Math.round(s.duration * fps);
    const sStart = sceneStart;
    sceneStart += dur;
    if (frame < sStart + dur) {
      index = i;
      sceneFrame = frame - sStart;
      const tDur = Math.round((s.transition_out?.duration ?? 0.3) * fps);
      curEnter = clamp01(sceneFrame / Math.max(1, tDur));
      if (i > 0) {
        prev = spec.scenes[i - 1];
        prevStart = sStart - Math.round(prev.duration * fps);
        prevFrame = frame - prevStart;
        prevExit = clamp01((frame - (prevStart + Math.round(prev.duration * fps))) / Math.max(1, tDur));
      }
      break;
    }
  }
  const scene = spec.scenes[index] || spec.scenes[0];
  const style = getStyle(spec);
  const W = spec.meta?.width || 1920, H = spec.meta?.height || 1080;
  const tDur = Math.max(1, Math.round((scene.transition_out?.duration ?? 0.3) * fps));
  const curTrans = scene.transition_out?.type || pickTransition({ styleTransitions: style.transitions, prev: prev?.transition_out?.type, seed: index });
  const curEffect = execTransition(curTrans, curEnter, { width: W, height: H, frame, fps });
  const prevTrans = prev?.transition_out?.type;
  const prevEffect = prev ? execTransition(prevTrans || pickTransition({ styleTransitions: style.transitions, prev: curTrans, seed: index + 7 }), prevExit, { width: W, height: H, frame, fps }) : NO_TRANSITION;
  const wrap = (fx: ReturnType<typeof execTransition>, child: React.ReactNode) => (
    <div style={{ position: 'absolute', inset: 0, opacity: fx.opacity, filter: fx.blur ? `blur(${fx.blur}px)` : undefined, transform: fx.rgbSplit ? `translateX(${fx.rgbSplit}px)` : undefined }}>
      {child}
    </div>
  );
  return (
    <AbsoluteFill style={{ background: '#080b12', overflow: 'hidden' }}>
      {wrap(curEffect, <SceneRenderer scene={scene} frame={sceneFrame} fps={fps} spec={spec} enter={curEnter} exit={1} />)}
      {prev && wrap(prevEffect, <SceneRenderer scene={prev} frame={prevFrame} fps={fps} spec={spec} enter={1} exit={prevExit} />)}
    </AbsoluteFill>
  );
}

export const remotionDefaultSpec: ProjectSpec = {
  version: 2,
  title: 'Motion story',
  prompt: '',
  language: 'en',
  meta: { fps: 30, width: 1920, height: 1080, duration: 8, style: 'bold-kinetic' },
  audio: {},
  scenes: [
    { id: 'scene-1', start: 0, duration: 4, background: { type: 'animated-gradient', colors: ['#0B1020', '#7C5CFC', '#21D4A7'] }, camera: { move: 'push-in', intensity: 0.6 },
      layers: [
        { id: 'l1', type: 'text', content: 'Hello world', start: 0.1, end: 3, position: { x: 0.5, y: 0.4 }, animation: { in_: { preset: 'pop-bounce', duration: 0.5 }, loop: { preset: 'float', amplitude: 8 }, out: { preset: 'slide-out', duration: 0.3 } }, style: { color: '#F8FAFC', fontSize: 80 } },
        { id: 'l2', type: 'text', content: 'Your next step', start: 0.8, end: 3, position: { x: 0.5, y: 0.7 }, animation: { in_: { preset: 'fade-up', duration: 0.4 } }, style: { color: '#21D4A7', fontSize: 40 } },
      ], transition_out: { type: 'whip-pan', duration: 0.4 } },
  ],
};
