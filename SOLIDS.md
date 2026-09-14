# Solids — the geometry contract, v5.5

How a drawn curve becomes a thing in the room. This is the third contract in the
set, and it is written the same way as the other two: before the code, and if the
halves ever disagree, this file is the thing to fix first.

| | |
|---|---|
| **Fitter** | `sketchpad.html` — sections *2b · THE SOLID FITTER*, *2c*, *2d*, *3b*, *5b*, *6b*, *8b* |
| **Host** | `production-hub-v5.5.html` — `take.solids`, `sanitiseSolid`, the `solid` op, `panelSolids` |
| **Tool** | `scene-study-3d.html` — section *4d · SOLIDS* |
| **Agent** | `agent/model.py` (`Solid`), `agent/stub.py` (`_solids`), `agent/agent.py` (`add_solid`) |
| **Version** | additive on both protocols: `AGENT_V` and `BRIDGE_V` both stay **1** |

---

## The problem

v5 could receive a rectangle. `block` ops carry `w`, `d`, `h`, and the Scene Study
builds a box — which is right for a riser and wrong for the thing people actually
draw first, which is a curve.

The wrong fix is to fit a bounding box, because the whole reason somebody drew a
curve is that the thing is curved. The other wrong fix is to ship the ink: three
hundred jittery points is not a stage. It cannot be built, it cannot be priced,
and nobody can read a dimension off it.

So v5.5 does what a draughtsman does. It reads the drawing, decides which parts
of it are **arcs** and which are **straights**, and re-states the whole thing as
the small number of vertices and true circular arcs the hand was aiming at.

---

## The fitter, in five steps

Each step is a **correction**, so each one is reported. A correction nobody can
see is a different drawing, not a correction.

| | step | what it does |
|---|---|---|
| 1 | **resample** | uniform arc length, so a tolerance means the same thing where the hand moved fast as where it moved slowly |
| 2 | **simplify** | Ramer–Douglas–Peucker at a declared tolerance. The noise goes. A closed loop is cut at its far point first — run plain RDP on a chain whose ends are the same point and the base segment has zero length, so every perpendicular distance is zero and a rectangle reduces to a dot |
| 3 | **arc fit** | runs of points that are genuinely circular become **one arc**, by algebraic (Kåsa) circle fit, accepted on four tests together: deviation inside tolerance, a **monotonic** turn, at least ~17° of sweep, and a **sagitta bigger than the noise we just threw away**. That last one is the load-bearing test — a jittery straight line fits a circle of enormous radius perfectly well, and without it a hand-drawn stage edge comes back as three gentle arcs of 300 m radius. Technically a good fit, and a lie about the drawing |
| 4 | **regularise** | vertices to a 25 cm grid; segments within 5° of axial made *exactly* axial by moving both ends to the average, which keeps a closed loop closed where rotating the segment would open it; arc radii rounded to 25 cm, with the endpoints kept and the bulge recomputed |
| 5 | **symmetrise** | closed shapes only, about the vertical axis through the centroid. The match is found by reversing the loop and rotating it — n² on twenty vertices, which is nothing — and applied only if the whole loop agrees inside 2.5× tolerance. A shape that is not symmetric is left exactly as drawn and says so |

Reported on the canvas, in the payload and in the plan row: raw points in,
vertices out, arc count, each arc's radius, the RMS the fit gave away, whether
symmetry fired, and whether a vertex was moved by hand afterwards.

### Symmetry has one trap worth writing down

Mirroring flips a bulge's sign and traversing the partner segment backwards flips
it again, so two mirror-paired bulges have the **same** sign and average
additively. Getting that wrong cancels every arc that crosses the axis — which is
exactly the one a curved thrust is made of, so the failure looks like "symmetry
deleted my curve". A segment that is its own partner (the front of a thrust) then
averages with itself and is left alone, which is the right answer for free.

---

## Curves on the wire are bulges

A **bulge** is the CAD convention: the signed sagitta over the half-chord, which
is `tan(θ/4)` for an included angle θ.

```
bulge  0   a straight
      ±1   a semicircle
      sign says which way it bows: positive toward (−dy, dx) of the chord
```

