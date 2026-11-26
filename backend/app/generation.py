from __future__ import annotations
import copy, json, math, os, re
from typing import Any
import httpx
from .models import ProjectSpec, GenerateRequest
from .asset_registry import search_assets, list_categories

PALETTES = {
    "violet": ["#0B1020", "#7C5CFC", "#B7A6FF", "#29D3A5"],
    "ocean": ["#071A2D", "#168AAD", "#41EAD4", "#EAF8FF"],
    "warm": ["#201310", "#FF784F", "#FFCA72", "#FFF1D2"],
    "green": ["#0A1C18", "#23B889", "#B5F36D", "#F3F8EF"],
}

def _is_farsi(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text)) or any(x in text.lower() for x in ("persian", "farsi", "iranian"))

def _choose_palette(text: str) -> list[str]:
    t = text.lower()
    if any(k in t for k in ("ocean", "blue", "finance", "inventory", "saas", "technology")): return PALETTES["ocean"]
    if any(k in t for k in ("nature", "green", "eco", "health")): return PALETTES["green"]
    if any(k in t for k in ("warm", "food", "coffee", "orange")): return PALETTES["warm"]
    return PALETTES["violet"]

def _local_spec(req: GenerateRequest) -> dict[str, Any]:
    prompt = req.prompt.strip()
    palette = _choose_palette(prompt)
    fa = _is_farsi(prompt)
    is_inventory = any(k in prompt.lower() for k in ("inventory", "stock", "warehouse", "انبار", "موجودی"))
    subject = ("مدیریت موجودی، بدون پیچیدگی" if fa and is_inventory else
               "موجودی؛ همیشه تحت کنترل" if is_inventory else
               "یک ایده. تأثیری بزرگ." if fa else
               "Make your next move." if any(k in prompt.lower() for k in ("launch", "campaign", "brand")) else
               "Clarity for what comes next.")
    if is_inventory:
        headlines = [subject, "همه‌چیز در یک نگاه" if fa else "Every item. In sync.", "تصمیم‌های بهتر، سریع‌تر" if fa else "Smarter moves, made simple.", "از همین امروز شروع کنید" if fa else "Ready when you are."]
        details = ["سامان‌دهی هوشمند کالاها" if fa else "Inventory, finally in your hands.", "موجودی لحظه‌ای، همیشه دقیق" if fa else "Live stock, always accurate.", "هشدارهای به‌موقع • گزارش‌های روشن" if fa else "Fewer surprises. Better decisions.", "کنترل کامل کسب‌وکار شما" if fa else "One calm place to run your stock."]
    else:
        headlines = [subject, "Built around your ambition." if not fa else "برای قدم بعدی شما", "Less friction. More momentum." if not fa else "ساده‌تر، سریع‌تر، بهتر", "Start with a clearer view." if not fa else "مسیر روشن از همین‌جا"]
        details = ["A fresh way to move your work forward." if not fa else "راهی تازه برای پیشرفت کار شما", "See the details that matter." if not fa else "جزئیات مهم را همان لحظه ببینید", "A thoughtful experience, from day one." if not fa else "تجربه‌ای سنجیده از روز نخست", "Make room for what matters." if not fa else "برای آنچه مهم است، وقت بسازید"]
    labels = ["INTRODUCTION", "THE BIG PICTURE", "MADE FOR MOMENTUM", "YOUR NEXT CHAPTER"]
    visual = ["✦", "↗", "◈", "→"]
    durations = [round(req.duration * w / sum([.19,.30,.29,.22]), 2) for w in [.19,.30,.29,.22]]
    scenes = []
    for i in range(4):
        scene_text = headlines[i]; body = details[i]; accent = palette[1] if i in (0,2) else palette[2]
        elements = [
            {"id":f"eyebrow-{i}","kind":"label","text":labels[i],"x":50,"y":26,"width":70,"color":palette[2],"font_size":15,"weight":700,"animation":"reveal","delay":0.08},
            {"id":f"title-{i}","kind":"headline","text":scene_text,"x":50,"y":43 if req.aspect_ratio != "9:16" else 39,"width":84,"color":"#F8FAFC","font_size":72 if req.aspect_ratio == "16:9" else 60,"weight":750,"animation":"rise","delay":0.18,"accent":accent},
            {"id":f"body-{i}","kind":"body","text":body,"x":50,"y":59 if req.aspect_ratio != "9:16" else 51,"width":72,"color":"#B8C3D6","font_size":25,"weight":450,"animation":"reveal","delay":0.38},
            {"id":f"symbol-{i}","kind":"icon","text":visual[i],"asset_id":["icon-sparkles","icon-arrow-up-right","icon-chart-no-axes-column-increasing","icon-circle-check"][i],"x":50,"y":77 if req.aspect_ratio != "9:16" else 69,"width":18,"color":accent,"font_size":50,"weight":600,"animation":"scale","delay":0.44},
            {"id":f"metric-{i}","kind":"metric","text":["01 / 04","LIVE · 24/7","−38%","LET'S GO"][i],"x":50,"y":90 if req.aspect_ratio != "9:16" else 87,"width":45,"color":"#E8EDF7","font_size":14,"weight":650,"animation":"reveal","delay":0.58},
        ]
        scenes.append({"id":f"scene-{i+1}","title":labels[i].title(),"duration":max(1.5,durations[i]),
          "description":["A confident opening creates a clear visual promise.","The product benefit arrives as a focused, kinetic statement.","A strong proof point lands with breathing room.","The story resolves into a crisp invitation to act."][i],
          "narration":body,"transition":["fade","wipe","zoom","fade"][i],"background":palette[0],"background_asset":["background-mesh-violet","background-grid-fine","background-aurora-mist","background-radial-rays"][i],"elements":elements})
    scenes[-1]["duration"] = round(req.duration - sum(s["duration"] for s in scenes[:-1]), 2)
    lang = "fa" if fa else "en"
    title = "Inventory motion story" if is_inventory else "Studio motion story"
    return {"title":title,"prompt":prompt,"language":lang,"aspect_ratio":req.aspect_ratio,"fps":30,"palette":palette,"scenes":scenes}

