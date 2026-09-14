# PRODUCTIONS v5 — the sketch, the agent, and the task

The plan for v5. v4 is frozen in the folder above this one and stays the working
demo until v5 can replace it end to end.

> **This folder is v5.5.** `v5/` is frozen as the previous step. v5.5 changes one
> thing and changes it thoroughly: **the sketch pad can now build the shape it
> drew.** A traced curve is fitted to vertices and true circular arcs and becomes
> real geometry in the Scene Study — an extruded deck, a curved wall a projector can
> throw at, or an LED wall faceted into flat cabinets. The contract is `SOLIDS.md`,
> written before the code like the other two, and both existing protocols stay at
> version 1 because every addition is additive. See **§ Solids — v5.5** below.

| | |
|---|---|
| **Host** | `v5/production-hub-v5.html` — was `productions-taskflow-v5.html`; the take model and layout engine are v4's, the front door is not |
| **Tool** | `v5/scene-study-3d.html` — copy of v4's, gains a ghost-preview mode and a snapshot message |
| **New panels** | `v5/sketchpad.html`, `v5/refboard.html` — iframes, same pattern as the Scene Study |
| **New service** | `v5/agent/` — the Studio Agent API, FastAPI on **:3902** |
| **Contract** | `v5/AGENT-BRIDGE.md` — HTTP + the postMessage additions. Written before the code, like the scene bridge was. |
| **Contract · v5.5** | `SOLIDS.md` — the fitter, the bulge convention, the three roles, the units argument |
| **Contract · v5.5** | `VISION.md` — reading an uploaded reference: SmolVLM2 over a deterministic tracer, and the arbitration between them |

---

## What changes, in one paragraph

v4 asks you to *tell* it the job: pick a profile, tick the checklist, then place
devices by hand. v5 lets you *draw* it. A sketch or a pile of reference images
goes to an agent; the agent reads the drawing, works out what is being proposed,
and answers in the take's own vocabulary — add these devices, put them here, aim
them there, this is a concert stage, this LED wall is 15 m wide. That answer is a
**plan**: reviewable, explainable, accepted or rejected op by op. And because the
agent now knows *what you are doing* — not who you are — the workspace stops
being configured by role and starts being configured by **task**.

Three consequences, in the order they matter:

1. **The role lens goes.** It was always a proxy. "CLIENT" was never a person,
   it was the task *explain the plan to someone who is not building it*. v5
   replaces `ROLES` with `INTENTS` and keeps the same layout algorithm.
2. **Nothing the agent decides is applied silently.** The agent stages ops; the
   take is mutated only by a human accepting them. The take stays the source of
   truth, and the prototype gains a diff you can screenshot in a design review.
3. **The drawing is data, not just pixels.** A sketch that declares its
   projection, its scale and its labelled anchors is worth an order of magnitude
   more than a napkin photo. The sketch pad is designed to make declaring those
   things cheaper than not declaring them.

---

## The landing — the sketch stage

The front door is **not** the entry model any more. You land in the phase before a
production exists.

```
   SKETCH ───────────► DESIGN ──────────► PRODUCE ─────────► DEPLOY
   draw it             the agent          the checklist       the show
   drop a reference    builds the scene   the tasks, money
                                          ▲
                                   START PRODUCTION
                                   (the onboarding, arriving late)
```

**The landing is three panels**: the two ways in on the **left** — Sketch Pad above,
Reference Board below — and on the **right** the Scene Study they fill. Input then
result, in reading order. No modal, no profile question, no checklist to tick. The
plan panel joins the input column by itself the first time the agent answers, and
only in this stage: in a workspace somebody arranged, nothing moves.

**And the Scene Study opens EMPTY** — a ground grid and nothing else. v4 defaulted
to a concert stage because a take always had one; here that would be a decision
nobody made, in the one phase where nothing has been decided, and the agent would
then have to argue with a room it did not propose. So the tool's default venue is
`none`, the sketch take's venue is `none`, and **the room is the first thing the
agent proposes off the drawing** — a `venue` op like any other, ticked or rejected
like any other.