One number per segment carries a true arc, survives uniform scaling, and is
reconstructible exactly at whatever resolution the reader wants. The Sketch Pad
walks it to a quarter of a pixel; the Scene Study walks it to two centimetres.
**There is one geometry, sampled twice, and neither is the other's
approximation.**

Reconstruction, for anything else that ever has to read one:

```
c   = |P₁ − P₀|          chord
d   = c / 2              half-chord
sag = bulge · d          signed sagitta
r   = |(d² + sag²) / (2·sag)|
n   = (−Δy, Δx) / c      the chord's unit normal
centre = midpoint + n · (sag − sign(sag)·r)
θ      = 4·atan(bulge)   signed sweep; walk from angle(P₀ − centre) by −θ
```

The arc walk is deliberately duplicated in the pad (pixels) and the tool
(metres) rather than shared. Both files boot on their own, and a pure function of
five numbers is the cheapest thing in this system to keep honest — the
alternative is a module neither file can run without.

---

## A trace is a filled solid until something says otherwise

**Every traced outline is closed, faced and extruded.** The default is `stage`, half
a metre thick — a deck, a riser, a rostrum — because that is what a shape drawn on a
plan almost always is, and because a ring of ribbon with nothing inside it is not a
thing anybody can stand on.

A hand rarely closes a loop exactly, so closure is **forced** rather than detected.
What the drawing actually said is remembered as `drawnClosed`, and it is the right
answer the moment the shape is named WALL or LED: those are runs, and a run is open.
A loop the hand really did close stays closed even then — somebody drew a ring and
meant it.

## Naming a shape is a stamp, not a mode

The role is **not armed before the trace.** It is declared afterwards, by dropping a
stamp on the shape:

| stamp | on empty canvas | on a traced shape |
|---|---|---|
| `LED` | an LED wall's position | **that shape is an LED wall** |
| `WALL` · `SCREEN` | a surface's position | **that shape is a surface to project on** |
| `STAGE` | the deck's position | **that shape is a deck** (the default, restated) |
| `PROJ` · `CAM` · `TRACK` | a device's position | *still a position* — a projector standing on a deck is a projector standing on a deck |

This is the rule the interpreter already used — *"dropping LED on a rectangle says
that rectangle IS the wall"* — extended to real geometry. Which way a stamp goes is
decided by **where it landed**, not by a mode, so there is still one palette.

Two things that had to be true for it to work:

- **A stamp aims at a place, so it beats a selection's own handles.** The place you
  most want to stamp is the middle of the shape you just traced, which is exactly
  where its vertex handles are. Letting the handles win meant dropping LED on a fresh
  wall silently dragged a vertex instead, and the shape stayed a deck with nothing to
  explain it. Every tool whose job is *"put this HERE"* — stamp, text, origin, scale,
  erase — is exempt from handle interception.
- **A naming stamp hit-tests generously, and ignores closure.** Selecting a shape is
  a precise act; pointing at one is not. Once a stamp opened a shape into a run its
  inside stopped being clickable, so you could name it LED and never get at it again
  to say it was really a wall.

A naming stamp only re-reads the ink if the **closure** actually changed — a refit
throws away hand-moved vertices, and naming a shape is not a reason to lose them.

## Three roles, because three things behave differently

A role is **not a colour and not a style**. It decides what gets built, and each
one exists because pretending otherwise is how a study starts lying.

### `stage`

The outline is a **footprint** — a closed face — extruded to `h`, which defaults to
**0.5 m**. Curves kept, corrected, simplified. On the front plane it is a silhouette
extruded through depth instead.

Reported: enclosed area by shoelace **over the tessellation**, so an arc
contributes the area an arc actually has rather than the area of its chord.

### `wall`

The outline is a **surface**, swept into a ribbon with real normals. This is the
one the projection pipeline cares about: § 8b's projective texturing wraps the
image round the curve, and § 8c's Sutherland–Hodgman clipping reports the polygon
the light actually lands on. A flat stand-in would have made the throw distance,
the image size and the lit footprint all wrong in the same direction.

A closed outline drawn in the **front** plane is a shaped flat panel — a cut-out
screen, where the shape is the point of it.

### `led`

