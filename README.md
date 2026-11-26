# Motion Studio

AI-assisted motion graphics editor that turns a creative brief into an editable, validated storyboard and a Remotion-rendered video. The repository began as an empty scaffold; the implementation plan is in [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md).

## Phase 1 features

- A staged generation pipeline with separate LLM calls for prompt interpretation and storyboard writing, then deterministic composition into reusable motion presets. A tailored local generator works without an API key.
- A Pydantic-validated, declarative project format with scene timing, palette, transitions, narration script fields, elements, positions, typography, and supported motion presets. Bounded preflight repairs common clipping/color/timing issues once before validation. Generated code is never executed.
- Browser studio with a multi-scene preview, scene timeline, play/scrub controls, editable scene and layer properties, text/color/position/size/animation controls, add/delete/duplicate scene, undo/redo, and autosave.
- Context-aware assistant edits for focused commands such as darken the background, emphasize the title, slow pacing, simplify the design, and recolor accents. Edits preserve unrelated project content.
- Reusable animated Remotion/SVG composition, local DM Sans, Manrope, and Vazirmatn fonts, plus MP4, WebM, and GIF export jobs with visible progress and downloadable results.
- Local JSON project persistence and export artifact storage in `data/` (git-ignored).
- Persian (Farsi) prompt detection, RTL UI text handling, Persian copy in the local storyboard provider, and bundled Vazirmatn rendering font.

## Architecture

```text
React + TypeScript + Vite + Zustand
   │ same-origin /api proxy
   ▼
FastAPI + Pydantic ── optional OpenAI-compatible LLM
   │ validated spec + local project JSON
   ▼
isolated Node renderer process → Remotion bundle → Chromium + FFmpeg → MP4/WebM/GIF
```

The Python API does not execute model-produced code. Models return structured JSON; the API validates it before saving or rendering. Rendering is launched in a subprocess, separate from request parsing. Local development projects and exports are stored below `data/`.

## Start locally

Requirements: Node.js 20+ and Python 3.10+. Remotion's platform package provides FFmpeg; the renderer includes a packaged Chromium build for local rendering.

The easiest way to run everything is the launcher:

```bash
./start.sh
```

It installs missing frontend and Python dependencies, starts the API on port 8000 and the studio on port 5173, and stops both with Ctrl+C. Set `WEB_PORT` to use a different frontend port (the API stays on 8000 because Vite proxies to it). An optional `.env` is picked up automatically; see step 3 below.

Or set things up manually:

1. Install frontend dependencies:
   ```bash
   npm install
   ```
2. Create and configure a Python environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```
3. (Optional) configure a server-side AI key:
   ```bash
   cp backend/.env.example .env
   # Set LLM_API_KEY; optionally change LLM_BASE_URL and LLM_MODEL.
   ```
   `LLM_API_KEY` is read by the backend only and must not be added to frontend variables. If omitted, the local structured generator runs without external services.
4. The `@sparticuz/chromium` renderer dependency supplies the headless browser used for local Remotion renders; Remotion's platform-specific compositor package supplies FFmpeg. No system FFmpeg/browser download is required.
5. In terminal one, start the API:
   ```bash
   source .venv/bin/activate
   uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
   ```
6. In terminal two, start the studio:
   ```bash
   npm run dev
   ```
   Open the Vite URL (normally `http://localhost:5173`). Vite proxies `/api` and `/exports` to FastAPI.

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `LLM_API_KEY` | Optional provider key used only by FastAPI | unset (local generator) |
| `LLM_BASE_URL` | OpenAI-compatible API base URL | `https://api.openai.com/v1` |
| `LLM_MODEL` | Chat-completions model | `gpt-4o-mini` |
| `MOTION_DATA_DIR` | Local JSON projects and export artifacts | `./data` |

## Tests and export

- Frontend typecheck and production bundle: `npm run build`
- API tests: activate the Python environment, then run `npm run test:api` (or `python -m unittest discover -s backend/tests -v`). The suite covers local prompt generation, Persian storyboard composition, schema validation, project save/edit, and invalid requests.
- End-to-end render verified: generated an 8-second project, exported a 1920×1080 MP4 through the API/Remotion worker, downloaded it, and checked the MP4 container signature (latest run: ~1.1 MB).
- Exports run asynchronously via `POST /api/projects/{id}/export?format=mp4|webm|gif`; poll `GET /api/jobs/{job_id}`. The bundled Remotion FFmpeg and Chromium binaries perform encoding without system-level installs.

## Current limitations / next phase

This is a local-first Phase 1 foundation. It has no accounts, cloud storage, Redis worker queue, cancellation, voice provider, uploaded audio, synchronized spoken narration, subtitle tracks, advanced asset importing, or multi-user access controls. Job state is process-local and should be moved to a durable queue before production. The built-in local generator is intentionally deterministic; configure an LLM provider for richer brief-specific storyboards. The editing assistant currently supports a focused safe command set rather than open-ended spec patching. Recommended next: Phase 2 timeline/property editing refinement and real-time preview, then Persian TTS/narration synchronization, followed by persistent background workers and user/project access control.