**The ground is the light end of the grey ladder now.** A near-black viewport read
as *"the tool is broken"* more often than it read as a room, and it is the wrong
default for a scene you are about to fill. So the Scene Study's ground and its grid
are offered the **same swatch selection** — Gray 600 · 700 · 800 · 850 · 900, with
600 the default — because they are two halves of one decision: a light ground wants
a dark grid, and the old build could not say that at all (every grid tint on offer
was *lighter* than the room). **Gray 850** is the new step that makes it possible:
a scene-only value between Gray 800 and Gray 900, **mixed from the two tokens
rather than typed**, so no hex is authored and it cannot drift from either. The list
is transmitted in `hello` like everything else — one selection, two uses, no second
copy to keep in step.

Two consequences worth keeping:

- A **STAGE anchor plus a declared scale** makes that op `fitted`, not `guessed` —
  the room's *size* comes from the drawing, and only the choice of preset is a
  guess, which is what the op's `why` says. So the room appears by default when the
  sketch actually said how big it is, and stays unticked when it did not.
- Everything else in a plan is positioned **relative to a room**, so a rejected
  venue is not one op fewer — it is every other op landing on an empty grid. The
  plan panel says so in as many words rather than letting it be discovered in the
  3D.

**The onboarding is parked behind one CTA.** `START PRODUCTION →` sits in the top
bar, locked with a reason until the scene has something in it. It opens the same
three-step entry model v4 had — but it opens at **step 2**, with the checklist
already ticked, because the sketch answered step 1 by building the scene.

**Why that is the right shape, and not just a nicer order.** The sketch still
lives in a take — a take is what owns a scene — but one with an **empty
checklist**. Accepting an op calls `addDevice`, which calls `ensureItem`, which
adds the checklist item that device belongs to. So the checklist **builds itself
from the drawing**: four projector anchors and a camera produce SET UP PROJECTORS
and SET UP CAPTURE, 5 objects, 29 tasks, and nobody ticked a box. By the time the
CTA is pressed, the questions the modal used to ask up front have mostly been
answered by the drawing — which is the argument for parking it.

Pressing it **promotes** rather than creates: every object, position and decision
the sketch produced is kept and becomes TAKE A. The counts in step 3 only *add*.
Verified: `GLASTONBURY PYRAMID · TAKE A · OPTION · 0/23 tasks done`, positions
unchanged, the workspace opening on RIG PROJECTION with real measurements already
derived.

Two details that follow from the rule about not moving panels under someone's
hands: while sketching, an accepted plan does **not** apply the task lens (there
is no task yet — the task is the sketch), and the rail says **STAGE · SKETCH**
instead of offering a lens with no checklist to key off. The task arrives with the
production.

`newSketch()` exists and is exported, so a second sketch alongside a running
production is a one-line addition when it is wanted.

---

## The rule the whole thing hangs off

The scene bridge already has one, and v5 does not get to break it:

> **The take owns the facts. The tool owns the view.**

v5 adds a third clause:

> **The agent owns nothing. It proposes.**

Practically: the agent API never talks to the Scene Study, never holds a take,
and has no database. It is a pure function of *(scene snapshot + images +
conversation)* → *a plan*. The host is its only client, because the host is the
only thing that holds the facts. Every op in a plan is applied through the
mutators that already exist — `addDevice`, `moveObject`, `setValue`,
`removeObject` — for the same reason the 3D drag was: it *is* that event.

That single decision is what keeps this from becoming a second, competing model
of the production.

---

## Topology

```
                 :3900  static  ─────────────────────────────────┐
                                                                 │
  ┌───────────────── production-hub-v5.html  (the HOST) ────┴──────────┐
  │                                                                          │
  │   ed-sketch ──┐                                        ┌── ed-stage      │
  │   (iframe      │  postMessage                          │   (iframe       │
  │    sketchpad)  ├──────────────►  the take  ◄───────────┤    scene-study) │
  │   ed-refs   ──┘                    │  ▲                └── ed-preview    │
  │   (iframe                          │  │                                  │
  │    refboard)                       │  │ accept                           │
  │                              ┌─────▼──┴─────┐                            │
  │                              │  ed-agent    │  the plan, op by op        │
  │                              └──────┬───────┘                            │
  └─────────────────────────────────────┼────────────────────────────────────┘
                                        │  fetch + SSE
                              ┌─────────▼──────────┐
                              │  :3902  agent API  │  FastAPI · anthropic SDK
                              └─────────┬──────────┘
                                        │  Messages API, tool loop
                                  claude-opus-5
```