**LED does not bend.** The outline is faceted into flat panels, each a whole
number of cabinets wide, and the cabinets are drawn as cabinets.

The facet count comes from the curve itself: a flat chord may sit no more than
**half a cabinet** inside the arc that was drawn. That is the physical truth of
the thing, and once it is drawn that way the question *"does this curve cost me
three extra cabinets"* answers itself. A 15 m curved wall is 31 cabinets across
in three flat panels.

Reported: `cols × rows`, total tiles, panel count, and the width and height the
whole tiles actually add up to — because a wall is not 15 m wide, it is 30
cabinets wide, and the difference is whether it can be built.

A shape drawn in the **front** plane is read as the rectangle that contains it.
An LED wall is a rectangle of cabinets, and a shaped one is a different order of
magnitude of problem than this panel should pretend to have solved.

#### v5.9.1 · who authors `tile`

`tile` used to have one author. The Sketch Pad carried a TILE field, wrote it into
the payload, and everything downstream read it — which quietly encoded the idea
that a cabinet size is a drawing property, like a tolerance.

It is not. It is a **product**, and the product decides four things the drawing
cannot: the pitch, the pixels, the mass and the draw. So from v5.9.1 the HUB's
**LED tiles** panel is a second author of this one field: choosing a tile writes
`tile: { w, h }` in take units — millimetres over 100 — onto the solid, and the
pad and the room both re-grid on the next push, exactly as if it had been typed
on the paper.

Three rules keep that from becoming an argument between two authors:

| | |
|---|---|
| **the field is the whole contract** | the HUB writes `tile` and nothing else. Which *product* a wall is made of lives beside the take, keyed by solid — the same way the room's geometry does — so nothing new travels on the wire and `sanitiseSolid` is untouched |
| **the count is never the HUB's** | resolution, mass, draw and price are the tile's spec times a COUNT, and the count is `derived.builtGeometry` — the room's own grid on the real outline. Where the room has not been opened the HUB estimates from the outline and marks the figure `EST` everywhere it surfaces |
| **the pad still wins on the paper** | typing in the pad's TILE field overwrites both dimensions, because that field is square by design. A non-square cabinet (600 × 337.5) round-trips intact through `tile.w` / `tile.h` and is used as such by both grids; it is only the pad's *input* that cannot express one |

#### v5.8 · upright or lying flat — `lay`

An LED used to be **upright, always**. A floor-plane outline was read as a FOOTPRINT and
the cabinets stood up out of it, which is right for a wall and wrong for every horizontal
screen there is — a stage-floor LED, a runway, the top of a plinth. The only way to get one
was to name it a `stage`, and a deck has no pitch, no cabinet count, no route and no crop:
precisely the things you point at a screen to ask about.

`lay: 'flat'` says **the outline IS the emitting face**, lying at `h` rather than rising to
it. It is the same construction a `front`-plane LED already used — the fitted outline with
the cabinet grid clipped to it — turned into the room's horizontal plane instead of standing
in its vertical one. Absent (or `null`) means upright, so the old reading is the one you get
by saying nothing.

**The face assigned is always the one pointing UP.** A picked patch takes its normal from
the seed triangle's winding, and in exported geometry that is arbitrary — which is exactly
why the flood fill joins triangles on `Math.abs(dot)` rather than the signed one. Measured on
`concert_stage.glb`: 56 of its 119 distinct horizontal patches came back pointing DOWN,
including an 8.5 m platform at 5 cm that anybody would call a floor. So a horizontal patch is
now always DESCRIBED facing up. Only the horizontal ones: a standing face's normal is a real
fact about which way the screen looks, and it travels to the paper to draw the facing tick.

A flat LED also lies on the **top** of what it is on (`maxY`, not the centroid — a thin plate's
top and underside merge into one patch, whose middle is inside the plate), and its `h` is an
ELEVATION rather than an extrude, so it is not clamped to a whole take unit the way a deck's is.
Floor level is a valid answer for a screen.

**And it can be DRAWN, not only picked off a model.** `LED FLOOR` is a fourth stamp in the
pad's role menu, offered on any closed plan outline — a rectangle somebody has just drawn is
the commonest case there is. It is a variant rather than a role: the `role` stays `led` and
`lay` carries the orientation, so the three-role set the take knows is unchanged. Three things
follow, and each is a place the upright reading is wrong:

