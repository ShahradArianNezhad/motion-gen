import '@fontsource/dm-sans/400.css';
import '@fontsource/dm-sans/500.css';
import '@fontsource/dm-sans/600.css';
import '@fontsource/dm-sans/700.css';
import '@fontsource/manrope/400.css';
import '@fontsource/manrope/500.css';
import '@fontsource/manrope/600.css';
import '@fontsource/manrope/700.css';
import '@fontsource/manrope/800.css';
import '@fontsource/vazirmatn/400.css';
import '@fontsource/vazirmatn/500.css';
import '@fontsource/vazirmatn/600.css';
import '@fontsource/vazirmatn/700.css';
import '@fontsource/vazirmatn/800.css';
import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  ArrowRight, Check, Clapperboard, Clock3, Cloud, Download, Layers, LoaderCircle,
  MessageCircle, MoreHorizontal, MousePointer2, Music, Palette, Pause, Play, Plus,
  Redo2, Send, Sparkles, Square, Trash2, Type, WandSparkles, X,
} from 'lucide-react';
import { api } from './api';
import { useStudio } from './store';
import type { Layer, ProjectSpec, Scene, TransitionType } from './types';
import './styles.css';

const samplePrompts = [
  'A sleek product launch for an AI note-taking app, midnight blue and electric violet, 18 seconds, landscape',
  'یک ویدیوی تبلیغاتی ۲۰ ثانیه‌ای برای نرم‌افزار مدیریت موجودی، با طراحی مدرن و روایت فارسی',
  'A joyful 15-second launch animation for a sustainable skincare brand, warm colors, vertical',
];
const PRESET_OPTS = [
  'pop-bounce', 'slide-in', 'scale-from-zero', 'fade-up', 'mask-reveal', 'rotate-in',
  'flip-3d', 'blur-to-sharp', 'glitch-in', 'typewriter', 'elastic-drop', 'whip-in',
  'color-sweep', 'float', 'pulse', 'wiggle', 'slow-rotate', 'shimmer', 'parallax-drift',
  'breathing-scale', 'leaf-drift', 'shake', 'highlight-sweep', 'color-flash',
  'scale-punch', 'draw-on', 'circle-draw-on', 'arrow-draw-on', 'underline-draw',
  'slide-out', 'scale-down', 'fade', 'mask-wipe-out', 'shatter', 'whip-out',
];
const TRANSITIONS = ['whip-pan', 'zoom-through', 'glitch', 'slide-push', 'shape-wipe', 'flash-cut', 'morph', 'cross-zoom'];
const RATIOS = ['16:9', '9:16', '1:1'] as const;
type Ratio = typeof RATIOS[number];
type ExportFormat = 'mp4' | 'webm' | 'gif';
type ExportState = { status: 'working' | 'done' | 'error'; message: string; progress?: number; url?: string };

