import '@fontsource/dm-sans/400.css';import '@fontsource/dm-sans/500.css';import '@fontsource/dm-sans/600.css';import '@fontsource/dm-sans/700.css';
import '@fontsource/manrope/400.css';import '@fontsource/manrope/500.css';import '@fontsource/manrope/600.css';import '@fontsource/manrope/700.css';import '@fontsource/manrope/800.css';
import '@fontsource/vazirmatn/400.css';import '@fontsource/vazirmatn/500.css';import '@fontsource/vazirmatn/600.css';import '@fontsource/vazirmatn/700.css';import '@fontsource/vazirmatn/800.css';
import React,{useEffect,useMemo,useState}from 'react';
import {createRoot}from 'react-dom/client';
import {ArrowRight,Check,Clapperboard,Clock3,Cloud,Download,Layers,LoaderCircle,MessageCircle,MoreHorizontal,Pause,Play,Plus,Redo2,Send,Sparkles,Square,Trash2,WandSparkles,X}from 'lucide-react';
import {api}from './api';
import {useStudio}from './store';
import type {Layer,ProjectSpec}from './types';
import './styles.css';

const samplePrompts=['A sleek product launch for an AI note-taking app, midnight blue and electric violet, 18 seconds, landscape','یک ویدیوی تبلیغاتی ۲۰ ثانیه‌ای برای نرم‌افزار مدیریت موجودی، با طراحی مدرن و روایت فارسی','A joyful 15-second launch animation for a sustainable skincare brand, warm colors, vertical'];
const PRESET_OPTS=['pop-bounce','slide-in','scale-from-zero','fade-up','mask-reveal','rotate-in','flip-3d','blur-to-sharp','elastic-drop','glitch-in','typewriter','whip-in','color-sweep','float','pulse','wiggle','slow-rotate','shimmer','parallax-drift','breathing-scale','leaf-drift','shake','highlight-sweep','color-flash','scale-punch','draw-on','circle-draw-on','arrow-draw-on','underline-draw','slide-out','scale-down','fade','mask-wipe-out','shatter','whip-out'];

