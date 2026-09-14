# Agent bridge — protocol v1

The contract between **`production-hub-v5.html`** (the host), the two new
input panels, and the **Studio Agent API** on `:3902`. Written before the code,
like `SCENE-STUDY-BRIDGE.md` was; if the halves ever disagree, this file is the
thing to fix first and `AGENT_V` is the thing to raise.

| | |
|---|---|
| **Host** | `production-hub-v5.html` — section *4c · THE AGENT BRIDGE*, plus `ed-sketch`, `ed-refs`, `ed-agent` |
| **Panels** | `sketchpad.html`, `refboard.html` — `<iframe>` + `postMessage`, same shape as the Scene Study |
| **Service** | `5.9/agent/` — FastAPI + uvicorn, `127.0.0.1:3902`, official `anthropic` SDK |
| **Model** | `claude-opus-5`, or a **local VLM** — see `VISION.md § The local engine` |
| **Version** | every message and every request carries `v: 1`; anything else is ignored, silently, on all sides |

> **v5.5 · SOLIDS.** A third contract joins these two: `SOLIDS.md`, which covers
> fitted outlines — the `solids` message, the `solids[]` field on `interpret`, the
> `solid` op, the `add_solid` tool and the bulge convention that carries a true arc
> as one number. Every addition is backwards-compatible, so **`AGENT_V` stays 1**.
> Read `SOLIDS.md` before touching anything geometric.
>
> **v5.5 · VISION.** And a fourth: `VISION.md`, which covers reading an uploaded
> reference — `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` over a deterministic tracer,
> the `read_reference` tool, and the arbitration that decides when the model's answer
> counts. `/health` gains a `vision` block; what it produces are the ordinary `solid`
> and `audience` ops, so nothing downstream knows a traced reference from a trace made
> by hand.
>
> **v5.5 · VISION.** And a fourth: `VISION.md`, which covers reading an uploaded
> reference — `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` over a deterministic tracer,
> the `read_reference` tool, and the arbitration that decides when the model's answer
> counts. `/health` gains a `vision` block; the ops it produces are the ordinary `solid`
> and `audience` ops, so nothing downstream knows a reference from a trace.

---

## Who may talk to whom

```
sketchpad ─┐                                    ┌─ scene-study (ghosts, measure)
refboard  ─┼─► HOST ─► :3902 agent API ─► Claude │
           │     ▲                               └─ scene-study (snapshot)
ed-agent ──┘     └── the take: the only writer of facts
```

**Only the host calls :3902.** Panels never do. The agent never calls the Scene
Study, never holds a take, and keeps no store. It is a function of
*(snapshot + images + conversation)* → *plan*.

Three reasons this is not negotiable: one auth path and no API key in an HTML
file; panels that still boot standalone against their own mock; and a single
writer for the facts, so the agent cannot become a second model of the
production.

---

## Part 1 · Host ⇄ the new panels (`postMessage`)

Same transport, handshake and `e.source` filter as the scene bridge — see
`SCENE-STUDY-BRIDGE.md § Origins`. `AGENT_V = 1` is carried separately from
`BRIDGE_V`; the two protocols version independently.

### Host → panel

| type | payload | meaning |
|---|---|---|
| `hello` | `tokens`, `unitsPerMetre`, `venue`, `stamps`, `refRoles` | identity and vocabulary, once per connection. `tokens` is the host's resolved BrandOS palette, written onto the panel's `:root` — nothing is transcribed |
| `underlay` | `png` (ArrayBuffer｜null) | a top-down snapshot of the current scene, to draw faint beneath the sketch |
| `busy` | `on` (bool), `label?`, `note?` | an interpret is in flight; the panel locks its BUILD 3D button and shows the phase. `label` is the phase name and `note` its detail — the host names both, so the panels do not each work it out from their own half of the story |
| `result` | `planId`, `opCount`, `intent`, `summary` | what came back, so the input panel can mark the sketch as *interpreted* |
| `clear` | — | the take changed under the panel; drop the canvas / board |
| `selectSolid` | `srcId｜null` | **v5.5** — a shape was selected in the Scene Study; select the trace it came from. **v5.8** — a `srcId` naming a MODEL FACE selects that face on the paper. A solid the room built from an imported face has no trace here, so the pad used to clear its selection and the surface vanished off the drawing entirely; the face's own id IS that solid's `srcId`, so it is the outline the paper lights |
| `scene` | `takeId`, `solids[]` | **v5.8** — WHAT THE TAKE ALREADY HOLDS, so the pad opens onto the show rather than onto blank paper. Sent on the handshake, on a take change, and whenever a shape appears in the take that the paper did not draw (a face taken in the room). Each row is a take solid as `SOLIDS.md` defines it, and the pad REDRAWS it: an editable outline, entered in its record of what is already true and locked, so BUILD has nothing to say about it until somebody unlocks it. The opposite kind of thing from the three rows below — those are the room's and are drawn as shadows; a solid is the take's and belongs on the paper. A solid with no `srcId` is given one here, after itself, so redrawing it REPLACES it instead of growing a second copy |
| `objects` | `objects[]` | **v5.8** — the FOOTPRINT of every model imported into the Scene Study: `{ id, name, person, at[], w, d, h, rot }`. Imports never become take facts, so without this the paper showed clear floor where a truss tower stands and a deck drawn through one looked fine. Relayed from the room, and the last one **replayed** on the handshake — see the note below |
| `ledLinks` | `links[]` | **v5.8** — which LED walls are one canvas, worked out in the room because it takes geometry to say so. The pad draws the tie and offers the way out of it |
| `objectFaces` | `faces[]` | **v5.8** — the significant FACES of those models, as the outline each one would become, already in take units and projected onto the plan. A footprint stops the paper drawing *through* a model; this is what lets somebody draw *with* one. Same family as the two above and replayed the same way — see `SCENE-STUDY-BRIDGE.md § Tool → host` for the row shape |