| | upright LED | LED FLOOR |
|---|---|---|
| closure | a run, so it **opens** unless the hand closed it | an area, so it **stays closed** |
| `h` | how far the cabinets are extruded | the **elevation** the screen lies at |
| the grid | `ledFacets` along the run, `rows` from `h` | the outline's own bbox, clipped to its shape |

The pad draws a floor's seams the way it already draws an elevation-drawn face's — the outline
IS the emitting surface in both — and on the front page it is a plate at its elevation rather
than a band rising from the deck.

Both are offered wherever a face is named, and the sensible one leads: a **horizontal** face
gets `LED FLOOR` first and `LED WALL` second (cabinets standing round its edge — a fascia,
which is real and rarer). A **standing** face is offered only the wall, because laying its
footprint flat is a screen with no width.

Two things a flat LED is deliberately kept out of. It takes no part in a **canvas** —
`ledCanvas` lays one picture across a horizontal axis with height as the other dimension, and
a floor has no height to give it, so `linkLeds` drops it by name and says so. And `ledRect`
asks the surface which way it faces: one looking UP reports the **depth** it covers as its
second dimension, because `size.y` on a horizontal screen is zero and every figure
downstream — the clip's aspect, the FILL crop, the canvas share — divides by it.

**A solid is not kit.** No checklist item, no cost, no steps — the same rule as a
`block`, for the same reason. What it promises is its shape, and its shape is what
every geometric figure downstream is measured against.

---

## Units, and the one place the pad converts

Everywhere else, the Sketch Pad **declares and converts nothing**: pixels and the
scale travel, and the far side does the arithmetic once, in one place. A panel
that converted would be a second opinion about where things are.

A solid is the deliberate exception. The pad holds the **fit** — it decided which
runs of ink were arcs, which vertices survived and what radius each arc was
rounded to. It is therefore not a second opinion about that geometry, it is the
**only** one, and handing the far side pixels and asking it to re-derive the fit
would be the second opinion.

So a solid crosses every wire in **take units** (1 unit = 10 cm) and carries
`units: "take"` on itself so that can never be read the other way.

### The axes change here too

The pad draws **Z-up** — X across the page, Y into the room in a top view, Z up
the page in a front view. The take counts `[across, UP, DEPTH]`. So:

| drawn in | plane | page-y means | verts are | bulges |
|---|---|---|---|---|
| TOP | `floor` | depth | `(across, depth)` | unchanged |
| FRONT | `front` | height, and it runs the *other way* | `(across, up)` | **negated** — the plane is mirrored, and a mirrored arc curves the other way |

`h` is the extrude height on the floor plane and the depth on the front plane.
`base` is how far off the deck the thing starts, so a flown wall is expressible.

---

## The schema

```js
{
  id: 'sk1',
  units: 'take',                       // never absent, never anything else
  role: 'stage' | 'wall' | 'led',
  name: 'THRUST' | null,
  plane: 'floor' | 'front',
  view: 'plan' | 'elevation',          // which page drew it
  closed: true,
  at: [x, up, depth],                  // TAKE UNITS — the outline's own anchor
  verts: [[a, b], …],                  // TAKE UNITS, LOCAL to `at`
  bulges: [0, 0, -1, 0],               // one per segment; closed → verts.length
  h: 10, base: 0, thick: 10,           // TAKE UNITS
  tile: { w: 5, h: 5 } | null,         // led only — the cabinet, mm/100. Authored by the pad OR the HUB's LED tiles panel
  lay: 'flat' | null,                  // led only — the outline IS the face, lying at `h`
  fit: {
    raw: 214, verts: 4, arcs: 1,       // what the correction cost
    rms: 0.07,                         // METRES
    tol: 0.15, symmetric: true, snapped: true, handEdited: false,
    radii: [6.0],                      // METRES, in segment order
  },
  metrics: { area: 76.5, perimeter: 39.2 },     // or { length } · or the LED grid
}
```

`bulges` has one entry per **segment**: `verts.length` when closed,
`verts.length − 1` when open. Anything shorter is zero-filled and anything past
±4 is flattened — a bulge that big is a fit that went wrong, and a straight is the
honest recovery.

