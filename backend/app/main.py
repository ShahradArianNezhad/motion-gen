from __future__ import annotations
import json, os, subprocess, threading, uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel
from .models import GenerateRequest, ProjectSpec, EditRequest
from .generation import generate_project
from .asset_registry import search_assets, get_asset, list_categories
import httpx

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
DATA = Path(os.getenv("MOTION_DATA_DIR", ROOT / "data"))
PROJECTS, EXPORTS = DATA / "projects", DATA / "exports"
PROJECTS.mkdir(parents=True, exist_ok=True); EXPORTS.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="Motion Graphics Studio API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])
app.mount("/exports", StaticFiles(directory=EXPORTS), name="exports")
app.mount("/asset-files", StaticFiles(directory=ROOT / "assets"), name="asset-files")
JOBS: dict[str, dict] = {}
LOCK = threading.Lock()

class SaveProject(BaseModel):
    id: str | None = None
    spec: ProjectSpec

@app.get("/api/health")
def health(): return {"status":"ok", "renderer":"remotion", "llm_configured":bool(os.getenv("LLM_API_KEY"))}

@app.get("/api/assets/categories")
def asset_categories(): return list_categories()

@app.get("/api/assets/search")
def asset_search(q: str = "", category: str | None = None, tags: str = "", mood: str | None = None, limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0)):
    selected=[tag.strip() for tag in tags.split(",") if tag.strip()]
    return {"assets":search_assets(q, category, selected, mood, limit, offset), "total":len(search_assets(q, category, selected, mood, 2000))}

@app.get("/api/assets/{asset_id}")
def asset_detail(asset_id: str):
    item=get_asset(asset_id)
    if not item: raise HTTPException(404,"Asset not found")
    item=dict(item); item["url"]="/asset-files/"+item["path"].removeprefix("assets/")
    return item

@app.get("/api/stock/search")
async def stock_search(q: str = Query(..., min_length=2, max_length=160), media_type: str = "photo", provider: str = "pexels", per_page: int = Query(12, ge=1, le=30)):
    """Search stock providers with server-side keys; provider terms/license remain provider governed."""
    if media_type not in ("photo", "video"): raise HTTPException(422,"media_type must be photo or video")
    async with httpx.AsyncClient(timeout=20) as client:
        if provider == "pexels":
            key=os.getenv("PEXELS_API_KEY")
            if not key: raise HTTPException(503,"Set PEXELS_API_KEY on the backend to enable Pexels search")
            endpoint="https://api.pexels.com/v1/search" if media_type=="photo" else "https://api.pexels.com/videos/search"
            response=await client.get(endpoint,headers={"Authorization":key},params={"query":q,"per_page":per_page})
        elif provider == "pixabay":
            key=os.getenv("PIXABAY_API_KEY")
            if not key: raise HTTPException(503,"Set PIXABAY_API_KEY on the backend to enable Pixabay search")
            endpoint="https://pixabay.com/api/" if media_type=="photo" else "https://pixabay.com/api/videos/"
            response=await client.get(endpoint,params={"key":key,"q":q,"per_page":per_page,"safesearch":"true"})
        elif provider == "unsplash" and media_type == "photo":
            key=os.getenv("UNSPLASH_ACCESS_KEY")
            if not key: raise HTTPException(503,"Set UNSPLASH_ACCESS_KEY on the backend to enable Unsplash photo search")
            response=await client.get("https://api.unsplash.com/search/photos",headers={"Authorization":f"Client-ID {key}"},params={"query":q,"per_page":per_page})
        else: raise HTTPException(422,"Provider/media combination is not supported")
        if response.status_code >= 400: raise HTTPException(response.status_code,f"{provider.title()} search failed")
        data=response.json()
    return {"provider":provider,"media_type":media_type,"attribution_required":provider in ("pexels","unsplash"),"results":data.get("photos",data.get("videos",data.get("hits",data.get("results",[]))))}

@app.post("/api/generate")
async def generate(request: GenerateRequest):
    try:
        spec, provider = await generate_project(request)
    except RuntimeError as e: raise HTTPException(502, str(e))
    return {"id":str(uuid.uuid4()), "spec":spec.model_dump(), "provider":provider, "stages":["Prompt interpreted", "Storyboard drafted", "Animation specification validated", "Reusable motion components selected"]}

def _project_path(pid: str) -> Path:
    if not pid.replace("-", "").isalnum(): raise HTTPException(400, "Invalid project id")
    return PROJECTS / f"{pid}.json"

@app.get("/api/projects")
def list_projects():
    rows=[]
    for file in PROJECTS.glob("*.json"):
        try:
            payload=json.loads(file.read_text())
            spec=payload["spec"]
            rows.append({"id":payload["id"],"title":spec["title"],"updated_at":payload["updated_at"],"duration":sum(s["duration"] for s in spec["scenes"]),"aspect_ratio":spec["aspect_ratio"],"scene_count":len(spec["scenes"])})
        except Exception: continue
    return sorted(rows,key=lambda x:x["updated_at"],reverse=True)

@app.post("/api/projects")
def save_project(payload: SaveProject):
    pid=payload.id or str(uuid.uuid4())
    data={"id":pid,"spec":payload.spec.model_dump(),"updated_at":datetime.now(timezone.utc).isoformat()}
    _project_path(pid).write_text(json.dumps(data,ensure_ascii=False,indent=2))
    return data