> **v5.8 · A PANEL THAT OPENS LATE OPENS ONTO THE SAME SHOW.** The drawing lives in the pad
> and the scene lives everywhere else, so every reload of the Sketch Pad — and every first
> open of it on a take somebody else built — began on blank paper beside a take that already
> had a deck, four walls and a set generated from a reference standing in it. The two
> surfaces then disagreed from the first stroke: the paper drew through geometry it could
> not see, BUILD re-proposed shapes the take already had, and a face taken in the room could
> be moved there and nowhere else.
>
> The handshake now says what is out there. `scene` carries the take's own solids, which the
> pad redraws. `objects`, `objectFaces` and `ledLinks` are none of them take facts — they are
> derived from geometry only the Scene Study holds — so the host keeps the **last one of each
> per take** in `ROOM_BY_TAKE`, beside the look and the venue bytes and with exactly the same
> lifetime: never saved, never forked, never sent to the agent, lost on reload. It is a
> replay, not a second copy: the Scene Study is still the only author, and it is asked to
> say it again (`resync`) at the same moment, so a room that is open and has moved on gets
> the last word. If no Scene Study is open, the replay is the answer — it is what the room
> last held.

### Panel → host

| type | payload | what the host does |
|---|---|---|
| `ready` | `capabilities[]`, `kind: 'sketch'｜'refs'` | replies `hello`, then `underlay` if it has one |
| `interpret` | the payload below | packages it with the scene snapshot and posts `/v1/interpret` |
| `solids` | `solids[]`, `drop[]`, `apply｜preview`, `clear?` | **v5.5** — build the traced outlines into the take, or ghost them in the Scene Study first. `drop` names traces that no longer exist, so BUILD means "make the scene match the sketch". NOT an interpret: no plan, no stream, no model. See `SOLIDS.md § Two lanes` |
| `selectSolid` | `srcId｜null` | **v5.5** — a shape was selected in the pad. The host maps the trace id to the take's solid and tells the Scene Study |
| `refine` | `planId`, `message` | posts `/v1/refine` |
| `cancel` | `planId` | aborts the in-flight request |
| `promoteFace` | `faceIds[]` (or `faceId`), `role`, `link?`, `lay?` | **v5.8** — faces of an imported model, held on the paper and named. Relayed to the Scene Study rather than answered here, for the same reason `linkLeds` is: the pad can SEE the faces because it was sent them, but the fit belongs to the only surface holding real geometry. They come back as solids through `addSolid`, so a face taken on the paper and the same face taken in the room are one op arriving by two doors. `link: true` asks for a set of LED faces as ONE CANVAS in the same breath, and `lay: 'flat'` asks for a HORIZONTAL LED rather than cabinets standing up out of the outline — the pad offers both on a flat face |
| `hoverFace` | `faceId｜null` | **v5.8** — the pointer is over that candidate; relayed so the room lights the same face. Nothing is built and nothing is selected |
| `deleteFace` | `faceIds[]` (or `faceId`) | **v5.8** — DEL on a held set of model faces, or the menu's DELETE FROM THE MODEL. Relayed for the same reason: the mesh only exists in the Scene Study. The solids already made from those faces are left alone |
| `dirty` | `strokes`, `stamps` (counts) | header state only — **no image travels on a stroke** |

### `interpret` from the sketch pad

```js
{
  v: 1, type: 'interpret', kind: 'sketch',
  png: ArrayBuffer,                  // the raster the model looks at
  canvas: { w: 1600, h: 1000 },
  projection: 'plan' | 'elevation',  // declared, never guessed
  scale: { pxPerMetre: 42.6, from: [x1,y1], to: [x2,y2], metres: 10 } | null,
  origin: [x, y],                    // world origin on the canvas; centre by default
  groundLine: y | null,              // elevation only
  strokes: [ { pts: [[x,y],…], w: 2, kind: 'pen'|'line'|'rect'|'ellipse'|'arrow' } ],
  stamps:  [ { label: 'PROJ', at: [x,y], rot: 0, note: '' } ],
  labels:  [ { text: 'FOH', at: [x,y] } ],
  note: 'five projectors from the balcony rail',   // the free-text prompt, optional

  /* v5.5 · FITTED OUTLINES, and the one part of this payload that is not in pixels.
     The pad holds the fit — which runs of ink were arcs, which vertices survived,
     what radius each arc was rounded to — so it is the only opinion about that
     geometry rather than a second one, and it hands over TAKE UNITS. Each solid says
     `units: 'take'` on itself so that can never be read the other way.
     Full schema, the bulge convention and the three roles: SOLIDS.md */
  solids: [ { id, units: 'take', role: 'stage'|'wall'|'led', plane: 'floor'|'front',
              closed, at: [x, up, depth], verts: [[a,b],…], bulges: [0,-1,…],
              h, base, thick, tile, fit: {…}, metrics: {…} } ],
}
```