def _bounded(value: Any, low: float, high: float, default: float) -> float:
    try: number=float(value)
    except (TypeError,ValueError): return default
    if not math.isfinite(number): return default
    return max(low,min(high,number))

def _repair_spec(raw: dict[str, Any]) -> dict[str, Any]:
    """One deterministic preflight repair pass; never executes generated code."""
    candidate=copy.deepcopy(raw)
    palette=candidate.get("palette") if isinstance(candidate.get("palette"),list) else []
    palette=[c for c in palette if isinstance(c,str) and re.fullmatch(r"#[0-9a-fA-F]{6}",c)]
    palette=(palette+PALETTES["violet"])[:4]
    candidate["palette"]=palette
    if candidate.get("aspect_ratio") not in ("16:9","9:16","1:1"): candidate["aspect_ratio"]="16:9"
    candidate["fps"]=int(_bounded(candidate.get("fps"),24,60,30))
    scenes=candidate.get("scenes")
    if not isinstance(scenes,list): candidate["scenes"]=[];return candidate
    candidate["scenes"]=scenes[:12]
    total=0.0
    for index,scene in enumerate(candidate["scenes"]):
        if not isinstance(scene,dict): candidate["scenes"][index]={};scene=candidate["scenes"][index]
        scene["id"]=str(scene.get("id") or f"scene-{index+1}")
        scene["title"]=str(scene.get("title") or f"Scene {index+1}")[:100]
        scene["duration"]=_bounded(scene.get("duration"),1,60,5)
        total+=scene["duration"]
        if scene.get("transition") not in ("fade","wipe","zoom","cut"): scene["transition"]="fade"
        if not isinstance(scene.get("background"),str) or not re.fullmatch(r"#[0-9a-fA-F]{6}",scene["background"]): scene["background"]=palette[0]
        elements=scene.get("elements") if isinstance(scene.get("elements"),list) else []
        elements=elements[:12]
        for el_index,el in enumerate(elements):
            if not isinstance(el,dict): elements[el_index]={};el=elements[el_index]
            el["id"]=str(el.get("id") or f"scene-{index+1}-element-{el_index+1}")
            if el.get("kind") not in ("headline","body","metric","icon","shape","label"): el["kind"]="body"
            el["text"]=str(el.get("text") or "")[:500]
            el["width"]=_bounded(el.get("width"),1,100,50)
            el["x"]=_bounded(el.get("x"),el["width"]/2,100-el["width"]/2,50)
            el["y"]=_bounded(el.get("y"),0,100,50)
            if not isinstance(el.get("color"),str) or not re.fullmatch(r"#[0-9a-fA-F]{6}",el["color"]): el["color"]=palette[(el_index+1)%len(palette)]
            accent=el.get("accent")
            if accent is not None and (not isinstance(accent,str) or not re.fullmatch(r"#[0-9a-fA-F]{6}",accent)): el["accent"]=None
            el["font_size"]=int(_bounded(el.get("font_size"),10,160,28))
            el["weight"]=int(_bounded(el.get("weight"),300,900,500))
            if el.get("animation") not in ("rise","scale","drift","pulse","reveal","none"): el["animation"]="reveal"
            el["delay"]=_bounded(el.get("delay"),0,max(0,scene["duration"]-.1),0)
        scene["elements"]=elements
        scene["description"]=str(scene.get("description") or "A focused visual beat advances the story.")[:240]
        scene["narration"]=str(scene.get("narration") or "")[:500]
    if total>120 and candidate["scenes"]:
        scale=120/total
        for scene in candidate["scenes"]: scene["duration"]=max(1,round(scene["duration"]*scale,2))
        candidate["scenes"][-1]["duration"]=round(120-sum(s["duration"] for s in candidate["scenes"][:-1]),2)
    return candidate

