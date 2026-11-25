# Motion Graphics Studio — implementation plan

## Repository assessment
The repository is an empty scaffold: one-line README, no application code, dependencies, tests, or established conventions. The working branch is clean. Runtime tooling available in this environment is Node.js 22 and Python 3.11; a system FFmpeg/Chrome is not installed. The final renderer uses packaged Remotion FFmpeg and packaged Chromium.

## Phase 1 architecture
- **Web editor:** React + TypeScript + Vite, Tailwind CSS, Zustand. A single-page studio includes a project dashboard, prompt composer, generated storyboard, scene preview, scene timeline, layer controls, and export state.
- **Generation API:** Python + FastAPI, Pydantic-validated declarative scene schema. Separate LLM calls interpret the brief and draft a storyboard; a local composition stage maps that story into reusable motion elements. A bounded preflight performs one deterministic repair attempt for clipping, colors, timing, and unsupported motion before validation. Configurable OpenAI-compatible chat-completions provider; a deterministic local provider keeps the app usable without API keys. No model-generated code is executed.
- **Rendering:** Remotion composition built from registered React/SVG animation components. A dedicated Node rendering script renders the validated spec using Remotion Renderer; the API owns job status and invokes this renderer in a subprocess. FFmpeg is required for MP4 encoding. The API reports a clear setup/runtime error when rendering prerequisites are missing rather than falsely marking an export complete.
- **Storage:** Local project JSON and export artifacts under an ignored `data/` directory in this first local-development phase. API keys remain server-side in environment configuration.

## Incremental implementation
1. Add the validated generation schema, local/LLM providers, project/job endpoints, renderer bridge, and API tests.
2. Add the Remotion composition and export script with reusable headline, metric, icon, and background motion components.
3. Build the studio UI and connect generation, project persistence, selection/editing, timeline, and exports to the API.
4. Add setup docs, run tests/build, and verify the full pipeline. In this sandbox, generate and download a real full-resolution MP4 through the API using the packaged renderer dependencies.

## Scope boundaries
This delivers Phase 1 as a usable local foundation. Accounts, cloud object storage, Redis workers, voice synthesis, and advanced editing are intentionally deferred. Scene-level edits are declarative and safe; generation returns editable specifications, never executable AI code.