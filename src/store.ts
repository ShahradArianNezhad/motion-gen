import {create}from 'zustand';
import type {ProjectSpec,Layer}from './types';
type State={projectId:string|null;spec:ProjectSpec|null;selectedScene:number;selectedLayer:string|null;history:ProjectSpec[];future:ProjectSpec[];setProject:(id:string,spec:ProjectSpec)=>void;setSpec:(spec:ProjectSpec)=>void;setScene:(n:number)=>void;select:(id:string|null)=>void;addLayer:(l:Layer)=>void;setLayer:(id:string,patch:Partial<Layer>)=>void;undo:()=>void;redo:()=>void;clear:()=>void};
export const useStudio=create<State>((set,get)=>({projectId:null,spec:null,selectedScene:0,selectedLayer:null,history:[],future:[],
  setProject:(projectId,spec)=>set({projectId,spec,selectedScene:0,selectedLayer:null,history:[],future:[]}),
  setSpec:(spec)=>{const old=get().spec;if(old)set(s=>({spec,history:[...s.history,old].slice(-40),future:[]}));else set({spec})},
  setScene:(selectedScene)=>set({selectedScene,selectedLayer:null}),
  select:(selectedLayer)=>set({selectedLayer}),
  addLayer:(layer)=>{const base=get().spec;if(!base)return;const next=structuredClone(base);const s=next.scenes[get().selectedScene];if(s)s.layers.push(layer);set({spec:next,selectedLayer:layer.id})},
  setLayer:(id,patch)=>{const base=get().spec;if(!base)return;const next=structuredClone(base);const s=next.scenes[get().selectedScene];const l=s?.layers?.find(x=>x.id===id);if(l){Object.assign(l,patch);l.position={x:Math.max(0,Math.min(1,l.position.x||0.5)),y:Math.max(0,Math.min(1,l.position.y||0.5))};}set({spec:next})},
  undo:()=>set(s=>{if(!s.history.length||!s.spec)return{};return{spec:s.history.at(-1)!,history:s.history.slice(0,-1),future:[s.spec,...s.future]}}),
  redo:()=>set(s=>{if(!s.future.length||!s.spec)return{};return{spec:s.future[0],history:[...s.history,s.spec],future:s.future.slice(1)}}),
  clear:()=>set({projectId:null,spec:null,selectedScene:0,selectedLayer:null,history:[],future:[]})}));