def validate_with_correction(raw: dict[str, Any], max_retries: int=1) -> tuple[ProjectSpec,list[str]]:
    """Validate the declarative spec and allow one bounded deterministic repair attempt."""
    candidate=copy.deepcopy(raw); corrections=[]
    for attempt in range(max_retries+1):
        try: return ProjectSpec.model_validate(candidate),corrections
        except Exception:
            if attempt>=max_retries: raise
            candidate=_repair_spec(candidate)
            corrections.append("Preflight normalized bounds, colors, timing, or unsupported motion values")
    raise ValueError("Animation specification could not be repaired")

async def _chat_json(client: httpx.AsyncClient, base: str, key: str, model: str, system: str, user: str) -> dict[str, Any]:
    response = await client.post(f"{base}/chat/completions", headers={"Authorization":f"Bearer {key}"},
      json={"model":model,"temperature":0.45,"response_format":{"type":"json_object"},"messages":[{"role":"system","content":system},{"role":"user","content":user}]})
    response.raise_for_status()
    return json.loads(response.json()["choices"][0]["message"]["content"])

def _compose_storyboard(req: GenerateRequest, brief: dict[str, Any], storyboard: dict[str, Any]) -> dict[str, Any]:
    palette=[c for c in brief.get("palette",[]) if isinstance(c,str) and re.fullmatch(r"#[0-9a-fA-F]{6}",c)]
    palette=(palette+["#0B1020","#7C5CFC","#B7A6FF","#29D3A5"])[:4]
    scenes_in=storyboard.get("scenes",[])
    if not isinstance(scenes_in,list) or not 3<=len(scenes_in)<=7: raise ValueError("Storyboard must contain between three and seven scenes")
    raw_durations=[]
    for item in scenes_in:
        try: raw_durations.append(max(1.0,float(item.get("duration",req.duration/len(scenes_in)))))
        except (TypeError,ValueError): raw_durations.append(req.duration/len(scenes_in))
    raw_total=sum(raw_durations)
    durations=[round(req.duration*d/raw_total,2) for d in raw_durations]
    durations[-1]=round(req.duration-sum(durations[:-1]),2)
    rtl=str(brief.get("language","en")).lower().startswith("fa") or _is_farsi(req.prompt)
    symbols=["✦","↗","◈","→","✳","◉","⌁"]
    frames=[]
    for i,item in enumerate(scenes_in):
        copy_text=item.get("on_screen_text",{}) if isinstance(item.get("on_screen_text"),dict) else {}
        headline=str(copy_text.get("headline") or item.get("title") or "A clearer way forward")[:120]
        body=str(copy_text.get("supporting_copy") or item.get("narration") or item.get("description") or "Designed to make your next step simpler.")[:180]
        label=str(copy_text.get("eyebrow") or item.get("title") or f"CHAPTER {i+1}")[:32].upper()
        accent=palette[1+(i%max(1,len(palette)-1))]
        transition=str(item.get("transition","fade")).lower()
        if transition not in ("fade","wipe","zoom","cut"): transition="fade"
        y_title=42 if req.aspect_ratio!="9:16" else 39; y_body=59 if req.aspect_ratio!="9:16" else 52; y_icon=77 if req.aspect_ratio!="9:16" else 70
        elements=[
          {"id":f"s{i+1}-eyebrow","kind":"label","text":label,"x":50,"y":25,"width":76,"color":palette[2] if len(palette)>2 else accent,"font_size":15,"weight":700,"animation":"reveal","delay":.08},
          {"id":f"s{i+1}-headline","kind":"headline","text":headline,"x":50,"y":y_title,"width":84,"color":"#F8FAFC","font_size":68 if req.aspect_ratio=="16:9" else 57,"weight":750,"animation":"rise","delay":.16,"accent":accent},
          {"id":f"s{i+1}-support","kind":"body","text":body,"x":50,"y":y_body,"width":74,"color":"#B8C3D6","font_size":23,"weight":450,"animation":"reveal","delay":.34},
          {"id":f"s{i+1}-motif","kind":"icon","text":symbols[i%len(symbols)],"asset_id":["icon-sparkles","icon-arrow-up-right","icon-chart-no-axes-column-increasing","icon-circle-check"][i%4],"x":50,"y":y_icon,"width":18,"color":accent,"font_size":48,"weight":600,"animation":"scale","delay":.42,"accent":accent},
          {"id":f"s{i+1}-chapter","kind":"metric","text":f"{i+1:02d} / {len(scenes_in):02d}","x":50,"y":90 if req.aspect_ratio!="9:16" else 88,"width":42,"color":"#E8EDF7","font_size":14,"weight":650,"animation":"reveal","delay":.52},
        ]
        frames.append({"id":f"scene-{i+1}","title":str(item.get("title") or label.title())[:80],"duration":durations[i],"description":str(item.get("visual_purpose") or item.get("description") or "A focused beat advances the story.")[:240],"narration":str(item.get("narration") or body)[:500],"transition":transition,"background":palette[0],"background_asset":["background-mesh-violet","background-grid-fine","background-aurora-mist","background-radial-rays"][i%4],"elements":elements})
    return {"title":str(brief.get("working_title") or storyboard.get("title") or "Motion story")[:100],"prompt":req.prompt,"language":"fa" if rtl else str(brief.get("language","en"))[:12],"aspect_ratio":req.aspect_ratio,"fps":30,"palette":palette,"scenes":frames}