### `interpret` from the reference board

```js
{
  v: 1, type: 'interpret', kind: 'refs',
  images: [ { name: 'tech-pack-p3.png', mime: 'image/png', bytes: ArrayBuffer,
              role: 'plan'|'elevation'|'photo'|'drawing'|'mood', note: '' } ],
  note: 'match the wall size in the drawing',
}
```

Panel-side limits, enforced before the bytes leave: at most **5** included
images, long edge downscaled to **1568 px**, PNG for line work and JPEG for
photographs — a ground plan re-encoded as JPEG loses the thin lines that were the
only reason it was dropped in. The host does **not** retain reference bytes: they
go into the request and are dropped. A venue `.glb` has to reach every panel of
the take; a reference only has to reach the model once.

---

## Part 2 · Host ⇄ the agent API (HTTP, `:3902`)

Bound to `127.0.0.1`. CORS allows `http://localhost:3900` and the `null` origin
so a `file://` host degrades rather than fails. Credentials come from the
environment — `ANTHROPIC_API_KEY` or an `ant auth login` profile — and never from
the browser.

### `GET /health`

```json
{ "ok": true, "v": 1, "model": "claude-opus-5", "interpreter": "agent",
  "stub": false, "credentials": true, "why": "", "plans": 3,
  "vision": { "ok": true, "engine": "smolvlm2",
              "model": "HuggingFaceTB/SmolVLM2-500M-Video-Instruct",
              "why": "…reads the drawing; the tracer measures it" } }
```

The plan panel polls this once on mount and names the *offline* state if it
fails, the way the Scene Study panel names its *lost* state. `vision` is **v5.5** and is its own state on purpose: the interpreter can be the real
model and still have no way to look at a picture. `smolvlm2` · `tracer` · `off`, and the
Reference Board shows it as a chip beside AID3N's own. `interpreter` is
`"stub"` or `"agent"` and `why` says which and why in one sentence — no
credential, `AGENT_STUB=1`, or `agent.py` absent. A panel that says STUB is
better than a stream that dies halfway through.

### `POST /v1/interpret` → `text/event-stream`

```json
{
  "v": 1,
  "takeId": "t7",
  "unitsPerMetre": 10,
  "intentHint": "rig",
  "sketch": { … the panel payload, bytes as base64 … },
  "images": [ { "role": "plan", "note": "", "mime": "image/png", "b64": "…" } ],
  "scene":  { … the same projection the scene bridge sends, verbatim … },
  "checklist": { "items": ["projectors","wiring"], "counts": { "projectors": 5 } },
  "catalogues": { … PROJECTOR_LIB / CAMERA_LIB / led / tracking … },
  "derived": { … take.derived as it stands … }
}
```

`scene` is **the same object the host already builds for the Scene Study**. One
projection of the take, two consumers — the agent gets no privileged view.

**SSE events** (`event:` name, JSON `data:`):

| event | data | the plan panel does |
|---|---|---|
| `open` | `planId`, `model`, `effort` | opens the plan, starts the timer |
| `thinking` | `delta` | appends to the reasoning strip (collapsed by default) |
| `note` | `delta` | appends to the narration — *"the two blobs upstage read as a 15 m LED wall"* |
| `ask` | `askId`, `tool`, `args` | a live read the API cannot answer alone (see below) — the host answers on `/v1/answer` |
| `op` | one op, below | appends a row, ghosts it in the Scene Study |
| `intent` | `intent`, `confidence`, `why`, `add[]`, `drop[]`, `reason` | validates, shows the chip |
| `done` | `planId`, `summary`, `confidence`, `risks[]`, `opCount`, `usage` | enables **Accept plan** |
| `error` | `code`, `message` | names the failure; never a partial apply |

Ops stream as they are decided, so the scene ghosts in while the agent is still
talking. A stream that dies mid-way leaves a plan that is **reviewable and
partial** — the panel says so, and accepting applies only what arrived.

### `POST /v1/answer`

The host's reply to an `ask`. This is how a read tool stays live:

```json
{ "v": 1, "planId": "p3", "askId": "a2",
  "result": { "derived": { "throwDistances": { "text": "…" } } } }
```

`measure_preview` is the reason this exists: the API asks, the host ghosts the
staged ops into the Scene Study, the tool measures real geometry and posts
`previewMeasured`, and the host answers. If no answer arrives within **4 s** the
API hands the model `{"unavailable": true}` and the model is instructed to say so
rather than invent a figure.