/** Keep scene start times and meta duration in sync with edited scene durations. */
function withTimings(spec: ProjectSpec): ProjectSpec {
  const next = structuredClone(spec);
  let cursor = 0;
  for (const scene of next.scenes) {
    scene.start = Math.round(cursor * 100) / 100;
    cursor += scene.duration;
  }
  next.meta.duration = Math.round(cursor * 100) / 100;
  return next;
}
function sceneStarts(spec: ProjectSpec | null): number[] {
  const starts: number[] = [];
  let cursor = 0;
  for (const scene of spec?.scenes || []) {
    starts.push(cursor);
    cursor += scene.duration;
  }
  return starts;
}
function totalDuration(spec: ProjectSpec | null): number {
  return (spec?.scenes || []).reduce((sum, scene) => sum + scene.duration, 0);
}
function formatTime(seconds: number) {
  const safe = Math.max(0, seconds);
  const m = Math.floor(safe / 60), s = Math.floor(safe % 60), f = Math.floor((safe % 1) * 30);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}:${String(f).padStart(2, '0')}`;
}
function ratioOf(spec: ProjectSpec | null): Ratio {
  const meta = spec?.meta;
  if (meta?.aspect_ratio === '9:16' || meta?.aspect_ratio === '1:1') return meta.aspect_ratio;
  if (meta && meta.height > meta.width) return '9:16';
  if (meta && meta.height === meta.width) return '1:1';
  return '16:9';
}
function animationClass(preset?: string) {
  if (!preset || preset === 'none') return '';
  if (['fade-up', 'slide-in', 'mask-reveal', 'whip-in', 'typewriter', 'draw-on'].includes(preset)) return 'anim-rise';
  if (['fade', 'blur-to-sharp', 'underline-draw', 'arrow-draw-on', 'shimmer'].includes(preset)) return 'anim-reveal';
  if (['pop-bounce', 'scale-from-zero', 'scale-punch', 'flip-3d', 'rotate-in', 'shatter'].includes(preset)) return 'anim-scale';
  if (['float', 'parallax-drift', 'leaf-drift', 'slide-out', 'whip-out', 'scale-down'].includes(preset)) return 'anim-drift';
  return 'anim-pulse';
}

export default function App() {
  const {
    spec, projectId, setProject, setSpec, selectedScene, setScene, selectedLayer, select,
    addLayer, setLayer, undo, redo, history, future,
  } = useStudio();
  const [screen, setScreen] = useState<'home' | 'editor'>('home');
  const [prompt, setPrompt] = useState('');
  const [duration, setDuration] = useState(20);
  const [ratio, setRatio] = useState<Ratio>('16:9');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [projects, setProjects] = useState<any[]>([]);
  const [health, setHealth] = useState<{ llm_configured: boolean } | null>(null);
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [assistant, setAssistant] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatLog, setChatLog] = useState<{ role: string; text: string }[]>([]);
  const [exportFormat, setExportFormat] = useState<ExportFormat>('mp4');
  const [exportState, setExportState] = useState<ExportState | null>(null);
  const [tool, setTool] = useState('select');

  const starts = useMemo(() => sceneStarts(spec), [spec]);
  const total = totalDuration(spec);
  const activeScene = spec?.scenes[selectedScene] || spec?.scenes[0];
  const sceneTime = Math.max(0, time - (starts[selectedScene] || 0));

  useEffect(() => {
    api.projects().then(setProjects).catch(() => {});
    api.health().then(setHealth).catch(() => {});
  }, []);
  useEffect(() => {
    if (!spec || !projectId || screen !== 'editor') return;
    const timer = setTimeout(() => api.save(projectId, withTimings(spec)).catch(() => {}), 750);
    return () => clearTimeout(timer);
  }, [spec, projectId, screen]);
  useEffect(() => {
    if (!playing || !total) return;
    const timer = setInterval(() => setTime((value) => {
      if (value + 0.1 >= total) {
        setPlaying(false);
        return 0;
      }
      return value + 0.1;
    }), 100);
    return () => clearInterval(timer);
  }, [playing, total]);

  async function createProject(text = prompt) {
    if (!text.trim()) return;
    setGenerating(true);
    setError('');
    try {
      const result = await api.generate(text, duration, ratio);
      const normalized = withTimings(result.spec);
      const saved = await api.save(result.id, normalized);
      setProject(saved.id, saved.spec);
      setScreen('editor');
      setTime(0);
      setPlaying(false);
      setExportState(null);
      setChatLog([]);
      setProjects(await api.projects());
    } catch (e: any) {
      setError(e.message || 'Generation failed. Please try again.');
    } finally {
      setGenerating(false);
    }
  }
  async function openProject(id: string) {
    try {
      const project = await api.getProject(id);
      setProject(project.id, withTimings(project.spec));
      setScreen('editor');
      setTime(0);
      setPlaying(false);
      setExportState(null);
      setChatLog([]);
    } catch (e: any) {
      setError(e.message);
    }
  }
  async function removeProject(id: string) {
    if (!confirm('Delete this project?')) return;
    await api.remove(id);
    setProjects(await api.projects());
  }
  async function sendEdit(command = chatInput) {
    if (!projectId || !command.trim()) return;
    const text = command.trim();
    setChatInput('');
    setChatLog((log) => [...log, { role: 'user', text }]);
    try {
      // Persist pending edits first so the assistant sees the current spec.
      await api.save(projectId, withTimings(spec!));
      const response = await api.edit(projectId, text, selectedLayer || undefined);
      setSpec(withTimings(response.project.spec));
      setChatLog((log) => [...log, { role: 'assistant', text: response.message }]);
    } catch (e: any) {
      setChatLog((log) => [...log, { role: 'assistant', text: e.message }]);
    }
  }
  function addTextLayer() {
    addLayer({
      id: `layer-${Date.now()}`, type: 'text', content: 'Text', start: 0.2, end: 4,
      position: { x: 0.5, y: 0.5 },
      animation: { in_: { preset: 'pop-bounce', duration: 0.5 }, loop: { preset: 'float', amplitude: 8 } },
    });
  }
  function addShapeLayer() {
    addLayer({
      id: `shape-${Date.now()}`, type: 'shape', start: 0.2, end: 4,
      position: { x: 0.5, y: 0.6 },
      animation: { in_: { preset: 'pop-bounce', duration: 0.4 } },
    });
  }
  function addScene() {
    if (!spec) return;
    const next = withTimings(spec);
    const index = selectedScene;
    const source = next.scenes[index] || next.scenes[0];
    const id = `scene-${Date.now()}`;
    next.scenes.splice(index + 1, 0, {
      id, start: 0, duration: 4,
      background: { type: 'animated-gradient', colors: (source?.background?.colors as string[]) || ['#0B1020', '#7C5CFC'] },
      camera: { move: 'push-in', intensity: 0.5 },
      layers: [{
        id: `l-${Date.now()}`, type: 'text', content: 'New headline', start: 0, end: 4,
        position: { x: 0.5, y: 0.5 },
        animation: { in_: { preset: 'pop-bounce', duration: 0.5 } },
      }],
      transition_out: { type: 'whip-pan', duration: 0.3 },
    });
    setSpec(withTimings(next));
    setScene(index + 1);
    setTime(starts[index + 1] ?? 0);
  }
  function seek(next: number) {
    setTime(Math.max(0, Math.min(total, next)));
  }

  /** Render through the API job queue, then offer the artifact the worker actually produced. */
  async function exportVideo() {
    if (!projectId || !spec || exportState?.status === 'working') return;
    setExportState({ status: 'working', message: 'Saving project…', progress: 0 });
    try {
      const saved = await api.save(projectId, withTimings(spec));
      const job = await api.export(saved.id, exportFormat);
      setExportState({ status: 'working', message: 'Queued for rendering…', progress: 0 });
      const deadline = Date.now() + 16 * 60 * 1000;
      while (Date.now() < deadline) {
        await new Promise((resolve) => setTimeout(resolve, 1200));
        const status = await api.job(job.id);
        if (status.status === 'completed' && status.download_url) {
          setExportState({ status: 'done', message: `${exportFormat.toUpperCase()} ready`, url: status.download_url });
          return;
        }
        if (status.status === 'failed') {
          throw new Error(status.error || 'Rendering failed. Check the API logs.');
        }
        setExportState({
          status: 'working',
          message: status.status === 'rendering' ? 'Rendering video…' : 'Waiting for a render worker…',
          progress: status.progress || 0,
        });
      }
      throw new Error('Rendering took too long. Check the API logs and try again.');
    } catch (e: any) {
      setExportState({ status: 'error', message: e.message || 'Export failed. Please try again.' });
    }
  }

  if (screen === 'editor' && spec) {
    const layers = activeScene?.layers || [];
    const updateScene = (patch: Partial<Scene>) => {
      const next = withTimings(spec);
      Object.assign(next.scenes[selectedScene], patch);
      setSpec(next);
    };
    const updateLayer = (patch: Partial<Layer>) => setLayer(selectedLayer!, patch);
    const deleteLayer = () => {
      const next = withTimings(spec);
      next.scenes[selectedScene].layers = next.scenes[selectedScene].layers.filter((layer) => layer.id !== selectedLayer);
      setSpec(next);
      select(null);
    };

    return (
      <div className="studio-app">
        <header className="studio-topbar">
          <button className="back-home" onClick={() => { setScreen('home'); setPlaying(false); api.projects().then(setProjects); }}>
            <span>motion<span className="brand-light">studio</span></span>
          </button>
          <span className="top-divider" />
          <div className="project-title-area">
            <input
              className="project-title-input" value={spec.title}
              onChange={(e) => setSpec({ ...spec, title: e.target.value })}
            />
            <span className="save-status"><Cloud size={12} /> Autosaved locally</span>
          </div>
          <div className="top-actions">
            <button className="top-icon" title="Undo" disabled={!history.length} onClick={undo}><span>↩</span></button>
            <button className="top-icon" title="Redo" disabled={!future.length} onClick={redo}><span>↪</span></button>
            <button className={`share-button ${assistant ? 'active' : ''}`} onClick={() => setAssistant((value) => !value)}>
              <MessageCircle size={15} /> AI assistant
            </button>
            <div className="export-group">
              <select aria-label="Export format" value={exportFormat} onChange={(e) => setExportFormat(e.target.value as ExportFormat)}>
                <option value="mp4">MP4</option>
                <option value="webm">WebM</option>
                <option value="gif">GIF</option>
              </select>
              <button className="export-button" onClick={exportVideo} disabled={exportState?.status === 'working'}>
                {exportState?.status === 'working' ? <><LoaderCircle className="spin" size={14} /> Rendering…</> : <>Export <Download size={14} /></>}
              </button>
            </div>
          </div>
        </header>

        <div className={`workspace ${assistant ? '' : 'assistant-collapsed'}`}>
          <nav className="tool-rail" aria-label="Editor tools">
            <button className={`rail-button ${tool === 'select' ? 'active' : ''}`} title="Select" onClick={() => { setTool('select'); select(null); }}>
              <MousePointer2 size={16} /><span>Select</span>
            </button>
            <button className={`rail-button ${tool === 'text' ? 'active' : ''}`} title="Add text" onClick={() => { setTool('text'); addTextLayer(); }}>
              <Type size={16} /><span>Text</span>
            </button>
            <button className={`rail-button ${tool === 'shapes' ? 'active' : ''}`} title="Add shape" onClick={() => { setTool('shapes'); addShapeLayer(); }}>
              <Square size={15} /><span>Shape</span>
            </button>
            <button className={`rail-button ${tool === 'design' ? 'active' : ''}`} title="Design" onClick={() => setTool('design')}>
              <Palette size={16} /><span>Design</span>
            </button>
            <button className={`rail-button ${tool === 'audio' ? 'active' : ''}`} title="Audio" onClick={() => setTool('audio')}>
              <Music size={16} /><span>Audio</span>
            </button>
            <a className="rail-button" href="/assets" title="Asset library"><Sparkles size={16} /><span>Assets</span></a>
            <div className="rail-bottom">
              <button title="Undo" disabled={!history.length} onClick={undo}>↩</button>
              <button title="Redo" disabled={!future.length} onClick={redo}>↪</button>
              <div className="avatar mini">M</div>
            </div>
          </nav>

          {assistant && (
            <aside className="assistant-panel">
              <div className="panel-header">
                <div><Sparkles size={15} /><strong>AI assistant</strong></div>
                <button className="icon-quiet" title="Close assistant" onClick={() => setAssistant(false)}><X size={16} /></button>
              </div>
              <div className="assistant-context">
                <b>Working on {activeScene?.id || 'this project'}</b>
                <small><span className="context-dot" />{layers.length} layers · {formatTime(total)} total</small>
              </div>
              <div className="chat-content">
                <div className="assistant-welcome">
                  <div className="welcome-spark"><WandSparkles size={16} /></div>
                  <b>Tell me what to change.</b>
                  <p>Try “make it darker”, “more dramatic”, “slow the pacing”, or “recolor accents”.</p>
                </div>
                {chatLog.map((message, index) => (
                  <div className={`chat-bubble ${message.role}`} key={index}>{message.text}</div>
                ))}
              </div>
              <div className="suggestion-chips">
                {['Make it darker', 'More dramatic', 'Slow down'].map((suggestion) => (
                  <button key={suggestion} onClick={() => sendEdit(suggestion)}>{suggestion}</button>
                ))}
              </div>
              <div className="chat-compose">
                <textarea
                  value={chatInput} placeholder="Describe an edit…"
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendEdit(); } }}
                />
                <button title="Send" disabled={!chatInput.trim()} onClick={() => sendEdit()}><Send size={14} /></button>
              </div>
              <div className="safe-edit-note"><Check size={12} /> Your existing edits stay yours</div>
            </aside>
          )}

          <main className="editor-main">
            <div className="editor-toolbar">
              <div className="breadcrumb"><Clapperboard size={12} /><b>{spec.title || 'Untitled'}</b> / {activeScene?.id}</div>
              <div className="toolbar-right">
                <span className="ratio-badge">{ratioOf(spec)}</span>
                <span className="ratio-badge">{spec.meta.style} · {spec.meta.fps} fps</span>
              </div>
            </div>

            <StudioPreview
              spec={spec} scene={activeScene} time={sceneTime} selectedLayer={selectedLayer}
              onSelectLayer={select} playing={playing}
            />

            <div className="transport">
              <div className="transport-left">
                <button
                  className="transport-play" title={playing ? 'Pause' : 'Play'}
                  onClick={() => { setPlaying((value) => !value); if (!playing && time >= total) setTime(0); }}
                >
                  {playing ? <Pause size={14} fill="currentColor" /> : <Play size={14} fill="currentColor" />}
                </button>
                <span className="timecode">{formatTime(time)} <i>/</i> {formatTime(total)}</span>
              </div>
              <div
                className="scrub-area" title="Scrub timeline"
                onClick={(e) => {
                  const bounds = e.currentTarget.getBoundingClientRect();
                  seek(total * (e.clientX - bounds.left) / bounds.width);
                }}
              >
                <div className="scrub-track"><span style={{ width: `${total ? time / total * 100 : 0}%` }} /></div>
                <div className="scrub-knob" style={{ left: `${total ? time / total * 100 : 0}%` }} />
              </div>
            </div>

            <div className="timeline-panel">
              <div className="timeline-head">
                <div><Layers size={15} /><b>Timeline</b><span className="scene-counter">{spec.scenes.length} scenes</span></div>
                <div className="timeline-tools"><button title="Add scene" onClick={addScene}><Plus size={15} /></button></div>
              </div>
              <div className="tracks">
                <div className="track-labels">
                  <span><Layers size={10} /> SCENES</span>
                  {layers.map((layer) => <span key={layer.id}>{layer.type}</span>)}
                  <span><Music size={10} /> AUDIO</span>
                </div>
                <div className="track-content">
                  {total > 0 && <div className="playhead" style={{ left: `${time / total * 100}%` }} />}
                  <div className="scene-track">
                    {spec.scenes.map((scene, index) => (
                      <button
                        className={`scene-block ${selectedScene === index ? 'selected' : ''}`}
                        key={scene.id}
                        style={{ flex: `${scene.duration} 1 0%` }}
                        onClick={() => { setScene(index); seek(starts[index] || 0); setPlaying(false); }}
                      >
                        <span className="scene-num">{String(index + 1).padStart(2, '0')}</span>
                        <strong>{scene.id}</strong>
                        <small>{scene.duration.toFixed(1)}s</small>
                        <div className={`mini-art mini-${index % 4}`}>
                          <span>{scene.layers?.[0]?.content?.slice(0, 22) || 'Scene'}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                  <div className="layer-track">
                    {layers.length === 0 && <div className="no-layers">No layers in this scene — add one in the inspector.</div>}
                    {layers.map((layer) => (
                      <div className="layer-row" key={layer.id}>
                        <div className="layer-name"><span className="layer-color" />{layer.type} · {layer.id}</div>
                        <div className="layer-bars">
                          <button
                            title={`${layer.content || layer.type} (${layer.start}s – ${layer.end}s)`}
                            onClick={() => select(layer.id)}
                            style={{
                              marginLeft: `${total ? ((starts[selectedScene] || 0) + layer.start) / total * 100 : 0}%`,
                              flex: `${total ? Math.max(0.5, layer.end - layer.start) / total * 100 : 10} 1 0%`,
                            }}
                          ><span /></button>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="audio-track">
                    <div className="audio-track-label"><Music size={9} /> NARRATION</div>
                    <div className="audio-empty"><span /><span /><span /><small>{spec.audio.voiceover ? 'VOICEOVER SCRIPT SET' : 'NO VOICEOVER · SFX GENERATED'}</small></div>
                  </div>
                </div>
              </div>
              <div className="timeline-footer">
                <span><span className="tiny-dot" /> Auto-saved</span>
                <span>{spec.meta.width} × {spec.meta.height} · {spec.meta.fps} fps</span>
                <span className="duration-total">Duration <b>{formatTime(total)}</b></span>
              </div>
            </div>
          </main>

          <aside className="inspector">
            <div className="inspector-top">
              <div>
                <span className="section-eyebrow">{selectedLayer ? 'LAYER PROPERTIES' : 'SCENE PROPERTIES'}</span>
                <h3>{selectedLayer ? layers.find((layer) => layer.id === selectedLayer)?.type : activeScene?.id}</h3>
              </div>
              {selectedLayer && <button className="icon-quiet" title="Deselect layer" onClick={() => select(null)}><X size={14} /></button>}
            </div>
            {selectedLayer && layers.find((layer) => layer.id === selectedLayer) ? (
              <LayerEditor
                layer={layers.find((layer) => layer.id === selectedLayer)!}
                update={updateLayer} onDelete={deleteLayer}
              />
            ) : (
              <SceneEditor scene={activeScene} update={updateScene} onAdd={addTextLayer} />
            )}
            <div className="inspector-divider" />
            <div className="layers-heading"><div><Layers size={13} /><b>Layers</b></div><span>{layers.length}</span></div>
            <div className="layer-list">
              {layers.slice().reverse().map((layer) => (
                <button
                  className={`layer-item ${selectedLayer === layer.id ? 'active' : ''}`}
                  key={layer.id}
                  onClick={() => select(layer.id)}
                >
                  <span className={`layer-icon type-${layer.type}`}>
                    {layer.type === 'text' || layer.type === 'caption' ? <Type size={12} /> : layer.type === 'shape' ? <Square size={11} /> : <Layers size={11} />}
                  </span>
                  <span className="layer-item-text">
                    <b>{layer.type}</b>
                    <small>{layer.content || `${layer.start}s – ${layer.end}s`}</small>
                  </span>
                </button>
              ))}
              <button className="layer-add" onClick={addTextLayer}><Plus size={14} /> Add text layer</button>
            </div>
            <div className="inspector-bottom">
              <span><span className="tiny-dot" /> Editable timeline</span>
              <button onClick={addShapeLayer}>+ Shape</button>
            </div>
          </aside>

          {error && (
            <div className="toast-error"><span>{error}</span><button onClick={() => setError('')}><X size={15} /></button></div>
          )}
          {exportState && (
            <div className={`export-toast ${exportState.status === 'error' ? 'toast-error' : ''}`}>
              {exportState.status === 'working' ? <LoaderCircle className="spin" size={15} /> : <Check size={15} />}
              <span>
                {exportState.status === 'working'
                  ? `${exportState.message}${exportState.progress ? ` ${exportState.progress}%` : ''}`
                  : exportState.message}
              </span>
              {exportState.url && (
                <a href={exportState.url} download title="Download rendered video">
                  Download <Download size={13} />
                </a>
              )}
              <button title="Dismiss" onClick={() => setExportState(null)}><X size={14} /></button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <main className="home-screen">
      <header className="home-nav">
        <div className="brand"><div className="brand-mark"><Clapperboard size={18} /></div><span>motion<span className="brand-light">studio</span></span><span className="beta-pill">BETA</span></div>
        <div className="nav-right"><div className="system-status"><span className="status-dot" />{health?.llm_configured ? 'AI engine connected' : 'Studio ready'}</div><button className="avatar">M</button></div>
      </header>
      <section className="hero">
        <div className="hero-kicker"><span className="sparkle-dot"><Sparkles size={13} /></span> YOUR CREATIVE CO-PILOT</div>
        <h1>Make your ideas<br /><span>move.</span></h1>
        <p className="hero-sub">Turn a few words into a motion story worth watching.</p>
        <div className="prompt-card">
          <div className="prompt-head"><div className="prompt-orb"><WandSparkles size={17} /></div><span>Describe the video you imagine</span></div>
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="A product launch, a bold brand story, an idea brought to life…" rows={3} disabled={generating} />
          <div className="prompt-footer">
            <div className="generation-settings">
              <label><Clock3 size={14} /><select aria-label="Duration" value={duration} onChange={(e) => setDuration(Number(e.target.value))}>{[10, 15, 20, 30, 45, 60].map((n) => <option key={n} value={n}>{n} sec</option>)}</select><span className="setting-separator" /></label>
              <label><Square size={13} /><select aria-label="Aspect ratio" value={ratio} onChange={(e) => setRatio(e.target.value as Ratio)}>{RATIOS.map((item) => <option key={item} value={item}>{item}</option>)}</select><span className="setting-separator" /></label>
            </div>
            <button className="primary-button" onClick={() => createProject()} disabled={!prompt.trim() || generating}>
              {generating ? <><LoaderCircle className="spin" size={16} /> Creating…</> : <>Generate story <ArrowRight size={16} /></>}
            </button>
          </div>
          {generating && <div className="generation-progress"><span className="progress-line" /><span>Generating your v2 timeline plan…</span></div>}
        </div>
        {error && <div className="error-banner"><span>{error}</span><button onClick={() => setError('')}><X size={15} /></button></div>}
        <div className="examples">
          <span className="example-label">TRY A PROMPT</span>
          {samplePrompts.map((example, index) => (
            <button
              key={index}
              onClick={() => { setPrompt(example); setRatio(index === 2 ? '9:16' : '16:9'); setDuration(index === 0 ? 18 : 20); }}
            >
              {index === 1 ? 'فارسی' : index === 2 ? 'Product story' : 'SaaS launch'} <ArrowRight size={12} />
            </button>
          ))}
        </div>
      </section>
      <section className="projects-section">
        <div className="section-heading">
          <div><span className="section-eyebrow">YOUR WORKSPACE</span><h2>Recent projects <span className="count-badge">{projects.length.toString().padStart(2, '0')}</span></h2></div>
          <button className="text-button" onClick={() => document.querySelector<HTMLTextAreaElement>('.prompt-card textarea')?.focus()}>New project <Plus size={15} /></button>
        </div>
        {projects.length ? (
          <div className="project-grid">
            {projects.map((project, index) => (
              <article className="project-card" key={project.id}>
                <button className={`project-art art-${index % 4}`} onClick={() => openProject(project.id)}>
                  <div className="art-noise" />
                  <span className="art-kicker">MOTION STUDY · {String(index + 1).padStart(2, '0')}</span>
                  <strong>{project.title}</strong>
                  <span className="art-open"><ArrowRight size={16} /></span>
                </button>
                <div className="project-meta">
                  <button onClick={() => openProject(project.id)}>
                    <strong>{project.title}</strong>
                    <span>Edited {new Date(project.updated_at).toLocaleDateString()} · {project.scene_count} scenes</span>
                  </button>
                  <button title="Delete project" className="icon-quiet" onClick={() => removeProject(project.id)}><MoreHorizontal size={17} /></button>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-projects">
            <div className="empty-icon"><Layers size={20} /></div>
            <div><strong>Your canvas is waiting.</strong><p>Start with a prompt above — your projects will find a home here.</p></div>
            <ArrowRight size={16} />
          </div>
        )}
      </section>
      <footer className="home-footer"><span>DESIGNED FOR THE BIG IDEA.</span><span>AI MOTION GRAPHICS STUDIO ✦ 2025</span></footer>
    </main>
  );
}

/** Live, editable canvas preview built from the validated scene/layer spec. */
function StudioPreview({
  spec, scene, time, selectedLayer, onSelectLayer, playing,
}: {
  spec: ProjectSpec;
  scene?: Scene;
  time: number;
  selectedLayer: string | null;
  onSelectLayer: (id: string | null) => void;
  playing: boolean;
}) {
  const colors = ((scene?.background?.colors as string[] | undefined) || ['#0B1020', '#7C5CFC']).filter(Boolean);
  const background = scene?.background?.type === 'color'
    ? colors[0] || '#0B1020'
    : `linear-gradient(135deg, ${colors.join(', ')})`;
  const ratio = ratioOf(spec);
  const visible = (scene?.layers || []).filter((layer) => time + 0.001 >= layer.start && time <= layer.end + (layer.end - layer.start) * 0.35);
  const ratioClass = ratio === '9:16' ? 'ratio-9-16' : ratio === '1:1' ? 'ratio-1-1' : '';

  return (
    <div className="canvas-zone">
      <div
        className={`preview-frame ${ratioClass}`}
        style={{ '--scene-bg': colors[0] || '#0B1020', background } as React.CSSProperties}
        onClick={() => onSelectLayer(null)}
      >
        <div className="preview-grid" />
        {colors[1] && <span className="preview-glow glow-a" style={{ background: colors[1] }} />}
        {colors[2] && <span className="preview-glow glow-b" style={{ background: colors[2] }} />}
        <div className="preview-side-mark"><i /> MOTION STUDY / {scene?.id?.toUpperCase()}</div>
        {visible.map((layer) => {
          const style = layer.style || {};
          const color = typeof style.color === 'string' ? style.color : '#ffffff';
          const fontSize = typeof style.fontSize === 'number' ? style.fontSize : 56;
          const fontWeight = typeof style.fontWeight === 'number' ? style.fontWeight : 700;
          const fontFamily = typeof style.fontFamily === 'string' ? style.fontFamily : undefined;
          const className = [
            'canvas-element',
            selectedLayer === layer.id ? 'element-selected' : '',
            animationClass(playing ? layer.animation?.loop?.preset : layer.animation?.in_?.preset),
          ].filter(Boolean).join(' ');
          const layerStyle: React.CSSProperties = {
            left: `${Math.max(0, Math.min(1, layer.position.x)) * 100}%`,
            top: `${Math.max(0, Math.min(1, layer.position.y)) * 100}%`,
            color,
            fontSize: `${Math.max(1.6, fontSize / 19.2)}cqw`,
            fontWeight,
            fontFamily,
          };
          return (
            <button
              key={`${layer.id}-${playing ? 'loop' : 'in'}`}
              className={className}
              style={layerStyle}
              title={`${layer.type}: ${layer.content || ''}`}
              onClick={(event) => { event.stopPropagation(); onSelectLayer(layer.id); }}
            >
              {layer.type === 'shape'
                ? <span className="shape-element" style={{ borderColor: color, boxShadow: `0 0 20px ${color}` }} />
                : layer.content || (layer.type === 'icon' ? '✦' : '')}
            </button>
          );
        })}
        <div className="preview-watermark"><span /> COMPOSITION PREVIEW</div>
      </div>
      <div className="preview-caption">
        <div>
          <span className="caption-indicator" />
          <strong>{scene?.id || 'Scene'}</strong>
          <span>{visible.length} visible layer{visible.length === 1 ? '' : 's'} · {scene?.duration?.toFixed(1) || 0}s</span>
        </div>
        <span>{ratio} · {spec.meta.width}×{spec.meta.height}</span>
      </div>
    </div>
  );
}

function LayerEditor({ layer, update, onDelete }: {
  layer: Layer;
  update: (patch: Partial<Layer>) => void;
  onDelete: () => void;
}) {
  const style = layer.style || {};
  const setAnim = (key: 'in_' | 'loop' | 'out', value: any) => update({ animation: { ...layer.animation, [key]: value } } as Partial<Layer>);
  const setStyle = (patch: Record<string, unknown>) => update({ style: { ...style, ...patch } });
  const color = typeof style.color === 'string' ? style.color : '#ffffff';
  const fontSize = typeof style.fontSize === 'number' ? style.fontSize : 56;

  return (
    <div className="prop-scroll">
      <div className="prop-section">
        <label className="field-label">TYPE &amp; CONTENT</label>
        <select className="full-select" value={layer.type} onChange={(e) => update({ type: e.target.value as Layer['type'] })}>
          {['text', 'caption', 'image', 'shape', 'icon', 'lottie', 'video', 'chart'].map((type) => <option key={type}>{type}</option>)}
        </select>
        <textarea className="property-text" value={layer.content || ''} onChange={(e) => update({ content: e.target.value })} dir="auto" />
      </div>
      <div className="prop-section">
        <label className="field-label">TIMING</label>
        <div className="prop-two">
          {(['start', 'end'] as const).map((key) => (
            <label key={key}>{key}
              <div className="number-input">
                <input type="number" step="0.1" min="0" value={layer[key] ?? 0} onChange={(e) => update({ [key]: Number(e.target.value) } as Partial<Layer>)} />
                <span>s</span>
              </div>
            </label>
          ))}
        </div>
      </div>
      <div className="prop-section">
        <label className="field-label">POSITION (0–1)</label>
        <div className="prop-grid">
          {(['x', 'y'] as const).map((axis) => (
            <label key={axis}>{axis.toUpperCase()}
              <div>
                <input
                  type="number" step="0.01" min="0" max="1" value={layer.position[axis]}
                  onChange={(e) => update({ position: { ...layer.position, [axis]: Number(e.target.value) } })}
                />
              </div>
            </label>
          ))}
        </div>
      </div>
      <div className="prop-section">
        <label className="field-label">TYPOGRAPHY &amp; COLOR</label>
        <div className="color-prop">
          <span>Text color</span>
          <label className="color-control">
            <input type="color" value={/^#[0-9a-f]{6}$/i.test(color) ? color : '#ffffff'} onChange={(e) => setStyle({ color: e.target.value })} />
            <code>{color}</code>
          </label>
        </div>
        <div className="prop-two">
          <label>Font size
            <div className="number-input"><input type="number" min="8" max="400" value={fontSize} onChange={(e) => setStyle({ fontSize: Number(e.target.value) })} /><span>px</span></div>
          </label>
          <label>Weight
            <select className="full-select" value={String(style.fontWeight || 700)} onChange={(e) => setStyle({ fontWeight: Number(e.target.value) })}>
              {[400, 500, 600, 700, 800].map((weight) => <option key={weight} value={weight}>{weight}</option>)}
            </select>
          </label>
        </div>
      </div>
      <div className="prop-section">
        <label className="field-label">ANIMATION IN</label>
        <select className="full-select" value={layer.animation.in_?.preset || 'pop-bounce'} onChange={(e) => setAnim('in_', { ...(layer.animation.in_ || {}), preset: e.target.value })}>
          {['none', ...PRESET_OPTS].map((preset) => <option key={preset}>{preset}</option>)}
        </select>
        <label className="field-label" style={{ marginTop: 12 }}>LOOP</label>
        <select className="full-select" value={layer.animation.loop?.preset || 'none'} onChange={(e) => setAnim('loop', e.target.value === 'none' ? undefined : { ...(layer.animation.loop || {}), preset: e.target.value })}>
          {['none', ...PRESET_OPTS].map((preset) => <option key={preset}>{preset}</option>)}
        </select>
        <label className="field-label" style={{ marginTop: 12 }}>ANIMATION OUT</label>
        <select className="full-select" value={layer.animation.out?.preset || 'fade'} onChange={(e) => setAnim('out', { ...(layer.animation.out || {}), preset: e.target.value })}>
          {['none', ...PRESET_OPTS].map((preset) => <option key={preset}>{preset}</option>)}
        </select>
      </div>
      <button className="delete-layer" onClick={onDelete}><Trash2 size={14} /> Delete layer</button>
    </div>
  );
}

function SceneEditor({ scene, update, onAdd }: {
  scene?: Scene;
  update: (patch: Partial<Scene>) => void;
  onAdd: () => void;
}) {
  if (!scene) return <div className="prop-scroll" />;
  const colors = ((scene.background?.colors as string[] | undefined) || ['#0B1020', '#7C5CFC']).slice(0, 3);
  const setColors = (index: number, value: string) => {
    const next = [...colors];
    next[index] = value;
    update({ background: { ...scene.background, colors: next } });
  };
  return (
    <div className="prop-scroll">
      <div className="scene-prop-title">
        <div className="scene-prop-thumb"><Clapperboard size={15} /></div>
        <div><b>{scene.id}</b><small>Scene starts at {scene.start.toFixed(1)}s · {scene.layers?.length || 0} layers</small></div>
      </div>
      <div className="prop-section">
        <label className="field-label">BACKGROUND</label>
        <select className="full-select" value={scene.background?.type || 'animated-gradient'} onChange={(e) => update({ background: { ...scene.background, type: e.target.value } })}>
          {['animated-gradient', 'color', 'grid', 'particles', 'image-kenburns'].map((type) => <option key={type}>{type}</option>)}
        </select>
        {colors.map((color, index) => (
          <div className="color-prop" key={index} style={{ marginTop: 10 }}>
            <span>Color {index + 1}</span>
            <label className="color-control">
              <input type="color" value={/^#[0-9a-f]{6}$/i.test(color) ? color : '#7C5CFC'} onChange={(e) => setColors(index, e.target.value)} />
              <code>{color}</code>
            </label>
          </div>
        ))}
      </div>
      <div className="prop-section">
        <label className="field-label">CAMERA</label>
        <select className="full-select" value={scene.camera?.move || 'push-in'} onChange={(e) => update({ camera: { ...scene.camera, move: e.target.value } })}>
          {['static', 'push-in', 'pan-left', 'shake', 'orbit'].map((move) => <option key={move}>{move}</option>)}
        </select>
        <div className="slider-label"><span>Intensity</span><span>{Math.round((scene.camera?.intensity ?? 0.6) * 100)}%</span></div>
        <input
          className="range-input" type="range" min="0" max="1" step="0.05" value={scene.camera?.intensity ?? 0.6}
          onChange={(e) => update({ camera: { ...scene.camera, intensity: Number(e.target.value) } })}
        />
      </div>
      <div className="prop-section">
        <label className="field-label">TRANSITION OUT</label>
        <div className="transition-options">
          {TRANSITIONS.map((transition) => (
            <button
              key={transition}
              className={scene.transition_out?.type === transition ? 'chosen' : ''}
              onClick={() => update({ transition_out: { type: transition as TransitionType, duration: 0.3 } })}
            >
              {transition.replace('-', ' ')}
            </button>
          ))}
        </div>
      </div>
      <div className="prop-section">
        <label className="field-label">DURATION</label>
        <div className="number-input"><input type="number" min="0.5" step="0.5" value={scene.duration} onChange={(e) => update({ duration: Math.max(0.5, Number(e.target.value)) })} /><span>s</span></div>
      </div>
      <button className="asset-tile" onClick={onAdd}><Plus size={14} /><span><b>Add text layer</b><small>Place a new editable headline</small></span></button>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