**Two vertices can enclose an area.** Straight segments need three, but two arcs
between two points is a lens — and a hand-drawn ellipse fits to exactly that, two
vertices and two arcs. A `closed` guard of `verts.length >= 3` therefore quietly
reopens every such shape: a closed shaped screen comes back as an open run swept
through its own depth, four times the area and the wrong object. The guard is
`>= 3`, **or** two vertices with any curvature.

---

## Additions to the two protocols

Both are backwards-compatible, so **neither version number moves**. The other
side ignores what it does not know, per each document's own rule.

### Sketch Pad → host — `AGENT-BRIDGE.md § Part 1`

| type | payload | meaning |
|---|---|---|
| `solids` | `solids[]`, `apply` \| `preview`, `clear?` | build them, or ghost them. Not an interpret: no plan, no stream, no model |

`interpret` gains `solids[]` — the same objects, in the same units, alongside the
pixel record everything else in that payload is in.

### Host → tool — `SCENE-STUDY-BRIDGE.md § Host → tool`

`scene` gains `solids[]`. `ghostClear` gains an optional `planId`: two things
ghost now, and clearing one must not clear the other.

### Tool → host

`measure.derived` gains **`builtGeometry`** — `{ text, rows[] }`, one row per
solid with its own metrics. Derived like everything else in § 7, and therefore
never typeable.

### The op

`solid`, applied by the host into `take.solids` through `sanitiseSolid`. The
bridge adds no mutation path of its own — same sentence as the other two
documents, and for the same reason.

### The agent's tool surface

`add_solid` stages one. The system prompt's instruction is blunt about the
division of labour: **the pad holds the fit and the model does not.** Pass a
fitted solid through unchanged, author one only for geometry nobody traced, and
never propose a `wall` where somebody meant LED in order to get a smooth curve —
that is a wall nobody can build.

---

## One selection, two surfaces

A shape exists in both places, so selecting it should mean the same thing in both. It
does: click it in the Scene Study and its row opens in the Sketch Pad; select it in the
pad and its edges light up in the 3D.

The two surfaces call it different things. The Scene Study knows it by the take's own
`solid.id`; the pad knows it by the id of the **trace** it came from. Neither can name
the other's, so the host is the one place holding both, and `t.focus.solid` is where the
answer lives — a slot of its own rather than `focus.obj`, which is for kit and has a
checklist behind it that half the panels look up.

The echo is suppressed the way the scene bridge already suppresses a drag echo: the
surface that set the selection is not told about it again.

**Anchors are the honest gap.** A stamp becomes a device only when a plan is accepted,
and nothing links the two afterwards — so selecting an anchor in the pad cannot select a
projector in the 3D, and it announces `null` rather than leaving a stale highlight
somewhere. Shapes are the things both surfaces genuinely hold.

## The shape comes to life while the hand is still moving

The ghost used to wait for the pen to come up — which meant the 3D said nothing during
the one moment somebody is actually looking for feedback. The partial path is now fitted
and ghosted like any other proposal; it just happens to be a proposal that is still being
drawn.

It is fitted by **the same fitter**, not a looser preview one: a preview fitted
differently from the thing it previews is a lie with a short lifespan. It is throttled —
a `pointermove` fires far faster than a fit is worth running, and the fit walks the whole
path each time — and it is never pushed into the drawing. On pointerup the committed shape
takes over from the draft.

## Resizing, and the one constraint that is geometry rather than taste

A selected shape carries four **transform corners** on its bounding box, dragged from a
corner and anchored on the opposite one. Free by default; SHIFT keeps the proportions.
They are drawn **hollow** and slightly larger than the vertex handles, because two kinds
of handle that look identical are one kind of handle you cannot aim at.

**A bulge describes a CIRCULAR arc, and a circle scaled differently in x and y is an
ellipse — which a bulge cannot express at all.** So a non-uniform drag on a shape with
arcs in it does not fudge the number: it rescales the **original ink** and re-runs the
fitter, which finds the arcs that actually fit the new outline. That is the same
correction the trace got in the first place, applied again, and it is the reason the raw
ink is kept on the item rather than thrown away after the first fit. Watch the footer
during such a drag and the vertex and arc counts change — that is the fit being honest,
not a bug.

