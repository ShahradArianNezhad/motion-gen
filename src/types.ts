// Version-2 project schema: timeline-based, multi-layer, animated composition
// (scenes + layers + keyframes), the model that motion-gen outputs.

export type LayerType = 'text' | 'image' | 'shape' | 'icon' | 'lottie' | 'video' | 'chart' | 'caption';

// Reusable animation presets executed by the renderer (see renderer/src/animations.ts).
export type AnimPreset =
  // Entrances
  | 'pop-bounce' | 'slide-in' | 'scale-from-zero' | 'fade-up' | 'mask-reveal' | 'rotate-in'
  | 'flip-3d' | 'blur-to-sharp' | 'glitch-in' | 'typewriter' | 'elastic-drop'
  // Loop / ambient
  | 'float' | 'pulse' | 'wiggle' | 'slow-rotate' | 'shimmer' | 'parallax-drift' | 'breathing-scale'
  // Emphasis
  | 'shake' | 'highlight-sweep' | 'underline-draw' | 'color-flash' | 'scale-punch' | 'draw-on'
  // Exits
  | 'slide-out' | 'scale-down' | 'fade' | 'mask-wipe-out' | 'shatter' | 'whip-out';

export type TransitionType =
  | 'whip-pan' | 'zoom-through' | 'glitch' | 'slide-push' | 'shape-wipe'
  | 'flash-cut' | 'morph' | 'cross-zoom';

export interface AnimStage {
  preset?: AnimPreset;      // preset name from the registry
  duration?: number;        // seconds
  delay?: number;           // seconds before the stage starts
  amplitude?: number;       // loop/emphasys presets (e.g. float amplitude, shake size)
  speed?: number;           // loop presets (e.g. parallax speed)
}

export interface LayerAnim {
  in_?: AnimStage;          // animate in on entry
  loop?: AnimStage;         // ambient animation while on screen
  out?: AnimStage;          // animate out on exit
  stagger?: boolean;        // stagger per character/word/line when applicable
}

export interface Layer {
  id: string;
  type: LayerType;
  content?: string;         // text, caption, symbol, etc.
  start: number;            // scene-relative start (seconds)
  end: number;              // scene-relative end (seconds)
  position: { x: number; y: number }; // 0–1, relative to scene dimensions (0.5, 0.5 = center)
  animation: LayerAnim;
  style?: Record<string, unknown>;    // renderer-specific extras (color, size, font, …)
}

export interface BackgroundSpec {
  type: string;             // 'animated-gradient' | 'video' | 'particles' | 'grid' | 'image-kenburns' | 'color' | …
  [key: string]: unknown;   // renderer-specific params (colors, speed, …)
}

export interface CameraSpec {
  move: string;             // 'static' | 'push-in' | 'pan-left' | 'shake' | 'orbit' | …
  intensity: number;        // 0–1
  [key: string]: unknown;
}

export interface Transition {
  type: TransitionType;
  duration?: number;        // seconds (0.2–0.5)
}

export interface Scene {
  id: string;
  start: number;            // timeline start (seconds)
  duration: number;         // seconds
  background: BackgroundSpec;
  camera: CameraSpec;
  layers: Layer[];
  transition_out?: Transition;
}

export interface AudioSfx {
  t: number;                // timeline time (seconds)
  type: string;             // 'whoosh' | 'pop' | 'click' | 'ding' | 'impact' | …
  [key: string]: unknown;
}

export interface AudioSpec {
  voiceover?: string;       // TTS text or uploaded audio path
  music?: string;           // music track hint
  sfx?: AudioSfx[];         // auto-placed sound effects
}

export interface Meta {
  fps: number;
  width: number;
  height: number;
  duration: number;
  style: string;            // style preset id from STYLES (see renderer/src/styles.ts)
}

export interface ProjectSpec {
  version: 2;
  title: string;
  prompt: string;
  language: string;
  meta: Meta;
  audio: AudioSpec;
  scenes: Scene[];
}

export interface Project {
  id: string;
  spec: ProjectSpec;
  updated_at: string;
}