@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    path=_project_path(project_id)
    if not path.exists(): raise HTTPException(404,"Project not found")
    return json.loads(path.read_text())

@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str):
    path=_project_path(project_id)
    if not path.exists(): raise HTTPException(404,"Project not found")
    path.unlink(); return {"deleted":True}

@app.post("/api/edit")
def edit_project(req: EditRequest):
    path=_project_path(req.project_id)
    if not path.exists(): raise HTTPException(404,"Project not found")
    data=json.loads(path.read_text()); spec=data["spec"]; text=req.command.lower()
    layers=[(scene,layer) for scene in spec["scenes"] for layer in scene.get("layers",[])]
    selected=next(((s,l) for s,l in layers if l["id"]==req.selected_element_id), None)
    if any(word in text for word in ("dark", "darker", "تیره")):
        for scene in spec["scenes"]: scene["background"]={"type":"color","colors":["#0B1020","#05070d"]}
        change="Darkened all scene backgrounds"
    elif any(word in text for word in ("slow", "slower", "آهسته")):
        total=sum(scene["duration"] for scene in spec["scenes"])
        factor=min(1.12,120/max(1,total))
        for scene in spec["scenes"]: scene["duration"]=round(scene["duration"]*factor,2)
        change=f"Slowed the rhythm by extending scene timing {round((factor-1)*100)}%"
    elif any(word in text for word in ("dramatic", "bold", "دراماتیک")):
        targets=[selected] if selected else [next((p for p in layers if p[1]["type"]=="text"),None)]
        for pair in targets:
            if pair:
                layer=pair[1]
                layer["style"]["fontSize"]=min(160,int((layer["style"].get("fontSize") or 36)*1.16))
                layer["style"]["fontWeight"]=800
                if layer.get("animation",{}).get("in_"): layer["animation"]["in_"]["preset"]="pop-bounce"
        change="Emphasized the selected text layer"
    elif any(word in text for word in ("minimal", "minimalist", "مینیمال")):
        for scene in spec["scenes"]: scene["layers"]=[l for l in scene.get("layers",[]) if l["type"] in ("text","caption")]
        change="Simplified each scene to its essential text"
    elif any(word in text for word in ("purple", "violet", "بنفش")):
        for scene in spec["scenes"]:
            scene["background"]["colors"]=["#7C5CFC","#05070d"]
            for layer in scene.get("layers",[]):
                if layer["type"] in ("text","caption"): layer["style"]["color"]="#9A7BFF"
        change="Shifted accent colors to violet"
    elif selected and any(word in text for word in ("bigger", "larger", "بزرگ")):
        sel=selected[1]
        sel["style"]["fontSize"]=min(160,(sel["style"].get("fontSize") or 36)+12)
        change=f"Increased {sel['type']} size"
    else:
        raise HTTPException(422,"Try: make it darker, make the title more dramatic, slow down, or make it more minimal.")
    validated=ProjectSpec.model_validate(spec)
    data.update(spec=validated.model_dump(),updated_at=datetime.now(timezone.utc).isoformat())
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2))
    return {"project":data,"message":change}

def _render_worker(job_id: str, project_id: str, spec: dict, fmt: str):
    with LOCK: JOBS[job_id]["status"]="rendering"; JOBS[job_id]["progress"]=4
    output=EXPORTS / f"{project_id}-{job_id}.{fmt}"
    try:
        spec_path=DATA / f"{job_id}.json"
        spec_path.write_text(json.dumps(spec,ensure_ascii=False))
        cmd=["node",str(ROOT/"renderer"/"render.mjs"),str(spec_path),str(output),fmt]
        process=subprocess.Popen(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=1)
        logs=[]
        assert process.stdout is not None
        for line in process.stdout:
            logs.append(line.rstrip())
            if line.startswith("PROGRESS "):
                try:
                    progress=max(4,min(96,int(line.split()[1])))
                    with LOCK: JOBS[job_id]["progress"]=progress
                except (ValueError,IndexError): pass
        return_code=process.wait(timeout=900)
        spec_path.unlink(missing_ok=True)
        if return_code: raise RuntimeError("\\n".join(logs)[-1400:] or "Remotion render failed")
        with LOCK: JOBS[job_id].update(status="completed",progress=100,download_url=f"/exports/{output.name}")
    except Exception as exc:
        with LOCK: JOBS[job_id].update(status="failed",error=str(exc),progress=0)

@app.post("/api/projects/{project_id}/export")
def export_project(project_id: str, background_tasks: BackgroundTasks, format: str="mp4"):
    if format not in ("mp4","webm","gif"): raise HTTPException(422,"Format must be mp4, webm, or gif")
    path=_project_path(project_id)
    if not path.exists(): raise HTTPException(404,"Project not found")
    spec=json.loads(path.read_text())["spec"]
    job_id=str(uuid.uuid4())
    job={"id":job_id,"project_id":project_id,"status":"queued","progress":0,"format":format,"created_at":datetime.now(timezone.utc).isoformat()}
    with LOCK: JOBS[job_id]=job
    background_tasks.add_task(_render_worker,job_id,project_id,spec,format)
    return job

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    with LOCK: job=JOBS.get(job_id)
    if not job: raise HTTPException(404,"Export job not found (jobs are held for this API process lifetime)")
    return job