The one case that cannot be done honestly is a **hand-edited** shape scaled
non-uniformly: re-fitting would discard the hand's own vertices, and keeping them would
keep arcs that are no longer arcs. That drag is constrained to uniform and the footer says
why — refusing quietly would look like a broken handle.

## The cursor says what a click will do

A crosshair on every tool claimed "you are about to draw", which is wrong under SELECT and
wrong over a handle — and a select tool that keeps a drawing cursor reads as one that is
not armed.

| over | cursor |
|---|---|
| empty canvas, SELECT armed | arrow |
| a shape, a stroke, an anchor | `move` |
| a vertex or an arc apex | `grab` |
| a transform corner | `nwse-resize` / `nesw-resize` |
| anything, with a drawing tool armed | crosshair |

## LIVE means two different things, and both are what you expect

`LIVE` is a live preview, and what a preview *is* depends on whether the shape has been
built yet:

| | |
|---|---|
| **not built yet** | ghost it — violet, in the Scene Study, touching nothing in the take |
| **already built** | **move it**, in the take, as the pointer moves |

Ghosting a shape that is already built would draw a violet copy floating beside the real
one that stayed put: two of the same thing, neither of them right. It also parks the tool
in preview mode, and while a proposal is up the tool measures into the *plan* rather than
into the take — so every derived figure in the workspace quietly stops updating. So a
built shape is applied, and only what is genuinely still a proposal is proposed.

The apply channel is throttled to ~110 ms during a drag, because a `pointermove` fires
far faster than anything needs to be mutated.

## One button, two halves

There is a single action in the pad: **BUILD 3D**. It was briefly two — *build the
geometry* and *interpret the sketch* — and that was a choice nobody should have to
understand before they can press anything. They are not alternatives; they are two
halves of turning a sketch into a scene, and the split between them is not
arbitrary:

- **What was DECLARED goes straight in.** A traced shape was drawn, fitted and
  stamped. Sending it to a model to be told what it already says would be theatre.
- **What was DRAWN is READ.** Anchors, loose strokes and the free-text note do not
  say what they are, so that half is a plan you accept.

They run in that order, room before kit — which is also why the solids travel inside
the interpret payload: the agent places a projector against a stage that already
exists. Either half may be empty, and the button's tooltip says which halves are
about to happen, because *"why is this greyed out"* and *"what is this about to do"*
are the two questions one button has to answer without being pressed.

**LIVE** still previews as you edit — ghosting what is not built and moving what is,
per the section above — so the preview happens before either half.

## Two lanes, and the courtesy between them

The declared half is not propose-then-apply, and everything else in the agent
bridge is, because the agent read something and might be wrong. **A solid from the
Sketch Pad is not that:** a person traced a shape, said in the same gesture what it
was, and pressed BUILD 3D. The consent *is* the gesture, so there is nothing to
review, and putting a plan panel between somebody and their own drawing would be
worse than useless.

What does not change: it goes through `agentApplyOp`, so the take is mutated by
exactly the code an accepted plan mutates it with. One writer, one path.

Two courtesies, because the agent may be mid-plan:

- a live ghost from the pad **never** overwrites a plan under review — the plan
  wins and the pad's ghosts wait
- ghosts carry their own `planId` (`sketch-solids`), so clearing one lane cannot
  clear the other

---

## Running two versions at once

v5 and v5.5 both want `:3902`, and comparing them meant stopping one service to
look at the other. So the host accepts `?agent=3903`, or a whole origin:

```bash
AGENT_STUB=1 v5/agent/.venv/bin/python -m uvicorn serve:app \
  --host 127.0.0.1 --port 3903 --app-dir v5.5/agent --reload
```

Then open `production-hub-v5.5.html?agent=3903`. Absent the parameter nothing
changes.

---

## Changing this contract

Adding a role, a field or a metric is backwards-compatible and needs no bump.
Changing what `bulge` means, or the units, or which plane `h` grows along, raises
`AGENT_V` **and** `BRIDGE_V` — and every side then refuses to talk to an old
counterpart rather than half-work.