### `POST /v1/refine`

`{ planId, message }` → the same SSE stream, same conversation, effort `medium`.
*"No — the wall is upstage, the cameras are on the balcony."*

### `POST /v1/accepted`

`{ planId, accepted: [opId], rejected: [opId], edited: [{opId, …}], asFork: bool }`
→ `204`. Nothing is applied here — the host has already done that. This is the
agent's feedback: the next turn in the conversation is told what a human kept,
and the second sketch is better than the first because of it.

### `GET /v1/plan/{planId}`

The whole plan and its transcript, for replay, screenshots and design review.
In-memory, per process, capped — this is a prototype, not a store.

### `POST /v1/image` · `GET /v1/image/health`

**v5.9.3 — content for a wall, from a prompt.** The only endpoint here that has
nothing to do with a plan: it produces a picture rather than ops, and it writes
nothing to the take. The Aiden · content panel is its only caller.

`{ v, prompt, w, h, variant?, refine?, engine?, steps?, cfg? }` →
`{ ok, engine, chose, model, ms, w, h, asked, prompt, promptUsed, refined, … }`, or
`502` with `{ ok: false, why }`. `/v1/image/health` answers
`{ ok, engine, chose, model, engines, want, refine, note }` and is what the panel
polls on mount, the way the plan panel polls `/health`.

**TWO ENGINES BEHIND ONE ENDPOINT**, and every answer names which one ran:

| engine | what it is | returns |
|---|---|---|
| `drawthings` | **Z Image Turbo, generated locally by the Draw Things app** over its A1111-compatible HTTP API. Real diffusion, saved to `IMAGE_OUT_DIR` | `png` (base64), `path`, `saved`, `seed`, `steps`, `cfg`, `sampler`, `skew`, `warn` |
| `qwen-svg` | the fallback below: Qwen writes an SVG document, the panel rasterises it | `svg`, `tokens`, `stripped` |

`IMAGE_ENGINE` pins one; `auto` prefers Draw Things whenever it answers. The full
pipeline — optional Qwen prompt expansion, engine choice, geometry, output folder,
every named failure state and how to test it without the checkpoint — is
**`IMAGE-PIPELINE.md`**. The rest of this section is about the `qwen-svg` engine
only.

**`qwen-svg` IS NOT DIFFUSION, and the response says so.** LM Studio serves language
and vision-language models: its API has no `/v1/images/generations`, and
`qwen/qwen3.8-27b` is a text model. So Qwen is asked for one standalone **SVG
document** and the *panel* rasterises it at the canvas's real pixel size. `engine`
names what drew it so no panel can present it as something it is not.

That medium is a fair match for the job rather than a consolation: what these walls
play is very often procedural — curtains, sweeps, gradients, scan lines, colour
fields, test cards — and a vector document is resolution-independent, so one prompt
fills a 2 640 × 1 408 wall and a 15 360 × 1 080 ribbon without resampling. It also
arrives as text, which is the only reason it can be **checked before it is
rendered**: `imagegen.sanitise` strips every executable and remote construct and
reports what it took out, and an unclosed document is refused rather than repaired.

A real image model **did** arrive, and it went behind this same endpoint exactly as
this note said it would: the panel asks AID3N for content and does not care what drew
it. Nothing in the panel changed but the badge. See `IMAGE-PIPELINE.md`.

Synchronous, deliberately. A frame is ~12 s for something plain and 45–70 s for
something dense: far too long to hide behind a spinner, far too short to deserve a
plan store. The panel shows the plan panel's own indeterminate sweep with an elapsed
clock beside it and a working stop, which is the honest form of a progress bar when a
single completion has no progress to report.

---

## Part 3 · The plan and its ops

A plan is a named, ordered list of ops with a summary and a confidence. Every op
maps onto a mutator that already exists, and carries its own reason.

```js
{
  id: 'p3', takeId: 't7', intent: 'rig',
  summary: 'Five projectors on the FOH rail covering an 18 m upstage wall.',
  confidence: 0.78,
  risks: ['no scale declared — positions fitted to the concert preset'],
  ops: [ … ],
}
```

```js
{
  id: 'o4',
  kind: 'add' | 'place' | 'aim' | 'decide' | 'remove' | 'duplicate'
      | 'venue' | 'track' | 'route' | 'note' | 'audience' | 'block' | 'solid',
  why: 'the third stamp on the rail, 4.2 m stage-left of centre',
  confidence: 'declared' | 'fitted' | 'guessed',   // never absent
  // kind-specific:
  req: 'projectors', model: 'BARCO G62-W14',       // add
  objId: 'projectors-3',                            // place / aim / decide / remove / duplicate
  // on an `add`, objId is the agent's own HANDLE for a thing that does not exist
  // yet — `aim` and `set_decision` name it, and the host maps handle → real id as
  // it applies the plan, because the id is whatever addDevice assigns
  at: [x, y, z],                                    // TAKE UNITS, always
  rot: { x, y, z },                                 // aim — DEGREES on the wire
  w, d, h,                                          // take units, for what a catalogue cannot know
  stepId: 'projectors.lens', value: '1.00 : 1',     // decide
  preset: 'concert', bounds: { w, d, h },           // venue
  name: 'OPENER', startMs: 0, route: 'led-1',       // track
  from: 'srv', to: 'matrix', medium: 'SM FIBRE',    // route
  text: 'sightline blocked from row A',             // note
}
```

