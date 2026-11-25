from __future__ import annotations
import json, os, subprocess, threading, uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel
from .models import GenerateRequest, ProjectSpec, EditRequest
from .generation import generate_project

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
DATA = Path(os.getenv("MOTION_DATA_DIR", ROOT / "data"))
PROJECTS, EXPORTS = DATA / "projects", DATA / "exports"
PROJECTS.mkdir(parents=True, exist_ok=True); EXPORTS.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="Motion Graphics Studio API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])
app.mount("/exports", StaticFiles(directory=EXPORTS), name="exports")
JOBS: dict[str, dict] = {}
LOCK = threading.Lock()

class SaveProject(BaseModel):
    id: str | None = None
    spec: ProjectSpec

@app.get("/api/health")
def health(): return {"status":"ok", "renderer":"remotion", "llm_configured":bool(os.getenv("LLM_API_KEY"))}

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
    elements=[(scene,el) for scene in spec["scenes"] for el in scene["elements"]]
    selected=next(((s,e) for s,e in elements if e["id"]==req.selected_element_id), None)
    if any(word in text for word in ("dark", "darker", "تیره")):
        for scene in spec["scenes"]: scene["background"]="#070B16"
        change="Darkened all scene backgrounds"
    elif any(word in text for word in ("slow", "slower", "آهسته")):
        total=sum(scene["duration"] for scene in spec["scenes"])
        factor=min(1.12,120/total)
        for scene in spec["scenes"]: scene["duration"]=round(scene["duration"]*factor,2)
        change=f"Slowed the rhythm by extending scene timing {round((factor-1)*100)}%"
    elif any(word in text for word in ("dramatic", "bold", "دراماتیک")):
        targets=[selected] if selected else [next(((s,e) for s,e in elements if e["kind"]=="headline"),None)]
        for pair in targets:
            if pair: pair[1]["font_size"]=min(160,int(pair[1]["font_size"]*1.16)); pair[1]["weight"]=800
        change="Emphasized the selected headline"
    elif any(word in text for word in ("minimal", "minimalist", "مینیمال")):
        for scene in spec["scenes"]: scene["elements"]=[e for e in scene["elements"] if e["kind"] in ("headline","body","label")]
        change="Simplified each scene to its essential type"
    elif any(word in text for word in ("purple", "violet", "بنفش")):
        for scene in spec["scenes"]:
            for el in scene["elements"]:
                if el.get("accent") or el["kind"] in ("icon","label"): el["color"]="#9A7BFF"
        change="Shifted accent colors to violet"
    elif selected and any(word in text for word in ("bigger", "larger", "بزرگ")):
        selected[1]["font_size"]=min(160,selected[1]["font_size"]+12); change=f"Increased {selected[1]['kind']} size"
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
