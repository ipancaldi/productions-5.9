# Productions 5.9

An interactive prototype for planning a live production: sketch the stage, build
it in 3D, cut content to it, and watch the result. No build step, no bundler, no
package manager — every panel is a single hand-written HTML file that runs
straight from the dev server.

## Run it

```bash
python3 serve.py
```

Then open <http://localhost:3900/HUB_5.9.html>.

**The port is not arbitrary.** The local agent's CORS allow-list is exactly
`localhost:3900` / `127.0.0.1:3900` / `null`, so on any other port the Sketch Pad
and Reference Board load perfectly and simply cannot reach the agent. `serve.py`
also sends `no-store` on everything, because an iframe whose `src` has not
changed is otherwise never re-fetched — every reload here is a real reload. Both
reasons are written into the top of [`serve.py`](serve.py).

## The panels

`HUB_5.9.html` is the host. It owns the take — the single shared document — and
hosts the tools as same-origin iframes over a versioned `postMessage` bridge.
The tools hold no truth of their own; they ask the host and render what comes
back.

| | |
|---|---|
| [`scene-study-3d.html`](scene-study-3d.html) | the stage in three.js — solids, LED screens, cameras, skies |
| [`sequencing-timeline.html`](sequencing-timeline.html) | cues, video tracks, clips, blend modes, routing to screens |
| [`content-bin.html`](content-bin.html) | the media library; drag from here onto a track or straight onto an LED |
| [`video-preview.html`](video-preview.html) | what the screens are playing, composited |
| [`sketchpad.html`](sketchpad.html) | draw a plan; the agent turns it into geometry |
| [`refboard.html`](refboard.html) | reference images, read by the vision model |

[`agent/`](agent/) is the local Studio Agent API — FastAPI, holds no take,
persists nothing. Image generation goes through **Draw Things locally**; there
are no paid cloud services and no cloud dependencies anywhere in this project.

## The contracts

These are the documents to fix first when the halves disagree:

- [`AGENT-BRIDGE.md`](AGENT-BRIDGE.md) — the host ↔ agent wire protocol
- [`SCENE-STUDY-BRIDGE.md`](SCENE-STUDY-BRIDGE.md) — the host ↔ scene messages
- [`SOLIDS.md`](SOLIDS.md) — what a solid is and how it is stored
- [`IMAGE-PIPELINE.md`](IMAGE-PIPELINE.md) — generation, through Draw Things
- [`VISION.md`](VISION.md) — how a sketch becomes geometry
- [`PLAN.md`](PLAN.md) · [`DEVELOPMENT-LOG.md`](DEVELOPMENT-LOG.md) — the plan, and what actually happened

## Not in this repo

Roughly 630 MB of media is deliberately left out — `Content/` video, the `.hdr`
and `.exr` skies, the `.glb` models, the Python virtualenv and the vision model.
GitHub refuses a file over 100 MB and one sky map alone is 87 MB. Recreate them
locally: put video in `Content/`, skies in `HDR/` (listed by `HDR/index.json`),
models in `glb/`, and run

```bash
python3 -m venv agent/.venv && agent/.venv/bin/python -m pip install -r agent/requirements.txt
```