`confidence` is per-op and mandatory. `declared` = the drawing said so (a stamp,
a scale bar, a number in a tech drawing). `fitted` = derived from the venue's own
dimensions. `guessed` = a reasonable default the agent chose. The plan panel
ramps the row colour off it, and **`guessed` ops are unticked by default** — the
human opts *in* to a guess.

### Applying

| op | mutator |
|---|---|
| `add` | `addDevice(req, model, at)` |
| `place` | `moveObject(t, objId, x, y, z)` |
| `aim` | `t.rot[objId] = rot` |
| `decide` | the same setter the Task editor uses — so the step closes, the checklist moves, the cost changes |
| `remove` / `duplicate` | `removeObject` / `duplicateObject` |
| `venue` | `t.venue`, then the tool's own venue path |
| `track` | `addDevice('sequence', null)` + the timing / media decisions |
| `route` | the wiring model's route setter |
| `note` | `t.notes` — the one new store, and the only op with no v4 equivalent |
| `solid` | **v5.5** — `t.solids`, through `sanitiseSolid`. A fitted outline with a role; see `SOLIDS.md` |

**The bridge adds no mutation path of its own.** Same sentence as the scene
bridge, and for the same reason.

---

## Part 4 · The agent's tools

The tool surface is the take's vocabulary, not CRUD. **Write tools stage into
the plan; read tools are live.** Python: `@beta_tool` functions passed to
`client.beta.messages.tool_runner(...)`.

**Read** — answered from the request, or by an `ask` round-trip to the host:

| tool | returns |
|---|---|
| `read_scene()` | devices, venue, tracks, checklist items, current `derived` |
| `read_catalogue(req)` | the real rows — `mm`, `lumens`, `res`, `lens`, `cost` — so it picks kit that exists and the cost panel prices it |
| `measure_preview()` | `derived` for the ops staged so far, via the ghost round-trip. `{"unavailable": true}` on timeout — and the model is told to report absence, never to invent |
| `read_reference(n)` | **v5.5** — one uploaded reference, TRACED: every shape the drawing encloses, fitted to vertices and true arcs, already in take units, with what the layout and the vision model each think it is. The instruction is blunt — *you can see the image and you cannot measure it* — so the bodies go to `add_solid` unchanged. See `VISION.md` |

**Stage** — each returns a confirmation, the running op count, and a warning past
**24** ops so the model self-limits:

`set_venue` · `add_device` · `place` · `aim` · `set_decision` · `remove` ·
`duplicate` · `add_track` · `route_signal` · `annotate` · `add_solid`

`add_solid` is **v5.5** and the system prompt is blunt about it: the pad holds the
fit and the model does not. Pass a fitted solid through unchanged; author one only
for geometry nobody traced; never propose a `wall` where somebody meant LED just to
get a smooth curve, because that is a wall nobody can build.

**Close:**

| tool | effect |
|---|---|
| `declare_intent(key, why, add[], drop[], confidence)` | the classification and the override request; host-validated |
| `finish(summary, confidence, risks[])` | ends the turn and emits `done` |

### Request shape

```python
runner = client.beta.messages.tool_runner(
    model="claude-opus-5",
    max_tokens=64000,
    thinking={"type": "adaptive", "display": "summarized"},
    output_config={"effort": "xhigh",
                   "task_budget": {"type": "tokens", "total": 48000}},
    betas=["task-budgets-2026-03-13", "server-side-fallback-2026-07-01"],
    fallbacks="default",
    system=SYSTEM,          # stable: the rules, the frames, the catalogues
    tools=TOOLS,            # deterministic order — it is part of the cache prefix
    messages=[{"role": "user", "content": [ *images, {"type": "text", "text": brief} ]}],
)
```

- **Streaming is load-bearing**, not decoration: a full interpret runs tens of
  seconds and the narration is what makes that legible.
- `display: "summarized"` is explicit because the default on Opus 5 is
  `omitted` — and here the reasoning is a design asset.
- **Effort** `xhigh` for interpret, `medium` for refine.
- **Caching:** render order is `tools` → `system` → `messages`. The system prompt
  and the catalogues are stable, so the breakpoint goes after them; the scene
  snapshot, the images and the brief go last, after it. Verify with
  `usage.cache_read_input_tokens` — a zero across repeated calls means something
  volatile crept into the prefix.
- **Refusal fallbacks** are on by default; a decline before output is not billed.

### What the system prompt has to say

Short list, because each line is there to prevent a specific failure:

1. Positions are **take units** (decimetres). You are given `unitsPerMetre`. Never
   emit metres.