function App(){
  const{spec,projectId,setProject,setSpec,selectedScene,setScene,selectedLayer,select,addLayer,setLayer,undo,redo,history,future}=useStudio();
  const[screen,setScreen]=useState<'home'|'editor'>('home');
  const[prompt,setPrompt]=useState('');
  const[duration,setDuration]=useState(20);
  const[ratio,setRatio]=useState<'16:9'|'9:16'|'1:1'>('16:9');
  const[generating,setGenerating]=useState(false);
  const[error,setError]=useState('');
  const[projects,setProjects]=useState<any[]>([]);
  const[health,setHealth]=useState<{llm_configured:boolean}|null>(null);
  const[playing,setPlaying]=useState(false);
  const[time,setTime]=useState(0);
  const[assistant,setAssistant]=useState(false);
  const[chatInput,setChatInput]=useState('');
  const[chatLog,setChatLog]=useState<{role:string;text:string}[]>([]);
  const[exportBusy,setExportBusy]=useState(false);
  const[downloadUrl,setDownloadUrl]=useState('');

  const scene=spec?.scenes[selectedScene];
  useEffect(()=>{api.projects().then(setProjects).catch(()=>{});api.health().then(setHealth).catch(()=>{});},[]);
  useEffect(()=>{if(!spec||!projectId||screen!=='editor')return;const t=setTimeout(()=>api.save(projectId,spec).catch(()=>{}),750);return()=>clearTimeout(t)},[spec,projectId,screen]);
  useEffect(()=>{if(!playing||!spec)return;const timer=setInterval(()=>setTime(v=>{const total=spec.scenes.reduce((a,s)=>a+s.duration,0);if(v+0.1>=total){setPlaying(false);return 0}return v+0.1}),100);return()=>clearInterval(timer)},[playing,spec]);

  const totalDur=spec?.scenes.reduce((a,s)=>a+s.duration,0)||0;
  const start=useMemo(()=>spec?.scenes.slice(0,selectedScene).reduce((a,s)=>a+s.duration,0)||0,[spec,selectedScene]);
  async function createProject(text=prompt){
    if(!text.trim())return;setGenerating(true);setError('');
    try{const result=await api.generate(text,duration,ratio);const saved=await api.save(result.id,result.spec);setProject(saved.id,saved.spec);setScreen('editor');setTime(0);setProjects(await api.projects());}
    catch(e:any){setError(e.message||'Generation failed. Please try again.')}
    finally{setGenerating(false)}
  }
  async function openProject(id:string){try{const p=await api.getProject(id);setProject(p.id,p.spec);setScreen('editor');setTime(0);setDownloadUrl('')}catch(e:any){setError(e.message)}}
  async function removeProject(id:string){if(!confirm('Delete this project?'))return;await api.remove(id);setProjects(await api.projects())}
  async function sendEdit(){if(!projectId||!chatInput.trim())return;const cmd=chatInput;setChatInput('');setChatLog(x=>[...x,{role:'user',text:cmd}]);try{const res=await api.edit(projectId,cmd,selectedLayer||undefined);setSpec(res.project.spec);setChatLog(x=>[...x,{role:'assistant',text:res.message}])}catch(e:any){setChatLog(x=>[...x,{role:'assistant',text:e.message}])}}
  const addTextLayer=()=>addLayer({id:`layer-${Date.now()}`,type:'text',content:'Text',start:0.2,end:4,position:{x:0.5,y:0.5},animation:{in_:{preset:'pop-bounce',duration:0.5},loop:{preset:'float',amplitude:8}}});
  const addShapeLayer=()=>addLayer({id:`shape-${Date.now()}`,type:'shape',start:0.2,end:4,position:{x:0.5,y:0.6},animation:{in_:{preset:'pop-bounce',duration:0.4}}});
  const exportVideo=()=>{
    if(!projectId)return;setExportBusy(true);setDownloadUrl('');
    const d=document.createElement('a');d.href=`/exports/${projectId}.mp4`;d.download=`${spec?.title||'project'}.mp4`;d.click();setExportBusy(false);
  };

  const layers=scene?.layers||[];
  if(screen==='editor'){
    return <div className="studio-app">
      <header className="studio-topbar">
        <button className="back-home" onClick={()=>{setScreen('home');api.projects().then(setProjects)}}><span>motion<span className="brand-light">studio</span></span></button>
        <span className="top-divider"/>
        <div className="project-title-area"><input className="project-title-input" value={spec!.title} onChange={e=>setSpec({...spec! as ProjectSpec,title:e.target.value})}/><span className="save-status"><Cloud size={12}/>Autosaved</span></div>
        <div className="top-actions">
          <button className="top-icon" title="Undo" disabled={!history.length} onClick={undo}><span>↩</span></button>
          <button className="top-icon" title="Redo" disabled={!future.length} onClick={redo}><span>↪</span></button>
          <button className="share-button" onClick={()=>setAssistant(v=>!v)}><MessageCircle size={15}/> AI assistant</button>
          <button className="export-button" onClick={exportVideo}>{exportBusy?'Exporting…':'Export MP4'} <Download size={15}/></button>
        </div>
      </header>
      <main className="editor-main">
        <div className="editor-toolbar"><span>Timeline v2</span><span>{spec?.meta?.style} · {spec?.meta?.fps} fps · {spec?.meta?.width}×{spec?.meta?.height}</span></div>
        <div className="transport">
          <div className="transport-left"><button className="transport-play" onClick={()=>{setPlaying(v=>!v);if(!playing&&time===0)setTime(start)}}>{playing?<Pause size={16} fill="currentColor"/>:<Play size={16} fill="currentColor"/>}</button><span className="timecode">{formatTime(time)} <i>/</i> {formatTime(totalDur)}</span></div>
          <div className="scrub-area" onClick={e=>{const r=e.currentTarget.getBoundingClientRect();setTime(totalDur*(e.clientX-r.left)/r.width)}}><div className="scrub-track"><span style={{width:`${time/totalDur*100}%`}}/></div><div className="scrub-knob" style={{left:`${time/totalDur*100}%`}}/></div>
        </div>
        <div className="timeline-panel">
          <div className="timeline-head"><div><Layers size={15}/><b>Timeline</b><span className="scene-counter">{spec?.scenes.length||0} scenes</span></div>
          <button title="Add scene" onClick={()=>{const next=structuredClone(spec!);const i=selectedScene;next.scenes.splice(i+1,0,{id:`scene-${Date.now()}`,start:next.scenes[i].start+next.scenes[i].duration,duration:4,background:{type:'animated-gradient',colors:next.scenes[0].background.colors||['#0B1020','#7C5CFC']},camera:{move:'push-in',intensity:0.5},layers:[{id:`l-${Date.now()}`,type:'text',content:'New headline',start:0,end:4,position:{x:0.5,y:0.5},animation:{in_:{preset:'pop-bounce',duration:0.5}}}],transition_out:{type:'whip-pan',duration:0.3}});setSpec(next);setScene(i+1)}}><Plus size={15}/></button></div>
          <div className="track-content"><div className="scene-track">{(spec?.scenes||[]).map((s,i)=>(<button className={`scene-block ${selectedScene===i?'selected':''}`} key={s.id} style={{flex:`${s.duration} 1 0%`}} onClick={()=>{setScene(i);setTime(s.start)}}><span className="scene-num">{String(i+1).padStart(2,'0')}</span><strong>{s.id}</strong><small>{s.duration.toFixed(1)}s</small></button>))}</div></div>
        </div>
        <div className="inspector">
          {selectedLayer&&scene?<LayerEditor key={selectedLayer} layer={layers.find(l=>l.id===selectedLayer)!} spec={spec!} update={p=>setLayer(selectedLayer,p)} onDelete={()=>{const next=structuredClone(spec!);next.scenes[selectedScene].layers=next.scenes[selectedScene].layers.filter(l=>l.id!==selectedLayer);setSpec(next);select(null)}}/>:<SceneEditor scene={scene!} update={(p:Partial<Scene2>)=>{const next=structuredClone(spec!);Object.assign(next.scenes[selectedScene],p);setSpec(next)}} onAdd={addTextLayer}/>}
          {layers.length>0&&(<div className="layers-heading">Layers <span>{layers.length}</span></div>)}
          {(layers.length===0||selectedLayer===null)&&scene&&<div className="layer-list">{layers.slice().reverse().map(l=><button key={l.id} className="layer-item" onClick={()=>select(l.id)}><span>{l.type}</span><span>{l.content?.slice(0,20)}</span></button>)}<button className="layer-add" onClick={addTextLayer}><Plus size={15}/> Add text layer</button></div>}
          <div className="add-layer-bar"><button onClick={addShapeLayer}>+ Shape layer</button></div>
        </div>
        {assistant&&(
          <aside className="assistant-panel">
            <div className="panel-header"><Sparkles size={16}/><strong>AI assistant</strong><button className="icon-quiet" onClick={()=>setAssistant(false)}><X size={16}/></button></div>
            <div className="chat-content"><div className="assistant-welcome"><b>Tell me what to change…</b></div>{chatLog.map((m,i)=><div className={`chat-bubble ${m.role}`} key={i}>{m.text}</div>)}</div>
            <div className="chat-compose"><textarea value={chatInput} onChange={e=>setChatInput(e.target.value)} placeholder="Tell me what to change…" onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendEdit()}}}/><button onClick={sendEdit} disabled={!chatInput.trim()}><Send size={15}/></button></div>
            <div className="safe-edit-note"><Check size={12}/> Your existing edits stay yours</div>
          </aside>)}
        {error&&(<div className="toast-error"><span>{error}</span><button onClick={()=>setError('')}><X size={15}/></button></div>)}
      </main>
    </div>;
  }

  return (
    <main className="home-screen">
      <header className="home-nav">
        <div className="brand"><div className="brand-mark"><Clapperboard size={18}/></div><span>motion<span className="brand-light">studio</span></span><span className="beta-pill">BETA</span></div>
        <div className="nav-right"><div className="system-status"><span className="status-dot"/>{health?.llm_configured?'AI engine connected':'Studio ready'}</div><button className="avatar">M</button></div>
      </header>
      <section className="hero">
        <div className="hero-kicker"><span className="sparkle-dot"><Sparkles size={13}/></span> YOUR CREATIVE CO-PILOT</div>
        <h1>Make your ideas<br/><span>move.</span></h1>
        <p className="hero-sub">Turn a few words into a motion story worth watching.</p>
        <div className="prompt-card">
          <div className="prompt-head"><div className="prompt-orb"><WandSparkles size={17}/></div><span>Describe the video you imagine</span></div>
          <textarea value={prompt} onChange={e=>setPrompt(e.target.value)} placeholder="A product launch, a bold brand story, an idea brought to life…" rows={3} disabled={generating}/>
          <div className="prompt-footer">
            <div className="generation-settings">
              <label><Clock3 size={14}/><select aria-label="Duration" value={duration} onChange={e=>setDuration(Number(e.target.value))}>{[10,15,20,30,45,60].map(n=><option key={n} value={n}>{n} sec</option>)}</select><span className="setting-separator"/></label>
              <label><Square size={13}/><select aria-label="Aspect ratio" value={ratio} onChange={e=>setRatio(e.target.value as any)}>{['16:9','9:16','1:1'].map(r=><option key={r} value={r}>{r}</option>)}</select><span className="setting-separator"/></label>
            </div>
            <button className="primary-button" onClick={()=>createProject()} disabled={!prompt.trim()||generating}>{generating?<><LoaderCircle className="spin" size={16}/> Creating…</>:<>Generate story <ArrowRight size={16}/></>}</button>
          </div>
          {generating&&<div className="generation-progress"><span className="progress-line"/><span>Generating your v2 timeline plan…</span></div>}
        </div>
        {error&&<div className="error-banner"><span>{error}</span><button onClick={()=>setError('')}><X size={15}/></button></div>}
        <div className="examples"><span className="example-label">TRY A PROMPT</span>{samplePrompts.map((p,i)=><button key={i} onClick={()=>{setPrompt(p);setRatio(i===2?'9:16':'16:9');setDuration(i===0?18:20)}}>{i===1?'فارسی':i===2?'Product story':'SaaS launch'}<ArrowRight size={12}/></button>)}</div>
      </section>
      <section className="projects-section">
        <div className="section-heading"><div><span className="section-eyebrow">YOUR WORKSPACE</span><h2>Recent projects <span className="count-badge">{projects.length.toString().padStart(2,'0')}</span></h2></div><button className="text-button" onClick={()=>document.querySelector<HTMLTextAreaElement>('textarea')?.focus()}>New project <Plus size={15}/></button></div>
        {projects.length?<div className="project-grid">{projects.map((p,index)=><article className="project-card" key={p.id}><button className={`project-art art-${index%4}`} onClick={()=>openProject(p.id)}><div className="art-noise"/><span className="art-kicker">MOTION STUDY · {String(index+1).padStart(2,'0')}</span><strong>{p.title}</strong><span className="art-open"><ArrowRight size={16}/></span></button><div className="project-meta"><button onClick={()=>openProject(p.id)}><strong>{p.title}</strong><span>Edited {new Date(p.updated_at).toLocaleDateString()} · {p.scene_count} scenes</span></button><button title="Delete project" className="icon-quiet" onClick={()=>removeProject(p.id)}><MoreHorizontal size={17}/></button></div></article>)}</div>:(<div className="empty-projects"><div className="empty-icon"><Layers size={20}/></div><div><strong>Your canvas is waiting.</strong><p>Start with a prompt above — your projects will find a home here.</p></div><ArrowRight size={16}/></div>)}
      </section>
      <footer className="home-footer"><span>DESIGNED FOR THE BIG IDEA.</span><span>AI MOTION GRAPHICS STUDIO ✦ 2025</span></footer>
    </main>
  );
}
type Scene2={duration:number}&Record<string,any>;
function LayerEditor({layer,spec,update,onDelete}:{layer:Layer;spec:ProjectSpec;update:(p:Partial<Layer>)=>void;onDelete:()=>void}){
  const setAnim=(key:'in_'|'loop'|'out', val:any)=>update({animation:{...layer.animation, [key]:val}} as any);
  return <div className="prop-scroll">
    <div className="prop-section"><label className="field-label">TYPE & CONTENT</label><select className="full-select" value={layer.type} onChange={e=>update({type:e.target.value as Layer['type']})}>{['text','caption','image','shape','icon','lottie','video','chart'].map(t=><option key={t}>{t}</option>)}</select><textarea className="property-text" value={layer.content||''} onChange={e=>update({content:e.target.value})} dir="auto"/></div>
    <div className="prop-section"><label className="field-label">TIMING</label><div className="prop-two">{['start','end'].map(k=><label key={k}>{k}{' '}<div className="number-input"><input type="number" step="0.1" value={(layer as any)[k]??0} onChange={e=>update({[k]:Number(e.target.value)} as any)}/><span>s</span></div></label>)}</div></div>
    <div className="prop-section"><label className="field-label">POSITION (0–1)</label><div className="prop-grid"><label>X <input type="number" step="0.01" value={layer.position.x} onChange={e=>update({position:{...layer.position,x:Number(e.target.value)}})}/></label><label>Y <input type="number" step="0.01" value={layer.position.y} onChange={e=>update({position:{...layer.position,y:Number(e.target.value)}})}/></label></div></div>
    <div className="prop-section"><label className="field-label">ANIMATION IN</label><select className="full-select" value={layer.animation.in_?.preset||'pop-bounce'} onChange={e=>setAnim('in_',{...(layer.animation.in_||{}),preset:e.target.value})}>{['none',...PRESET_OPTS].map(p=><option key={p}>{p}</option>)}</select></div>
    <div className="prop-section"><label className="field-label">ANIMATION OUT</label><select className="full-select" value={layer.animation.out?.preset||'fade'} onChange={e=>setAnim('out',{...(layer.animation.out||{}),preset:e.target.value})}>{['none',...PRESET_OPTS].map(p=><option key={p}>{p}</option>)}</select></div>
    <div className="prop-section"><label className="field-label">STAGGER</label><label><input type="checkbox" checked={layer.animation.stagger||false} onChange={e=>setAnim('in_',{...(layer.animation.in_||{}),stagger:true})}/><span>Apply stagger per char/word reveals</span></label></div>
    <button className="delete-layer" onClick={onDelete}><Trash2 size={14}/> Delete layer</button>
  </div>;
}
function SceneEditor({scene,update,onAdd}:{scene:any;update:(p:Partial<any>)=>void;onAdd:()=>void}){
  return <div className="prop-scroll">
    <div className="prop-section"><label className="field-label">BACKGROUND</label><select className="full-select" value={scene.background?.type||'animated-gradient'} onChange={e=>update({background:{type:e.target.value,colors:['#0B1020','#7C5CFC']}})}>{['animated-gradient','color','grid','particles','image-kenburns'].map(t=><option key={t}>{t}</option>)}</select></div>
    <div className="prop-section"><label className="field-label">CAMERA</label><select className="full-select" value={scene.camera?.move||'push-in'} onChange={e=>update({camera:{move:e.target.value,intensity:0.6}})}>{['static','push-in','pan-left','shake','orbit'].map(t=><option key={t}>{t}</option>)}</select></div>
    <div className="prop-section"><label className="field-label">TRANSITION OUT</label><select className="full-select" value={scene.transition_out?.type||'whip-pan'} onChange={e=>update({transition_out:{type:e.target.value,duration:0.3}})}>{['whip-pan','zoom-through','glitch','slide-push','shape-wipe','flash-cut','morph','cross-zoom'].map(t=><option key={t}>{t}</option>)}</select></div>
    <div className="prop-section"><label className="field-label">DURATION</label><div className="number-input"><input type="number" min="0.5" step="0.5" value={scene.duration} onChange={e=>update({duration:Number(e.target.value)})}/><span>s</span></div></div>
    <button className="asset-tile" onClick={onAdd}><Plus size={14}/><span><b>Add text layer</b></span></button>
  </div>;
}
function formatTime(seconds:number){const m=Math.floor(seconds/60),s=Math.floor(seconds%60),f=Math.floor(seconds%1*30);return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}:${String(f).padStart(2,'0')}`}
createRoot(document.getElementById('root')!).render(<App/>);