**Panels are input devices.** The sketch pad and the reference board hold no
take state and never call the API themselves. They post their payload to the
host; the host is the one client of :3902. That buys: one auth path, no CORS
matrix, no key in an HTML file, and panels that still boot standalone against
their own mock — the standing test that a panel is genuinely external.

Ports: **3900** static (existing), **3901** mm-proxy (existing, untouched),
**3902** agent API (new).

### The third panel

You asked for two. Propose-then-apply needs a third, and it is the one the
design lives in: **ed-agent**, the plan panel. In-host Vue, not an iframe — it
renders take facts and drives take mutators, so it belongs on this side of the
boundary. It holds the agent's narration, its reasoning summary, the ops list
with per-op accept/reject, the intent it classified and why, and the single
**Accept plan** action. Without it the agent is a magic trick; with it the agent
is a colleague showing their working.

---

## The sketch pad — `sketchpad.html`

> **v5.5 · the icons are BrandOS.** Not drawn, not approximated: the canonical Disguise
> UI glyphs, lifted verbatim from the vault's own library
> (`2ndBrain/Resources/Disguise Icon Library/All Icons`, the same 3,627-glyph set the
> workspace's other 43 came from) and embedded as an inline sprite with `fill:
> currentColor`. The first cut of this bar was hand-drawn SVG that *looked* like the
> family and was not in it — the same mistake v2 made with typographic characters, off
> the grid and answerable to nobody. Each symbol is named for what it does here and
> commented with the glyph it is, so the mapping back to the library is greppable.
> `polyline` for TRACE is the happy accident: it is literally a chain of segments with
> its vertices marked, which is what the fitter produces.
>
> The workspace's own **ICON DEBT is paid** at the same time — `sketch`, `refs` and
> `agent` borrowed `edit`, `dashboard` and `priority` while the Figma plugin was
> unreachable, and now carry `draw`, `photo_library` and `wand_stars` from the vault.
>
> **v5.5 · the bar is icons.** Eighteen text labels was 640 px of toolbar in a panel that
> is routinely 260 px wide, so everything scrolled and the things at the end — the stamp
> palette among them — were effectively gone. One inline sprite, drawn in the file because
> this panel has to boot from `file://` and a toolbar whose meaning arrives over HTTP is a
> toolbar that is sometimes blank. Six groups, separated: **projection** (the only STATE
> on the bar, and the only pair with a filled mark) · **select** · **draw** · **geometry**
> · **edit** · **what the drawing is measured against**. Every icon keeps a full-sentence
> tooltip, and the footer names the armed tool in words — the icon is for finding it
> again, the tooltip is for learning it the first time.
>
> Renamed to what a drawing office calls them: **PLAN** and **ELEVATION**. TOP and FRONT
> were describing the camera.
>
> **SELECT (V) is new**, and it is the tool the pad was missing: click anything — a
> stroke, a label, an anchor, a shape — and drag it. Strokes and labels could not be moved
> at all before, which made a drawing something you redraw rather than rearrange.
>
> **The ARROW drawing tool is gone.** An arrow drawn on a sketch said nothing the AIM
> gesture does not say better, and it was one more thing in a bar that had too many.
> SCALE stays: drawing over a plan at some other scale is a real case.

Free drawing, but with three declarations that do most of the accuracy work:

| declaration | how it is made | what it buys |
|---|---|---|
| **Projection** | a two-state toggle: **PLAN** (↑ upstage) / **ELEVATION** (ground line) | removes the single largest source of 3D ambiguity |
| **Scale** | two-click gesture on a drawn line, type a distance: *"this is 10 m"* | pixels become metres, so positions become real |
| **Anchors** | a stamp palette — PROJ · CAM · LED · TRACK · STAGE · AUDIENCE · SCREEN — dropped and dragged | high-confidence labelled points instead of guessed blobs |

Everything else is ordinary: pen with pressure, eraser, straight line, rect,
ellipse, text label, arrow, undo/redo, clear. Colour is not a variable — one ink,
BrandOS `--text-primary`, because a legible mono-ink sketch reads better to both
the model and the room.

**Two things travel, not one.** On *Interpret* the panel posts the rasterised
PNG *and* the vector record: strokes as polylines, stamps with labels and
positions, the scale factor, the projection, and the canvas size. The image is
what the model looks at; the vectors are what makes its answers snap to what you
actually drew.

**Optional underlay.** The Scene Study can post a top-down snapshot of the
current scene; the sketch pad draws it faint underneath. You then sketch *over*
the existing rig and registration is free — no "where is this relative to what
you already have" guesswork.

---

## Solids — v5.5

The fourth declaration, and the biggest one: **what a shape IS.**

v5 could receive a rectangle — `block` ops carry `w`, `d`, `h` and the tool builds
a box. That is right for a riser and wrong for the thing people draw first, which
is a curve. Fitting a bounding box throws away the only reason somebody drew a
curve; shipping the raw ink is not a stage, because three hundred jittery points
cannot be built, priced or measured.

So the pad does what a draughtsman does. It **reads** the outline, decides which
runs of it are arcs and which are straights, and re-states it as the few vertices
and true circular arcs the hand was aiming at — resample, RDP simplify, algebraic
circle fit, regularise to a buildable grid and radius, symmetrise if the shape is
nearly symmetric. Every one of those is a correction, so every one is reported:
raw points in, vertices out, arc radii, the RMS it gave away, whether symmetry
fired, whether a vertex was later moved by hand.

**A curve travels as a bulge**, the CAD convention — signed sagitta over
half-chord — so one number per segment carries a true arc, and the pad walks it to
a quarter of a pixel while the tool walks it to two centimetres. One geometry,
sampled twice; neither is the other's approximation.

**A trace is a filled solid until something says otherwise.** Every traced outline
is closed, faced and extruded — `stage`, half a metre thick, because that is what a
shape drawn on a plan almost always is and a ring of ribbon with nothing inside it
is not something anybody can stand on. Closure is *forced*, not detected, since a
hand rarely closes a loop exactly; what the drawing actually said is remembered, and
it becomes the right answer the moment the shape is named WALL or LED, which are
runs.

**The role is a STAMP, not a mode.** It is not armed before the trace — it is
declared afterwards by dropping a stamp on the shape, which is the rule the
interpreter always used (*"dropping LED on a rectangle says that rectangle IS the
wall"*) extended to real geometry. On empty canvas the same stamp is what it always
was: a declared position for a piece of kit. `WALL` joins the palette; `PROJ`, `CAM`
and `TRACK` stay positions even on top of a shape, because a projector standing on a
deck is a projector standing on a deck.

**Three roles, because three things behave differently in a room:**

| role | what gets built | why it is its own builder |
|---|---|---|
| `stage` | the outline is a footprint, extruded to height | the curve is the point; the area is measured by shoelace *over the tessellation*, so an arc contributes the area an arc has |
| `wall` | the outline is swept into a real surface with real normals | a projector throws at it: the throw distance, the image size and the lit footprint are then measured against the **curve**, not against a flat stand-in that would have made all three wrong in the same direction |
| `led` | the outline is **faceted** into flat panels of whole cabinets | **LED does not bend.** A flat chord may sit no more than half a cabinet inside the arc that was drawn, so the facet count comes from the curvature — and what you are proposing is a cabinet count, which is the number that gets ordered |

**A solid is not kit** — no checklist item, no cost, no steps, exactly like a
block. What it promises is its shape.

**One button, two halves.** There is a single action: **BUILD 3D**. It was briefly
two — build the geometry, interpret the sketch — and that was a choice nobody should
have to understand before they can press anything. What was **declared** (a traced,
fitted, stamped shape) goes straight into the scene; what was **drawn** (anchors,
loose strokes, the note) is **read** into a plan you accept. Room first, then the kit
that goes in it — which is also why the solids travel inside the interpret payload:
the agent places a projector against a stage that already exists.

The declared half is deliberately not propose-then-apply: a person traced a shape,
said in the same gesture what it was, and pressed build — the consent *is* the
gesture. It still goes through `agentApplyOp`, so one writer, one path. **LIVE**
ghosts the shapes as you edit them, and never over a plan under review. The agent's
instruction stays blunt: the pad holds the fit and the model does not.

### The Scene Study, in step — v5.5

Three things it needed once the pad could select and build:

- **SELECT is a mode indicator as much as a mode.** A click in that viewport can be a
  selection, the second half of placing a device, or a ruler point — and two of those lit
  a button while the third did not, so the state you were in was legible only by
  exception and *"why did my click not select that"* had no answer on screen.
- **The view presets are exact and they say which one you are in.** ISO · FRONT · SIDE ·
  TOP, framing the room, with the pressed one lit; FOCUS is gone (the F key still frames
  the selection). TOP is a true plan, axis-aligned, because the Sketch Pad draws its plan
  axis-aligned and the two surfaces have to agree about what looking down means. A preset
  is a place you are standing, not a mode you are in: drag the orbit and the lamp goes
  out, which is all "back to free rotate" needs to mean.
- **CLEAR empties the scene, and asks twice in the button.** No undo crosses the bridge,
  so one click that empties somebody's scene is a trap rather than a button — and a modal
  in a panel this size is worse than the two-step. Devices go out through `removeObject`
  one at a time, so the checklist, the wiring model and the cost panel unwind exactly as
  they would by hand.

One pre-existing bug fell out of it: **every overlay is a child of the viewport**, so a
click on the view cube bubbled down, started an orbit of zero pixels and ended as a click
that selected nothing — pressing TOP silently cleared your selection. Only the canvas
orbits and selects now.

**Editing.** A fit is a proposal about what was drawn, so it is arguable: vertices
drag, arc apexes bend, SIMPLIFY re-reads the ink at a different tolerance, and
SNAP / SYMMETRY / CLOSED are per-solid rather than global — two stages in one
drawing may be simplified differently. One interaction rule fell out of it: **a tool
whose job is "put this HERE" — stamp, text, origin, scale, erase — is never
intercepted by a selection's handles**, because the place you most want to stamp is
the middle of the shape you just traced, which is exactly where its handles are.

## Reading a reference — v5.5

The board could always collect images and label them; what it could not do was get
anything out of them. Now a **plan** or an **elevation** dropped on it becomes real
geometry, through `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` over a deterministic
tracer. Contract: `VISION.md`.

**The split is the same one as everywhere else.** A vision model is good at judgement
over a picture and hopeless at measurement — ask any model for `verts: [[-60,-40], …]`
and it returns a plausible list that is not the shape in the picture, and nothing
downstream can tell an invented coordinate from a measured one. So the geometry is
traced (threshold → close the gaps → find the enclosed regions → follow each boundary →
fit to vertices and true arcs) and the model is asked only what each traced region IS.

**And what it decides was measured rather than assumed.** Asked to name three plainly
different traced regions, SmolVLM2-500M answered `stage · stage · stage` to a six-way
list and `seating · seating · seating` to a binary one — constant across the inputs,
tracking the last option offered. It also called a plan a front elevation and counted
three shapes as two. But *"strip or block"* it got 3 of 3 right. So the model is
**calibrated on every drawing** against ground truth the tracer already knows, the
**geometry decides the role**, and the model's disagreement is kept and surfaced as a
risk with one click to accept it. `VISION_TRUST_ROLES=1` lets a calibrated model
overrule the layout; it ships off because it was measured off, and `VISION_MODEL` swaps
the checkpoint with no other change.

**It never invents a scale.** A photograph carries none, so a reference is `fitted` to
the venue's own width or explicitly `guessed` — and guessed ops arrive unticked, which
is already the rule for a guess.

## The reference board — `refboard.html`

Drag-and-drop, paste, or file-pick. Tiles, each carrying:

- thumbnail, filename, size
- a **role** chip — PLAN · ELEVATION · PHOTO · TECH DRAWING · MOOD
- a one-line note (*"the wall is 15 m, from the tech pack"*)
- an **include** toggle, and drag-to-reorder — the board's order is the order
  the images reach the model, and order matters

Same declaration discipline as the sketch pad: **every reference states what
kind of image it is.** A tech drawing read as a mood board is the failure mode,
and one chip prevents it.

**Bytes are downscaled in the panel and not retained anywhere.** The board holds
them until you hit Interpret; the host base64s them straight into the request and
keeps nothing. That is deliberately *less* than the `.glb` treatment — a venue
mesh has to reach every panel of the take, a reference only has to reach the
model once. If a second panel ever needs them, `REF_ASSETS` becomes the same
plain `Map` keyed by take that `GLB_ASSETS` already is — kept off the take,
which is deep-watched. Cap: 5 included images, long edge 1568 px.

---

## Intents — the panel config, keyed to the task

`ROLES` out, `INTENTS` in. Same two tests as the role lens (**ownership** →
**relevance**), same lead / working-column / context-column algorithm, new
vocabulary. An intent is *what is being done right now*.

| key | label | reads as | cluster (lead first) |
|---|---|---|---|
| `block` | BLOCK THE SPACE | venue, deck, sightlines, where the audience is | sketch · stage · devices · measure |
| `rig` | RIG PROJECTION | projectors, positions, lenses, coverage | stage · projlib · measure · checklist |
| `frame` | FRAME THE CAMERAS | camera placement, lensing, what it sees | preview · camlib · stage · devices |
| `wall` | BUILD THE WALL | LED geometry, pitch, processors | stage · devices · measure · refs |
| `patch` | PATCH THE SIGNAL | runs, machines, genlock, power | wiring · devices · measure |
| `cue` | CUE THE PLAYBACK | tracks, media, timing, routes | sequence · stage · preview |
| `price` | PRICE THE OPTION | what it costs, against the other takes | cost · compare · takes · deadline |
| `pack` | PACK THE TRUCK | cases, weights, dock windows | transport · devices · deadline |
| `explain` | EXPLAIN THE PLAN | showing it to someone not building it | compare · stage · cost · guide |

`explain` is where the old CLIENT role went, and `price` is most of PRODUCER.
That is the argument for the change, stated as a table.

```js
INTENTS.rig = {
  key: 'rig', label: 'RIG PROJECTION', icon: 'present_to_all',
  why: 'Getting light on the surface: what the projectors are, where they hang, what they cover.',
  implies: ['projectors'],                        // the relevance test
  panels: ['stage', 'projlib', 'measure', 'checklist'],
}
```

Three ways an intent is chosen, in ascending authority:

1. **Inferred** — `inferIntent(take)`, a heuristic over the take: which panel is
   focused, which checklist step is in progress, what just changed. No agent
   required, so the host still demos on its own.
2. **Proposed** — the agent classifies and says why. It arrives as a chip, not a
   rearrangement: *"Looks like RIG PROJECTION — switch?"* **Nothing autonomous
   moves panels under someone's hands.** Accepting a plan *is* consent, so a
   plan accept may switch intent directly; a bare classification may not.
3. **Chosen** — the intent switcher in the top bar, replacing the role switcher.

### The agent's override, and its limits

The agent may adjust the authored cluster and must say so:

```json
{ "intent": "rig", "confidence": 0.82,
  "why": "five projector stamps around a thrust, and a 10 m scale bar",
  "add": ["measure"], "drop": ["checklist"],
  "reason": "the sketch declares scale, so throw distances are the live question" }
```

Host-side validation, non-negotiable: at most **2** adds and **2** drops, only
keys that exist in `registry`, never dropping a `req: 'core'` panel, never
dropping the lead. The chip reads `RIG PROJECTION · + Measurements (agent)`, and
rejecting the override is one click and remembered per intent — so the agent
trains down instead of nagging.

### Storage

Layout keys move from `takeId|role` to `takeId|intent`, and the localStorage
prefix from `pctf.layout.` to **`pctf5.layout.`** — v5 is a new file, so it gets
a new namespace rather than inheriting arrangements saved against clusters that
no longer exist. The preset-hash guard stays: if an intent's authored cluster
changes, the saved arrangement is dropped and the toast names the intent.

---

## Units and frames — the one conversion rule

The take counts positions in **decimetres** (1 unit = 10 cm). The Scene Study
works in metres and converts at its boundary. **The agent API does the same and
writes take units only** — it is told `unitsPerMetre` and it converts once, in
one function, at the edge. No metre ever reaches a mutator.

Sketch pixels become take units through the declared scale:

```
metres      = (pixels − origin) / scale.pxPerMetre
take units  = metres × unitsPerMetre
```

Frames, pinned against the venue builders (authored in metres) and the v3 seed
positions:

| | |
|---|---|
| `+x` | stage right → left, as drawn |
| `+y` | up. Flown kit is positive (the projector ring sits at y 96 = 9.6 m) |
| `+z` | **downstage / toward the audience.** The upstage LED wall is at `−z`; the thrust and seating are at `+z` |

So in a PLAN sketch with the stage at the top: `x = (px − ox)`, `z = (py − oy)`,
no negation — which is exactly why the panel prints **↑ upstage** on the canvas.
In an ELEVATION sketch: `x = (px − ox)`, `y = −(py − groundLine)`.

If a sketch declares no scale, the agent gets the venue's own dimensions and
fits the drawing to them — and every position it proposes is marked
`confidence: "fitted"` so the plan panel can say so. It never prints a plausible
default, same rule the Measurements panel already lives by.

---

## The agent

`claude-opus-5`, adaptive thinking with `display: "summarized"` (the summary is
a design asset here — the panel shows the working), streaming, effort `xhigh`
for an interpret and `medium` for a refine turn, and a task budget so a runaway
interpretation paces itself instead of being cut off. Server-side refusal
fallbacks on by default. Tool surface, staging semantics, and the wire format
are all in **AGENT-BRIDGE.md**.

The shape that matters: **the write tools stage, the read tools are live.** The
agent can add six projectors, then ask what they cover, and get a real answer —
because the host ghosts the staged ops into the Scene Study, which measures them
with the geometry it already has (section 7 of the tool does this today for real
devices) and posts the figures back. That round-trip is the most expensive piece
of v5 and it is deliberately the last phase.

### Accepting a plan

Two ways, and the panel offers both:

- **Into this take** — the default. Ops run through the existing mutators, one
  undo step per op, the checklist and the cost panel react as they always do.
- **As a fork** — for a whole scene read off a reference image. The plan lands as
  a new take: an OPTION, inheriting decisions and no progress. The model already
  has the word for "a second opinion about how this should be done", and a
  sketch is exactly that.

---

## Phases

Each one ends demoable. Nothing in phase *n* is blocked on phase *n+1*.

| # | what | state |
|---|---|---|
| **0** | v5 folder, docs, launch entry. `AGENT-BRIDGE.md` written first. | ✅ |
| **1** | API on :3902 — `/health`, `/v1/interpret` (SSE), `/v1/answer`, `/v1/refine`, `/v1/accepted`, `/v1/plan/{id}`, and a **stub interpreter**: deterministic, no model call, and reaching every state the plan panel has to render. | ✅ verified end to end |
| **2** | `sketchpad.html` + `refboard.html`, standalone-bootable, plus the host-side iframe hosts. | ✅ verified |
| **3** | `ed-agent` plan panel: narration, reasoning, per-op tick, accept-into-take, accept-as-fork, revise. Ghosts + the measure round-trip in the tool. | ✅ verified — including the round-trip, which was meant to be phase 6 |
| **4** | AID3N: 16 tools, vision, streamed narration and reasoning, prompt caching, task budget, refusal fallbacks. | the `claude` engine is **written, not run** — no credential here. The **`external` engine is running and verified**: Claude Code reads the sketch out of `agent/inbox/` and drives the same plan over HTTP |
| **5** | `INTENTS` replace `ROLES`: 9 authored tasks, `presetForIntent`, `inferIntent`, the switcher, the agent's override chip and its validation. | ✅ verified |
| **6** | What is left: `route` ops applied through the wiring model, a `venue` op previewed in 3D, and refine turns against the real agent. | open |
| **7a** | AID3N named, three engines (`claude` · `external` · `mock`), the external channel, the `audience` op and the silhouette crowd, LED walls sized from the drawing, `aim` in degrees. | ✅ verified end to end, driven by Claude Code |
| **7** | The landing: renamed to **production hub**, the entry model parked behind `START PRODUCTION →`, and the sketch stage as the front door. | ✅ verified end to end |
| **9 · v5.5** | **VISION.** `vision.py`: the tracer (local-threshold ink, gap closing, enclosed-region labelling, Moore boundary following), the Python mirror of the pad's fit, SmolVLM2 over `transformers`, and the calibrate-then-arbitrate policy. `read_reference` on the model engine, the traced path on the mock engine, `vision` on `/health`, a VISION chip on the board. | ✅ verified end to end: a PNG dropped on the board became a curved thrust, a tiled LED wall and a crowd in the Scene Study |
| **8 · v5.5** | **SOLIDS.** The fitter in the pad (resample → RDP → circle fit → regularise → symmetrise), three builders in the tool (extruded deck · swept curved wall · faceted LED cabinets), `take.solids` and the `solid` op in the host, the `solids` message and its two lanes, `builtGeometry` in the Measurements panel, `add_solid` on the agent and the solids pass-through in the mock interpreter. | ✅ verified end to end |

**Verified for v5.5, in the browser:** a noisy 300-point semicircle fits to 3
vertices and 2 arcs of exactly the drawn radius at 0.7 px RMS; a hand-drawn
rectangle comes back as 4 vertices, no arcs, symmetric; a circular-fronted thrust
comes back as 4 vertices and one arc of exactly the drawn radius, symmetrised. In
the hub: trace → LIVE ghosts appear violet in the Scene Study → BUILD 3D turns
them real through the same mutators → the Measurements panel prints
*"1 DECK 270.9 M² · 1 WALL 249.4 M² · 297 TILES IN 3 PANELS"*. A projector aimed
at a fitted `wall` reports *"throw 18.28 m → CYC"* and its video wraps the curve,
with the lit footprint clipped against the real ribbon at 513.5 M². And
INTERPRET → plan row (*"solid · stage · 4 verts · 2 arcs · h 1.00 m"*) → accept
puts the same geometry in the take.

**Verified in the browser, not asserted:** the stub plan streams into the panel op
by op; ghosts appear in the Scene Study as they stream; `measure_preview` comes
back with real geometry (*"8 of 8 derived · 10,673–18,869 MM"* for five real
projectors plus three ghosted ones); accepting adds the devices through
`addDevice`, so the checklist grows from 78 tasks to 96 and the cost panel moves;
accepting as a fork lands the plan as an OPTION with its parent's decisions;
`take.derived` returns to the truth the moment the ghosts clear.

### Debt, named

- **Three icons are borrowed.** `sketch`, `refs` and `agent` want `draw`,
  `photo_library` and `auto_awesome` pulled from the Figma file's own icon page
  like the other 43. Nothing was redrawn — they borrow `edit`, `dashboard` and
  `priority` until the Figma plugin is authorised again. Greppable: `ICON DEBT`.
- **`route` ops are refused, not silently dropped.** The wiring model has its own
  setter and the plan says a route could not be applied rather than applying half
  of one.
- **The venue is not ghosted**, so a plan that changes the room says so in words.
- **v5.5 · an LED wall drawn in FRONT view is read as its bounding rectangle.** An
  LED wall is a rectangle of cabinets; a shaped one is a different order of problem
  and the panel says the rectangle it used rather than pretending.
- **v5.5 · a solid is not selectable in the tool.** It can be clicked *through* to
  place kit on, and it is measured, but it has no gizmo — editing a shape happens in
  the pad, which is the only thing that holds the fit.
- **v5.5 · `add_solid` on the real `claude` engine is written, not run** — same
  credential gap as phase 4. The mock interpreter's pass-through is verified.

---

## What will bite

- **Unlabelled sketches give room-level accuracy, not rig-level.** This is a
  property of the input, not a bug to fix. The stamps, the scale bar and the
  projection toggle exist because of it; the plan being reviewable is the rest of
  the answer. Do not demo a napkin photo and call it placement.
- **Latency.** A full interpret with a tool loop at `xhigh` is tens of seconds.
  Without streamed narration it reads as broken, so the stream is load-bearing,
  not decoration.
- **The ghost round-trip is the hard part.** Staged ops → ghosts → measure →
  back is three hops through two boundaries. Phase 6, and honest absence
  (*"— waiting on the Scene Study"*) whenever it times out.
- **Payload weight.** PNG + vectors on every stroke would be absurd; the panel
  posts only on Interpret. Reference bytes are downscaled before they leave the
  panel, not after.
- **Roles → intents is a breaking change to saved layouts.** Handled by the new
  `pctf5.` prefix rather than a migration nobody will trust.
- **`file://` and the API.** An agent panel opened by double-click cannot reach
  :3902 cleanly. The panels degrade to a named *"the agent needs the local
  server"* state, the same way the Scene Study panel already names its lost
  state — and v5 is served over :3900 in every demo.

---

## Conventions carried forward

- Nothing is transcribed. The tool is *sent* the resolved BrandOS tokens; so are
  the new panels, over the same `hello`.
- Every panel boots standalone against a mock, or the split is a slogan.
- Adding a message type or a field to a protocol is backwards-compatible and
  needs no version bump; changing the meaning or the units of an existing field
  bumps it on both sides. The scene bridge stays at **v1** for v5's additions.
- A derived figure is never typeable, and never defaulted.