2. `+y` is up, `+z` is downstage toward the audience, `−z` is upstage. In a plan
   sketch the top of the canvas is upstage.
3. Only ever name kit from the catalogue you were given.
4. Every op carries a `why` and a `confidence`. Say `guessed` when you guessed.
5. If a figure needs geometry, call `measure_preview`. If it comes back
   unavailable, say it is unavailable.
6. Classify one intent, and justify any panel override in one sentence.
7. Stop at `finish`. Under 24 ops; if the drawing implies more, propose the
   structure and say what you left out.

---

## Part 5 · Additions to the scene bridge

Backwards-compatible additions, so `BRIDGE_V` **stays 1** — the tool ignores what
it does not know, per that document's own rule.

### Host → tool

| type | payload | meaning |
|---|---|---|
| `snapshot` | `view: 'top'｜'iso'`, `w`, `h` | render once off-screen and post the PNG back |
| `agentStatus` | `phase`, `label`, `note`, `ops` | what the agent is doing, shown over the viewport. Only `building`, `measuring` and `applying` are drawn: an agent still *reading* a drawing is not yet doing anything to this scene, and saying so over an empty room is noise |
| `preview` | `planId`, `ops[]`, `measure?` | draw the staged ops as **ghosts** — the palette's INFO violet at low opacity, drawn without depth — and, with `measure`, measure them |
| `ghostClear` | `planId?` | drop the ghosts. **v5.5**: two lanes ghost now — an agent plan and the Sketch Pad's own solids, whose ops carry `planId: 'sketch-solids'` — so a `planId` narrows it and clearing one cannot clear the other. No id still means "clear whatever is there" |

### Tool → host

| type | payload | what the host does |
|---|---|---|
| `snapshotImage` | `png` (ArrayBuffer), `view` | forwards it to the sketch pad as `underlay` |
| `previewMeasured` | `planId`, `derived{}` | answers the pending `ask` on `/v1/answer` |

Ghosts are **view, not fact.** They never enter the `scene` message, they are not
pickable, their measurements go to the **plan** and not to `take.derived`, and
they vanish on `ghostClear` or when the plan is accepted. Accepting is what turns
a ghost into a device — through `addDevice`, like everything else.

Two things about the implementation are worth knowing, because they are what make
the figures trustworthy. A ghost is a **device record like any other**: it goes
through the tool's own `makeDevice`, so a proposed projector has the body of the
catalogue row it names and throws the beam its proposed lens would throw, and the
measuring pass reads it without knowing it is not real. There is no second
geometry and no second measuring path. And `measure()` has one exit with two
destinations — `previewMeasured` while a proposal is ghosted, `measure` otherwise
— so a proposal can never quietly become the take's derived truth.

**Violet, not magenta.** The obvious choice is wrong: in this palette magenta is
`status/failed`, and a proposal is not a failure.

**A `venue` op is not previewed.** Rebuilding the room under a review is a bigger
jolt than the preview is worth, so the plan says so in words instead.

---

## Changing this protocol

Adding a message type, an event, an op kind or a field is backwards-compatible
and needs no bump. Changing the meaning of an existing field, or its units,
raises `AGENT_V` on every side — and every side then refuses to talk to an old
counterpart rather than half-work.


---

## What the panels are told, and what crosses a boundary

`hello` carries the vocabulary rather than letting each side keep a copy: the
resolved BrandOS tokens, `unitsPerMetre`, the venue as the take knows it, the
**stamp labels** the Sketch Pad offers, the **reference roles** the board offers,
and `maxIncluded`. One decision, transmitted — the panels transcribe nothing.

**postMessage clones, and a Vue reactive proxy cannot be cloned.** Everything
crossing into a panel or into the tool is flattened to plain data first. This is
written down because of how the failure presents: the `DataCloneError` is thrown
inside the *sender*, so it looks exactly like the other side ignoring the
message — the ghosts simply never appeared and the measurement "timed out".


---

## Phases — one wait, said in three places

An interpret is silent for tens of seconds while the model looks at the drawing, so
"loading" for the whole run tells you nothing about whether it is stuck. The host
keeps a phase, derived entirely from things the bridge already sees, and pushes the
same words to every surface somebody might be looking at: the input panel, the plan
panel, and the Scene Study.

| phase | when | shown as |
|---|---|---|
| `sending` | the payload is being packaged here — rasterise, base64 | PREPARING · *packaging what you drew* |
| `reading` | the request is out, no op back yet | READING · *the agent is looking at the drawing* |
| `building` | ops are arriving and being ghosted | BUILDING THE SCENE · *n proposed so far* |
| `measuring` | an `ask` is out, waiting on the tool's geometry | MEASURING · *asking the Scene Study what this covers* |
| `applying` | somebody accepted; the mutators are running | APPLYING · *n ops into TAKE A* |
| `done` / `error` | over | PLAN READY · *n ops to review* |

The indicator is **indeterminate** — one sweeping segment, in the agent's violet.
An interpret has no honest percentage and a fake one is worse than a moving bar.
Nothing can be accepted while `applying` is on screen.