async def _llm_spec(req: GenerateRequest) -> dict[str, Any] | None:
    key=os.getenv("LLM_API_KEY")
    if not key: return None
    base=os.getenv("LLM_BASE_URL","https://api.openai.com/v1").rstrip("/"); model=os.getenv("LLM_MODEL","gpt-4o-mini")
    interpretation="""Stage 1 — interpret a motion-graphics creative brief. Return JSON only with: working_title (short project name), video_purpose, target_audience, visual_style, duration_seconds, aspect_ratio, palette (3-4 hex colors), language (ISO code, use fa for Persian), narration_style, typography_direction, transition_mood, and scene_count (3-7). Extract what the user actually asked for; do not write a storyboard or animation yet. Preserve Persian/mixed-language requirements."""
    storyboard_prompt="""Stage 2 — create a storyboard only from the interpreted brief. Return JSON only with a title and scenes array. Each scene must contain title, duration (seconds), visual_purpose, description, transition (fade/wipe/zoom/cut only), narration, and on_screen_text with eyebrow, headline, and supporting_copy. 3-7 scenes. Each beat must advance one coherent story: hook, concrete benefit/demo, proof or differentiator, and a satisfying close/call to action where appropriate. Keep screen copy concise and native to the requested language. Treat a scene as a continuous piece of motion design, not a still-slide caption. Use the supplied library matches before inventing decorative primitives; mention up to two matching asset names in visual_purpose when useful. Compose a restrained background + texture + type hierarchy, consistent palette, readable hold, and varied motion hierarchy. Never invent asset IDs. Do not return code, JSX, or the final animation JSON. The local searchable library offers icons, shapes, backgrounds, textures, illustrations/stickers, device mockups, Lottie references, typography and pairings, text animation recipes, transitions, easing/springs, particle effects, components/templates, color palettes, and gradients. Registry API: GET /api/assets/search?q=...&category=...&tags=...&mood=...&limit=..., GET /api/assets/categories, GET /api/assets/{id}."""
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            brief=await _chat_json(client,base,key,model,interpretation,f"Requested runtime: {req.duration}s. Requested aspect: {req.aspect_ratio}. User brief: {req.prompt}")
            matches=search_assets(req.prompt,limit=12)
            categories=', '.join(f"{row['name']} ({row['count']})" for row in list_categories())
            asset_context=json.dumps([{'id':x['id'],'name':x['name'],'category':x['category'],'tags':x['tags'][:5],'description':x['description'][:100]} for x in matches],ensure_ascii=False)
            story=await _chat_json(client,base,key,model,storyboard_prompt,f"Interpreted brief: {json.dumps(brief,ensure_ascii=False)}. Asset categories: {categories}. Relevant library search results for the creative brief: {asset_context}. Create a coherent {req.duration}-second storyboard. Use only currently supported transitions fade, wipe, zoom, or cut.")
        return _compose_storyboard(req,brief,story)
    except Exception as e:
        if isinstance(e,ValueError): raise RuntimeError("The LLM storyboard could not be composed into supported motion scenes. Try again or check the model output.") from e
        raise RuntimeError(f"LLM generation failed during prompt interpretation or storyboard creation ({type(e).__name__}). Check LLM_API_KEY, LLM_BASE_URL, and model settings.") from e

async def generate_project(req: GenerateRequest) -> tuple[ProjectSpec, str]:
    raw = await _llm_spec(req)
    provider = "llm"
    if raw is None:
        raw = _local_spec(req); provider = "local"
    try:
        spec,_corrections = validate_with_correction(raw,max_retries=1)
    except Exception as e:
        if provider == "llm": raise RuntimeError("The storyboard animation specification failed preflight validation after one correction. Try again or adjust the brief.") from e
        raise
    return spec, provider