The panels also own the phases the host cannot see: the Sketch Pad says PREPARING
while it rasterises its canvas, and the Reference Board says READING FILES · *3 of 5*
while it decodes and downscales, which on a phone photo is a real wait.


---

## AID3N, and who is answering as AID3N

The agent has a name, and it is the platform's own: **AID3N**. What used to show in
the panel headers was `STUB` — the name of an implementation, leaking into a demo
surface. The name is now constant; what changes is the **engine** behind it, shown
as a dot and a tooltip rather than a word, because it matters to us and not to the
room. It is never hidden: *was this a model or not* is the one question a reviewer
must always be able to ask.

| engine | who answers | `/health` |
|---|---|---|
| `claude` | `agent.py` — the model called from inside the service | `engine: "claude"` |
| `external` | an agent outside it, driving the plan over HTTP | `engine: "external"`, `attached: "Claude Code"` |
| `mock` | `stub.py` — deterministic, instant, free, no model | `engine: "mock"`, and `why` says why |

`auto` prefers an attached external agent, because attaching is a deliberate act by
something that intends to answer. `AGENT_ENGINE=mock｜claude｜external` pins one.

### The external channel

The credential problem had an obvious way round it: something with model access was
already in the room. So a plan can be **parked** — the sketch is written to
`agent/inbox/` as a real PNG somebody can open, the SSE stream stays live, and an
outside agent stages the ops in. The host cannot tell the difference, which is the
test that the boundary was drawn in the right place.

| route | what it does |
|---|---|
| `POST /v1/attach` | announce an external agent (`{name}`); 5-minute TTL, refreshed by any inbox read |
| `GET /v1/inbox` | what is parked: `planId`, the brief JSON, the image paths, how long it has waited |
| `GET /v1/plan/{id}/brief` | the same facts the local model gets, over HTTP instead of off the disk |
| `POST /v1/plan/{id}/note` | narration — it streams into the plan panel as AID3N's own voice |
| `POST /v1/plan/{id}/op` · `/ops` | stage one op, or a list. Same validation, same events, ghosts immediately |
| `POST /v1/plan/{id}/intent` | the classification and any panel override |
| `POST /v1/plan/{id}/measure` | the ghost round-trip on demand: real geometry, measured off the staged proposal |
| `POST /v1/plan/{id}/finish` | ends the turn and releases the parked stream |

A parked plan waits **15 minutes**. If nothing answers, whatever was staged is kept
and the plan says the agent stopped answering — never a silent empty result.

---

## Accurate in size, shape and orientation

Four things carry this, and only one of them is new:

- **Size** was already right and stays right: device bodies are built from the
  catalogue's real millimetres, so *naming the right model is the size*. What a
  catalogue cannot know now travels too — `w`/`h` on an `add`, so an LED wall read
  off a plan is 16 m wide because the plan said 16 m, not because 7.4 m is the
  tool's default. A wall's `size` change rebuilds its geometry, and the pitch
  measurement follows: 16 m over a 3840 px map is 4.17 mm, derived.
- **Shape** is the catalogue too — a projector has a body, a lens and a yoke; a PTZ
  camera has a dome and a different mount; a tracking base is a downward cone.
- **Orientation** is a yoke basis, not a `lookAt`: local Z is the aim, local X is
  forced horizontal. Left alone, a projector aims at a surface it can plausibly
  cover, and a camera at the stage. An `aim` op overrides that, and it is in
  **degrees** — a model reasoning about *"35° toward the screen"* is far more
  reliable than one emitting `0.611`, so the conversion happens at the boundary,
  once, exactly like the units.
- **Decisions that are geometry** must be staged, not left: a lens is a throw ratio,
  a resolution is the shape of what is thrown, a pixel map is the aspect of a wall.
  A position without a lens is a body without a beam.

## `audience` — the only op that is neither a device nor a decision

```js
{ kind: 'audience', at: [x, y, z], w, d, rot: { y }, why, confidence }
```

An AUDIENCE anchor becomes **people**: one instanced silhouette per person, jittered
on a grid, each a different height and handedness, all turned toward the stage.

Why it is worth having at all: **a room with nobody in it has no scale.** Every
judgement made looking at a Scene Study — is that wall too high, is that camera too
close, can row A see the screen — is a judgement against human size, and until there
are humans in it the eye has nothing to measure against.

Ownership is unchanged. *Where* the audience is and *how big* it is are facts, so the
take carries them (`take.audience`) and they fork with everything else. The people
are geometry, so they live in the tool. And the size comes from the drawing when the
drawing has it: the smallest rectangle enclosing the anchor is the seating block
somebody drew round it — which is exactly what the vector record is for.

Unlike `venue`, a proposed crowd **is** ghosted, because it is the one thing in the
scene that gives the rest of it human scale and it costs a single instanced draw.


---

## Z-up naming, and the one thing that does not change

**The room is named Z-up.** Red **X** across, blue **Y** into the room (positive
downstage), green **Z** up. That is what a lighting plan, a CAD file and everybody in
the room already means, and it is now what the gizmo, the Scene Study's floor axes,
the sketch pad's axes and the position fields all say.

**The wire does not change.** A take stores a position as `[across, up, depth]`
because three.js is Y-up and the whole tool is built on it. So the ORDER on the wire
stays and the NAMES are mapped in the display layer — `AXIS_NAME`/`XYZ_ORDER` in the
host, `AXES[].n` in the tool. Renaming the storage would mean touching every mutator
to gain what a label already gives. Both conventions are spelled out in the brief the
interpreter receives, because mixing them is the one mistake that puts a projector in
the floor:

```json
"frames": { "wire_order": "at = [across, UP, DEPTH]",
            "X": "across · FIRST number", "Z": "UP · SECOND number",
            "Y": "into the room · THIRD number" }
```

## The grid is the scale

The sketch pad draws **1 m squares** — the same metre the Scene Study's floor grid
draws — and says so. So a drawing with no scale bar is not a drawing with no scale;
it is one measured in squares, and nothing has to ask. `scale.basis` is `"grid"` or
`"drawn"`, and the scale gesture survives only for drawing over a plan at some other
scale. **TOP** and **FRONT** are the two projections: top is X across and Y into the
room, front is X across and Z up.

## `block` — the drawing, at the size it was drawn

```js
{ kind: 'block', name, at: [x, bottom, z], w, d, h, rot: { y }, why, confidence }
```

A rectangle is the most common thing anybody draws and the one thing this bridge had
no way to receive. A block is **not kit**: it never joins the checklist and it claims
nothing except its dimensions — a deck, a riser, a screen, a banner, a truck. `at` is
the point the thing rests on, which is the same rule in both projections.

Height is the interpreter's business, not the tool's: a rectangle in a TOP view has no
height on the page, so it arrives as a low footprint; the same rectangle in a FRONT
view has real height and no depth, so it arrives as a thin upright.

## `aim` — a target, not angles

```js
{ kind: 'aim', objId, at: [x, y, z] }      // preferred: point at THERE
{ kind: 'aim', objId, rot: { x, y, z } }   // degrees, if something has them
```

Dragging out of a PROJ · CAM · TRACK anchor on the sketch says which way it points,
and what travels is **the point it was dragged to** — because that is what the gesture
means, it is how anybody describes an aim out loud, and it goes straight through the
yoke basis that already makes hand-aiming behave. No Euler order to get backwards, and
a device aimed from a drawing lands in exactly the frame a device aimed by hand does.
In a TOP view the target is on the floor; in a FRONT view it carries the height that
was drawn.


---

## A stamp NAMES a drawing; it is not a second object

The rule that decides how a sketch becomes a scene:

> An anchor dropped inside a rectangle says **what that rectangle is**. It never
> adds an object of its own.

So an LED stamp on an 8 m rectangle produces **one** 8 m wall — not a wall and a
default-sized processor on top of it, which is what it did before. A PROJ or CAM
stamp inside a rectangle places that device **at the rectangle's centre**, sized from
the catalogue, because a rectangle round a projector is saying where and how big, not
"a box as well". An anchor with no rectangle around it places a device at its own
point, as it always did.

The interpreter therefore claims boxes first and only then places the anchors that
claimed nothing. The plan's summary is counted **off the ops**, not off the drawing,
for the same reason: "2 rectangles and 2 devices" reads as a double placement even
when there is not one.

## Front view: height zero is the ground line

In a TOP view the horizontal axis runs through the origin. In a FRONT view it is the
**ground**, and the two are not the same line. Drawing the X axis at the origin in a
front view put it halfway up the wall, so an anchor dropped on the red line came out
two metres in the air — which is what looked like the axes flipping. The red X axis
and the ground line are now one line, the grid is anchored to it, and a point on it
reads `0.0 m up`.


---

## One sketch, two views

The pad used to hold 2D pixels with a label on them, so toggling TOP/FRONT relabelled
the axes and left the drawing where it was. It now holds **one sketch seen two ways**:
every item remembers which view drew it, and anything drawn in the other one is
re-projected through the room to reach the page you are looking at.

| drawn in | knows | seen from the other view |
|---|---|---|
| **TOP** | X across, Y depth | collapses to a line on the ground — the drawing never said how tall |
| **FRONT** | X across, Z height | collapses to a line on the room's centre — it never said how deep |

That collapse is the honest answer rather than a defect, and seeing it is how you
notice the third dimension has not been established yet. Cross-view items draw
**dashed and dimmed**, they are not hit-testable (switch views to move the thing), and
the footer counts them separately: `0 STROKES · 1 FROM THE OTHER VIEW`.

**Both views travel.** Each stroke, stamp and label carries `view`, and the payload
carries both of the page's zeros — `origin_y` for depth and `groundLine_elevation` for
height — because an item drawn in the other view was measured against that view's
zero. `Frame.take(px, py, view=…)` converts per item, so interpreting from TOP no
longer throws away the heights a FRONT drawing established. Every decision in the
reader follows **the box's own view**, not the view that happened to be on screen when
INTERPRET was pressed.
