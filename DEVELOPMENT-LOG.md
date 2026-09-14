# Production Hub v5.8 — Development Log

This is the durable, plain-language record of work on the local Production Hub prototype.

## 7 September 2026 (4) — The canvas the room forgot, and the tile that never reached the invoice

### What changed

- **Linked LED canvases survive a workspace switch and a second Scene Study.**
- **The playhead survives with them** — the position, not the running.
- **Choosing an LED tile moves the Cost panel.**

### Why

**"The video I loaded into the LEDs is gone."** The route was fine; the thing it named
was not. A LINKED CANVAS — several LED screens made one picture — is the single LED
fact that lives ONLY in the Scene Study: the id comes from a local counter
(`ledlink-1`), and the members are route ids that instance minted. Nothing about it is
a take fact.

That was survivable while a panel stayed open for a session. It stopped being
survivable the moment a task button became the normal way to move around: pressing
RIG & LOAD re-creates every area, the tool reloads, `ledLinks` comes back empty, three
linked walls are three walls again, and every clip routed at `ledlink-1` has a route
naming something that no longer exists. Dark LED, cue apparently lost.

**The host had been storing them since v5.8** — it forwards them to the Sketch Pad so
the paper can draw the ties — and simply never sent them back. It does now, on every
scene handshake, before the media, because a `clips` row routed at `ledlink-2` cannot
resolve until `ledlink-2` exists. Links also fan to the take's OTHER rooms: two Scene
Studies disagreeing about whether three walls are one canvas is two different shows.

**And the same trap was waiting on the way out.** `postLinks()` is called from
`routeMedia()`, which runs on boot — so a freshly created room would have published
"there are no canvases" straight over the store it was about to be restored from.
`linksSettled` is the guard: the tool says nothing about links until its own replay has
arrived, empty or not. That is the third place this rule has had to be written down —
after the sequence loss and the imported models — and it is always the same sentence:
**a panel must not be taken at its word about what it holds before it holds it.**

**The playhead came along for the ride.** A re-created room opened at 00:00 while the
show was parked at 00:12, so the wall showed whatever happens to sit under the top of
the timeline rather than the frame somebody was looking at. The transport is now stored
whole and replayed whole — except `playing`, which is forced false. The clock lives in
the Sequencing Timeline, and replaying `playing: true` into a room with no clock sets it
running free on its own frame loop, away from every other panel. A Timeline that IS open
and playing beats every 1.5 s and picks the room straight back up.

**The screens were the biggest number on the job and were not on the invoice.** `costOf`
prices OBJECTS — things the checklist counts — and an LED wall is not one: it is a shape
somebody drew, made of a tile somebody chose, and the count belongs to the room. So it
was worth nothing, on jobs where it is routinely worth more than every projector, camera
and server put together. It goes in with the kit rather than beside it, so the
contingency covers it too, and it is the one line whose unit is a tile.

### Verified, on one 11 × 6 m wall

| | ROE CARBON CB5 MKII · 5.77 mm | ROE RUBY RB1.5 · 1.5 mm |
|---|---|---|
| tiles | 22 × 12 = **264** | 18 × 18 = **324** |
| resolution | 1,892 × 1,032 | **7,200 × 4,050** |
| LED screens line | €182,160 | **€531,360** |
| take total | €288,230 | **€665,366** |

Swapping the cabinet on the same wall moves the job by €377,000 without anybody typing a
price — the shape decides how many, the tile decides what one costs. Rigging agrees:
324 × 7.9 kg + 5 × 72 kg = 2,919.6 kg, which is what that panel now reads.

Also verified: a clip routed at a drawn LED wall is still playing on it after a switch to
RIG & LOAD, a second Scene Study opened beside the first shows the same picture on the
same wall immediately, and the wire carries `ledLinks[1]` and `transport t=12.5
playing=false` on every scene handshake while a booting room publishes no `ledLinks` at
all.


## 7 September 2026 (3) — Two libraries fall in line, and a chart stops stretching its own type

### What changed

- **The camera and projector libraries add with a `+` icon button**, like everything else.
- **The burn-down chart is measured rather than stretched**: one SVG unit is one screen pixel,
  so the plot rescales and the type, the dash patterns and the hairlines do not.

### Why

**The libraries were the last two panels doing it their own way.** Everywhere else — the tile
catalogue, the Kanban, the Gantt, the survey, the snag list — adding something is a `+` icon
button. In these two the whole ROW was one big `<button>`, with the word "add" set in 8px under
the price, and the alternative action (hand the placement to the Scene Study) had to be a
`<span>` pretending to be a button, because a button cannot legally contain one.

So the row is a container and both actions are real buttons: `+` to add on the default ring,
the target to place where you click. The row still lifts its border on hover, because it holds
controls; it no longer shows a pointer, because it no longer promises anything itself.

**The chart was drawn the normal way for a responsive SVG and the wrong way for a chart.**
A fixed 320-unit viewBox stretched to `width: 100%` scales EVERY user unit with the panel — so
the 6.5px axis labels rendered at about 4px in a narrow column and 11px in a wide one, the
dashes on the ideal line became a different pattern at every width, and the hairlines went soft
because they no longer landed on pixels.

The fix is not to compensate with `vector-effect` or an inverse scale — it is to stop lying
about the coordinate system. The box reports its real width, the geometry is recomputed in those
units, and the SVG renders at exactly that size. Measured: at 442 px and at 238 px the plot
rescales and a caption is 11 px tall in both.

Two details that came with it. `shape-rendering: crispEdges` is scoped to the lattice, the axis
and the today line and nothing else — it snaps a horizontal hairline onto a pixel and turns a
diagonal into a staircase. And chart captions moved out of inline styles into a `.ch-t` class,
so the next chart inherits the rule rather than re-learning it.

The box is watched rather than measured once at mount: this panel can mount with no take open,
in which case there is nothing to measure yet and a one-shot reading would leave the chart on
its 320px default for the rest of the session.


## 7 September 2026 (2) — Fields that were white, buttons that burst, and the light on the wall

### What changed

- **`.inp` now exists.** Seven panels had been asking for it and there was no such rule.
- **`.rl-ic` is a row, not a box** — glyph, gap, word — so no button's label leaves its border.
- **LED tiles** lost the `+`; **LED tile** is two columns under a preview that shows what pitch
  actually means.
- **Deadlines** says its four figures as four figures, over a ruled lattice.
- **Kanban** cards can be selected, handed over by name, and removed.
- **Photometric analysis** — a new panel in the Projectors workspace.
- **An imported model survives a workspace switch.**
- **Media spec** names the sequence and the surface.

### Why

**The white fields were not a theming oversight, they were a missing component.**
`class="inp"` appeared in the Kanban, the Gantt, the survey, the snag list and the footprint
panel, and nothing in the stylesheet defined it — so every one of them rendered a browser
default: white ground, blue focus ring, a spinner on the numbers, in the middle of a dark
panel. It is now the same recessed field `.rl-sel` is, because they sit beside each other in
half these rows and were never meant to look like two different products.

**The bursting buttons had one cause too.** `.rl-ic` was `width: 26px` — a hard box sized for
one glyph — and about half of them now carry a word as well. One rule fixed every instance:
`min-width` instead of `width`, `inline-flex`, a gap, `nowrap`, and the glyph pinned in pixels
so it does not shrink with the label. Icon-only buttons are unchanged.

**The plus on the LED tiles panel was the idea the tile catalogue exists to kill.** It added an
LED *processor* specced with the tile, which is a different object, and read as "add this screen
to the scene". A wall is drawn; a processor is a checklist item.

**The tile preview now shows the only thing that matters about pitch.** Three numbers in headline
type down one column made a reference panel read like a landing page and pushed the
per-square-metre figures — the ones you actually decide on — below the fold. It is two columns
now, under a preview spanning both: the cabinet at its real proportion, and a DENSITY SWATCH —
the same fixed 36 mm of wall for every product, drawn as its real lattice of emitters. That is
the only honest way to show pitch, because a preview that scales with the product makes every
tile look equally dense. 1.5 mm fills that window with 576 dots and a 10 mm batten with 16.

**The burn-down was correct and read like a paragraph.** One long sentence carrying four separate
figures, so it had to be read rather than glanced at — the one thing a burn-down must not
require. The numbers are a strip of four cells now, and the chart got a faint lattice ruled in
the axes' own units, so a reader can take a figure OFF the graph instead of taking it on trust
from the caption.

**Removing a Kanban card is two different acts and the panel refuses to pretend otherwise.** A
loose card is yours and is deleted. A step card is part of the checklist across every object it
touches, and deleting it here would silently rewrite the plan — so it is SKIPPED: a state the
take has always had, honest about what somebody means ("this does not apply to this job"), out
of every percentage, listed at the foot of the board, and one click to take back. Verified: 50
tasks → 45 on a skip, back to 50 on the restore.

**Photometric analysis.** The one question about a projector this workspace could not ask — not
*does the beam reach*, which Alignment answers, but *how much light is on the surface*.

The division of labour is the one used everywhere the room is involved. The Scene Study publishes
`derived.photometry`: where each beam lands, solved as four boundary rays against the real
receiver set, grouped by surface with the identical test the overlap figure uses, each quad
flattened into that surface's own 2D frame. Not one lumen crosses. Flux is a catalogue fact, and
illuminance-or-luminance, the scale, the screen gain and what counts as enough are judgements
somebody makes while looking at the answer.

The model is printed on the panel rather than buried, because a false-colour map is the most
persuasive picture in this whole tool and the easiest one to lie with:

```
E = Φ · o / A        lux on the patch the beam actually lights
L = E · ρ / π        cd/m² a camera or an eye sees
```

`o` is an output factor — a rated machine in a real room with a real lens does not put its spec
sheet on the wall, 80% is the honest default and it is a control, not a constant. Obliquity needs
no term: a raked beam lights a bigger patch and A already knows. **Overlaps add, because light
adds** — the double-bright seam down a blend is what the room will really do until somebody
soft-edges it. Measured against SMPTE 196M's 48 cd/m² cinema white, which is a number the panel
can be wrong about.

Two things it found immediately. The seed rig's five projectors overshoot the LED wall, so four
are excluded — and they were being reported as "grazing at 55°" when the grazing threshold is
20°. `runaway` (a corner ray that never found a surface) forces the grazing flag whatever the
centre incidence was, so anything printing that angle was printing a number with nothing to do
with why the beam was dropped. Both faults are now published separately. And *Alignment & blend*
was printing `derived.overlap` raw — a panel about whether two beams meet was showing people
`{"pct":0,"pairs":0,"text":"NO OVERLAP…"}`, because that key grew from a string into an object
some versions ago.

**The imported model.** The note in the Scene Study said it plainly: *"They stay local. The bridge
has no word for an object."* That was defensible while a panel stayed open for a session, and
stopped being defensible the moment workspaces existed — pressing RIG & LOAD re-creates the areas,
the tool reloads, and a set piece somebody spent ten minutes placing was gone, silently, with the
room still claiming to be the room.

So the bridge learned the word, on the same bargain the venue GLB already had: bytes to the host
once on import, the pose riding on `objects` (which the room already posts on every move for the
Sketch Pad's benefit), both replayed on the handshake. Removal is **said, never inferred** —
pruning the store from the next `objects` list would empty it every time a panel reloaded, because
a booting room reports no objects before its replay arrives. Same class of bug as the sequence
loss, same rule: *a panel must not be taken at its word about what it holds before it holds it.*

**Media spec** knew the resolution an output wanted and never said whose output it was, so the one
question it is opened to answer could not be answered from it. It now names the sequence and the
surface — and a route to a drawn LED wall or a linked canvas resolves, where both used to come back
as "no output" on a correctly routed cue.

### Verified

- Sequence → output correspondence, end to end: two four-second clips recorded in the browser,
  SEQ 1 → PROJ 1 and SEQ 2 → PROJ 3, both live at once. The Video Preview follows SEQ 1, prints
  `OUTPUT PROJ 1`, and shows clip A while the room shows B on PROJ 3.
- Photometry: PROJ 5, 30,000 lm × 80% ÷ 97.4 m² lit = **247 lux**, ×0.85 ÷ π = **67 cd/m²**.
- The import survives SKETCH → CAMERAS → RIG & LOAD and comes back at its recorded pose.
- Twelve workspaces swept: no element overflows its box, no white field, no console error.

### Still true, and worth saying

- The pad's TILE input is square; a 600 × 337.5 cabinet round-trips intact through
  `tile.w`/`tile.h` and both grids use it, but that one field cannot express a non-square tile.
- Photometry is flux over lit area with a stated output factor. No ambient, no inter-reflection,
  no lens shading beyond the model above. It says so on the panel.


## 7 September 2026 — The room gets a fixed seat, a wall gets made of something, and the producer gets two views

### What changed

- **The Scene Study has one position in every workspace that contains it**: two thirds of the
  width, hard right, first area on that side. SKETCH is the one exception and splits 50/50 with
  the Sketch Pad — it is the same object drawn twice, and the whole activity is looking from one
  to the other.
- **The LED library is gone.** In its place, **LED tiles** — twelve real rental products across
  six uses, sorted by pitch — and a second panel, **LED tile**, which shows one of them at the
  size it is with its per-square-metre consequences.
- **A drawn LED surface can be made of a tile**, and everything downstream is that tile times the
  count the room measured: resolution, mass, draw and price.
- **Two producer panels**: a **Kanban board** whose cards are checklist steps, and a
  **Production Gantt** seeded from the take's own requirement groups.
- **Deadlines & burn-down was rebuilt** on the take's real dates.

### Why

**The room's position.** A list reads fine at 300 px and a room does not — you cannot judge a
sightline, a trim height or where a beam lands in a letterbox. But the argument that settled it is
the second one: somebody who presses SKETCH, then CAMERAS, then RIG & LOAD should find the room in
the same place all three times. If it moves, every switch costs a re-orientation, and the panel
people look at most is the one that can least afford it. So its position stopped being an output
of the layout algorithm and became a constant the algorithm works around — `withRoom`.

**The library was lying about what an LED screen is.** It listed cabinets the way the projector
library lists projectors — pick one, add one, own one. Nobody buys a screen. You buy a TYPE OF
TILE, and the shape you drew decides how many turn up on the truck. So the catalogue became a tile
catalogue and every number that used to be typed became a multiplication.

The load-bearing decision is **where the count comes from**. Not from here: the Scene Study
already builds the real cabinet grid on the real outline, faceting curves at half a cabinet, and
publishes it as `derived.builtGeometry`. That is what the panels read. Where the room has not been
opened yet the count is estimated from the outline — with true arc length, because summing chords
under-counts a curved wall and that is the direction of error that leaves you short on site — and
it is marked `EST` everywhere it surfaces. A tile count that cannot be sourced is the one number
in this workspace that ends up on a purchase order.

Applying a tile writes exactly one field: `sol.tile`, the cabinet size in take units. That field
already existed and the whole stack already understood it, so the pad re-grids, the room rebuilds
and the count comes back — measured, not calculated in the HUB. Verified end to end: a 10.8 × 6.1 m
wall at 500 mm is 21 × 12 = 252 tiles; the same wall re-tiled to INFiLED DB1.9 (600 × 337.5) is
18 × 18 = 324, the pad's own TILE field reads 0.60, and Rigging, Power, Footprint and Canvas all
land on 2,332.8 kg, 35,640 W (106,920 peak) and 5,688 × 3,186 px without being told separately.

**The catalogue's honesty.** Pitch, cabinet size and pixel count are the products' defining
published figures and are exact. Mass, draw, brightness and price move with batch, driver IC and
hire company — they are class figures to the nearest useful number and the panel says so, rather
than implying a spec sheet was consulted for this job.

**The Kanban's one real decision is what a card is.** A card is a STEP — one job across every
object it applies to — because that is how work gets handed to somebody. "Calibrate" is one card,
not eight. That makes the board a projection of the checklist rather than a second place to type
things: four of its five columns are DERIVED from the cells, and dropping a card WRITES them, which
is why moving a card moves the burn-down and the cost in the same instant.

IN REVIEW is the exception and it is the Snag list's argument again: "I have finished it" and
"somebody checked it" are different claims, and the gap between them is where load-ins go wrong.
The cells cannot express that, so it is the one piece of state the board owns.

**The Gantt starts full.** The schedule is already implied by the checklist — the groups of work
are known, how much work each holds is known, the window is known — so the first draft is those
three facts laid end to end. It is almost certainly wrong about the order, which is the point:
arguing with a draft is faster than building one. Dependencies are drawn because a bar starting
before the thing it waits on has finished is the most common error in a schedule and the one a
Gantt exists to show.

**The burn-down was decoration.** It drew a convincing chart off `const NOW = 0.62` — a hard-coded
position for the today line — so the headline read "62% of the time gone" on the first morning of a
job and on the last, and everything downstream of it (points behind the line, the colour, the
projection) inherited that. It now uses only facts the take holds: a start date, an end date, a
count of tasks and a count of closed ones. And it burns DOWN rather than up, because the question
is "how much is left", not "what percentage are we". Achieved rate is closed tasks over elapsed
days — the bluntest possible velocity, deliberately, because anything cleverer needs a history this
workspace does not keep. Under half a day gone it refuses to project at all rather than extrapolate
from a rounding error.

### Files and components

- `HUB_5.9.html` — `withRoom`, `ROOM`, `layoutFromPanels(list, share)`, `layoutStacked`,
  `applyTask`, `presetForIntent`; `TILE_LIB`, `TILE_PICK`, `applyTileTo`, `outlineLenDm`,
  `estimateLed`, `ledWalls`, `nearestM`, `ed-ledlib` (rewritten), `ed-ledtile` (new);
  `ed-kanban` + `KAN_COLS`/`KAN` (new), `ed-gantt` + `GANTT`/`seedGantt` (new),
  `ed-deadline` (rewritten); `ed-canvas`, `ed-rigging`, `ed-power`, `ed-green` now read
  `ledWalls`; `TASKS` (sketch, led, numbers), registry (`ledlib` retitled, `ledtile`,
  `kanban`, `gantt`), `PANEL_ALWAYS`.
- `SOLIDS.md` — new section *v5.9.1 · who authors `tile`*.
- Nothing changed in `sketchpad.html`, `scene-study-3d.html` or the bridge. That is the point of
  the tile going onto a field both of them already read.

### Known limits, stated rather than hidden

- **The pad's TILE input is square.** A 600 × 337.5 cabinet round-trips intact through
  `tile.w`/`tile.h` and both grids use it as such — it is only that one input field that cannot
  express a non-square tile.
- **The house limits are stated, not derived.** 32 A per phase, 1000 kg per point, 45 m / 50°
  on a sightline. They are the numbers the panels can be *wrong* about, which is what makes them
  worth having.
- **The checklist preset was left alone.** The room's fixed 2/3 applies to the task workspaces
  and the agent's lenses. Forcing it on the checklist layout would leave the grid and the step
  editor sharing a third of the screen, which breaks the thing that preset exists for.


## 2 September 2026 (7) — An LED floor you can draw, and a room that is not showroom-fresh

### What changed

- **`LED FLOOR` is a fourth stamp in the Sketch Pad's role menu**, offered on any closed plan
  outline — including a rectangle that has only just been drawn and is still a stroke.
- **The show opens at GLOSS 30%** instead of AS BUILT, and RESET returns to the same number.

### Why

Two requests. The first closes the Pending item the (4) entry left open: the horizontal LED was
only reachable off an imported model's face, so the obvious gesture — draw the floor's outline
on the plan and say what it is — did nothing horizontal.

**It is a variant, not a fourth role.** The take knows three roles and carries `lay` as a
separate field, so the pad keeps `role: 'led'` and stamps `lay: 'flat'` beside it. That kept
`SOLID_ROLE_SET` in the host untouched and meant the whole thing rode through the existing
`sanitiseSolid`. Three consequences, each a place the upright reading is wrong:

- **Closure.** Naming a shape WALL or LED OPENS it, because those are runs. A floor is an
  area, so this variant forces closed — the same way the pad has always forced a deck closed.
- **`h` changes meaning**, from how far the cabinets are extruded to the elevation the screen
  lies at. So a height nobody has touched resets to the new default rather than being
  reinterpreted as the other thing, and on the front page the shape is a plate at its
  elevation rather than a band rising off the deck.
- **The grid.** `ledGrid` already had the right arithmetic for this and had it for a different
  reason: an elevation-drawn LED is a face, so its grid is the outline's own bbox clipped to
  its shape. A floor is the same claim in the other plane, so it shares that branch and the
  run branch is left alone.

**One thing I got wrong first.** `canLieFlat` asked for `t === 'solid'`, and the role menu opens
on a **stroke** — naming an outline is what converts it. So the option was withheld from
exactly the case that was asked for: a rectangle somebody had just drawn. It accepts strokes
now, and refuses a straight LINE, because two points enclose nothing.

**On the gloss:** GLOSS is a CEILING rather than a value — at 1 every material is exactly what
it says it is, and below that each is dragged towards matte with its reflection scaled down,
staying differentiated all the way. Opening at 1 flattered every surface in the venue; a marley
floor has been walked on and a deck has been gaffed and struck a dozen times. RESET uses the
same constant, so "back to the default" and "what you opened at" are one place rather than two.

### Files and components

- `sketchpad.html` — `isFlatLed`, `canLieFlat`, `setLay`, `ROLE_STAMPS`, `openRoleMenu`
  (offer + tick), the role-menu click, `nameSolid`, `applyRole`, `nameHeld`, `ledGrid`,
  `drawLedTiles`, `solidTitle`, `elevationProfile`, `heldLeds`, the solid payload
- `scene-study-3d.html` — `GLOSS_DEFAULT`, `LOOK.gloss`, the look RESET
- `SOLIDS.md`

### Verification

Drew a rectangle in the pad with RECT and right-clicked it: the menu offers
STAGE / WALL / LED / **LED FLOOR**, where before the fix a stroke was offered only the first
three. Taking LED FLOOR reports *LED FLOOR · 18×10 TILES · 9.0×5.0 M* — 0.5 m cabinets over a
9 × 5 m outline — draws the cabinet grid over the AREA rather than faceting the perimeter, and
posts `role:"led"`, `lay:"flat"`, `closed:true`, `h:0`.

Replayed that payload through the hub's own BUILD path (`solids` → `panelSolids` →
`agentApplyOp` → `sanitiseSolid`), which is a different door from the face-pick's `addSolid`:
a 12 × 8 m outline builds **384 tiles in 1 panel** — 24 × 16 — lying flat in the room and
labelled STAGE FLOOR. No console errors.

Gloss: `LOOK.gloss` is `0.3` on load and the ROOM tab's GLOSS row reads **30%**.

### Pending

- The role ROW under the canvas still has three buttons, so an LED FLOOR shows LED lit there.
  Only the title and the menu tick distinguish the two; the row wants a fourth or a modifier.
- A flat LED's H field is an elevation and is labelled H like every other height. Dragging the
  plate's top edge in ELEVATION does move it, which is right, but nothing says the number means
  something different for this one shape.
- GLOSS only shows in RENDER — the look panel says so itself — so the new default is invisible
  in the working view. Somebody comparing the two views will not see 30% of anything.
- The default is the tool's, not the take's: it is not persisted, so a take saved before this
  opens at 30% too rather than at whatever it was built under.

## 2 September 2026 (6) — Half the horizontal faces described themselves upside down

### What changed

- **A horizontal patch is always described facing UP.** `facePatchFrom` negates a flat patch's
  normal when it points down, before the in-plane axes are derived from it.
- **A flat LED lies on the TOP of what it is on** — `maxY` rather than the patch centroid.
- **A flat LED's `h` is an elevation, not an extrude**, so it is no longer clamped to a whole
  take unit. A floor-level screen sat 10 cm in the air; it now sits at 1 cm.

### Why

Asked for directly: for an LED floor, make sure the face assigned is always the one pointing up.

**It was measurably broken and I had already shipped past it without noticing.** A patch takes
its normal from whichever triangle the ray happened to hit, and export winding is arbitrary —
which the fill already knew, because it joins triangles on `Math.abs(dot)` rather than the
signed one. Swept over `concert_stage.glb`: of 119 distinct horizontal patches, **63 pointed up
and 56 pointed down**. One of the down-facing ones was the 8.5 x 8.5 m platform at 5 cm that I
used as the worked example for LED FLOOR in the (4) entry.

Three things followed, and it is worth being exact about which:

- **The candidate's highlight fill was offset the wrong way.** It is nudged 6 mm along the
  patch normal so it does not fight the triangles it lies on; on a down-facing floor that put it
  6 mm UNDER the surface, where it is hidden. That is the visible symptom.
- **The fitted outline's order flipped with the normal.** `ay` is `cross(nW, ax)`, so it
  reversed, and the same face picked from two different angles produced two different vertex
  orders. Six seeds on one patch now produce one outline; before they did not.
- **The reported face was not the one you stand on**, which is what was actually asked about.

**What was NOT broken, and I should not claim it was:** the built emitting surface always faced
up regardless, because `buildLedSolid` rotates the holder unconditionally and works from the
solid's vertices rather than from the patch normal. The bug was in the DESCRIPTION, not the
build — which is why it showed up as a missing highlight and an unstable outline rather than a
black screen.

The other two changes came out of testing this one. `h` for a flat LED is the height the screen
lies AT, not how far it is extruded, so `Math.max(1, …)` — correct for a deck — floated every
stage-floor screen 10 cm off the deck. And a patch that merges a thin plate's top with its
underside has its centroid inside the plate, so a screen laid at the centroid sits a centimetre
below the surface it is meant to be on.

### Files and components

- `scene-study-3d.html` — `facePatchFrom` (the normal), `faceSolidOp` (`maxY`, the clamp)
- `SOLIDS.md`

### Verification

Swept every seed triangle of every imported mesh on `concert_stage.glb`, sampling 120 per mesh
and de-duplicating by patch centroid:

| | flat patches | normal up | normal down |
|---|---|---|---|
| before | 119 | 63 | **56** |
| after | 119 | **119** | 0 |

The 8.5 x 8.5 m platform at 0.05 m reports `ny: 1` where it reported `-1`. Six different seed
triangles landing on that patch now build **one** distinct outline.

End to end in the hub: that same platform promoted from the Sketch Pad as an LED FLOOR builds
`8.50 × 8.53 m` and is selected in both surfaces; the floor-level 67.5 x 39.8 m face builds at
**H 0.01 m** where it previously reported H 0.10 m. No console errors.

### Pending

- A genuine SOFFIT — a horizontal surface that only exists facing down — is now described as
  facing up like everything else, so LED FLOOR on one builds a screen facing up under a
  ceiling. A ceiling LED wants `lay: 'flat'` with a downward face, which nothing expresses.
- Picking the UNDERSIDE of a thick slab still gives a screen at the underside's height. The
  patch is what it is; jumping to the opposing face would be guessing which one is meant.
- The 0.1-take-unit minimum on a flat LED's elevation is there to stop it z-fighting the floor.
  It is a centimetre, and it is a fudge rather than a depth-bias.

## 2 September 2026 (5) — A taken face stopped existing on the paper

### What changed

- **A face that has been taken is still drawn on the Sketch Pad**, as BUILT — solid line, the
  built ink — instead of disappearing. It stays hittable, and its label says what it now is.
- **It stays selected, in both surfaces.** The pad adopts a `selectSolid` whose `srcId` names a
  model face, and announces one back the same way, so pointing at a built surface on the paper
  lights it in the room and the other way round.
- **The elevation says which way it is looking**: *ELEVATION · FROM THE AUDIENCE*, on the page
  and in the status chip.
- **The elevation has a depth cue.** Imported objects and their faces are drawn upstage-first
  and faded by depth, so near surfaces read as in front of far ones.

### Why

Reported as "LED floor is a bit buggy — when selected it disappears from the sketchpad", and
"once converted to LED it should stay selected, in both views".

**Both were the same bug, and it was mine.** When the pad started drawing model faces I made
taken ones stop drawing, on the argument that "the solid it became is on the plan in its own
right". That is true of a shape the PAD drew and false of one the room built from a model face:
the pad holds no item for that, and the take's solids are not sent to it — the pad is the
AUTHOR of solids, so it only ever holds its own. So taking a face removed the only outline the
paper had for that surface, and `IN.selectSolid` then could not find an item with that `srcId`
and cleared the selection. The pad's own comment had been saying so all along — *"a shape built
from a plan the pad never drew has no outline here to light"* — which was a fair description of
the world before faces were pickable and a bug report afterwards.

The fix is not to ship the take's solids to the pad. The face's id **is** the solid's `srcId`
(that was already true, from `faceSolidOp`), so the candidate outline is the outline, and it is
drawn as built rather than hidden. That also makes the echo guard fall out for free: an inbound
`selectSolid` naming a face produces exactly the key `announceSelection` would build, so the
selection does not bounce.

**The elevation was already the front view.** Asked to make it the front rather than the back, I
checked before changing it, and it is not mirrored:

- `buildConcert` puts its UPSTAGE LED at `z = -D/2` and `buildArena` puts its seating bank at
  `+FD/2`, so **+depth is downstage** — the audience side.
- The Scene Study's `front` preset is `yaw: 0`, which `applyOrbit` places at `target + (0,0,+dist)`
  — measured at `(0, 4.24, +54.02)`, on the audience side.
- Projecting `(+10, 2, 0)` through that camera gives NDC x **+86**: **+across is on the right of
  the FRONT view.** The pad's elevation puts `+across` on the right too (`x = ox + across·s`),
  and left–right is never negated anywhere in the pad — only page-y flips for the front plane,
  which is why `SOLIDS.md` negates front-plane bulges.

So plan and front elevation share the x axis, which is both the drafting convention and what
keeps the paper in step with the 3D FRONT view; mirroring it would have broken both. What the
view actually lacked was any statement of its direction and any depth cue — with every face
collapsed to across × height regardless of depth, an elevation is an overlay of everything at
once and reads as no particular viewpoint. Naming it and ordering it by depth is what makes it
read as a view *from* somewhere.

### Files and components

- `sketchpad.html` — `faceSel`, `drawRoomFaces` (built ink, depth order, label), `hitRoomFace`,
  the face pointerdown and contextmenu branches, `openFaceMenu` header, `announceSelection`,
  `IN.selectSolid`, `IN.objectFaces` pruning, the `c-faces` chip, `drawUpstage`, `status`,
  `drawRoomObjects` (depth order), and the new `faceDepth` / `depthFade`
- `AGENT-BRIDGE.md`

### Verification

In the pad, replaying the exact promote sequence — the face comes back `taken`, then a
`selectSolid` naming it: the chip goes `2 MODEL FACES` → `1 MODEL FACE · 1 BUILT`, the surface
is drawn in the accent rather than vanishing, and its label reads
*"20.0 × 12.0 m · FLAT — BUILT · right-click to change what it is"*. No `selectSolid` is posted
back, so the guard holds.

Full loop in the hub: promoting an LED FLOOR from the pad leaves the chip at
`27 MODEL FACES · 1 BUILT` **and** the Scene Study's readout naming the solid —
*LED FROM MODEL · led · H 0.10 m · 9.18 × 9.12 m*. Selected in both, which is what was asked.

Elevation: an upstage tower at depth −90 and a downstage riser at +70 draw faint-then-solid in
that order, the tower at across −120 on the left and the riser at +80 on the right; the chip and
the page both read FROM THE AUDIENCE. Plan is byte-for-byte the same behaviour as before — the
fade collapses to 1 and the order to the unsorted list off the plan.

### Pending

- Right-clicking a BUILT face offers the roles again, which the room answers by REPLACING its
  solid on the same `srcId`. That is the intended behaviour and it is not obvious from the menu
  that it replaces rather than adds; the header says "is BUILT · make it a…" and little else.
- The depth fade is linear between the nearest and furthest thing on the page, so two surfaces
  a metre apart in a shallow set look as different as two thirty metres apart in a deep one.
- A built face still cannot be MOVED from the paper. It is a solid in the take with a `srcId`
  the pad now understands, so `moveSolid` would work; nothing wires the drag.
- The pad still holds no item for a face-built solid, so BUILD 3D does not know about it and
  the SOLIDS count in the status bar does not include it.

## 2 September 2026 (4) — An LED can lie flat

### What changed

- **A horizontal surface can be an LED.** New `lay: 'flat'` on a solid: the fitted outline
  IS the emitting face, lying at `h`, tiled with real cabinets. Pitch, cabinet count,
  routing, crop and the video texture all work on it exactly as they do on a wall.
- **Both options are offered wherever a face is named**, in the Scene Study and the Sketch
  Pad, with the sensible one leading. A **flat** face gets `LED FLOOR` first and `LED WALL`
  second; a **standing** face is offered only the wall.
- **`ledRect` asks a surface which way it faces.** One looking up reports the DEPTH it
  covers as its second dimension instead of its height.
- **A floor is kept out of a canvas.** `linkLeds` drops flat members by name and says why.

### Why

Asked for directly: an LED should not only extrude vertically — a horizontal plane should be
able to be an LED, with both options available.

The old behaviour was not a missing feature so much as a **wrong default with no alternative**.
A floor-plane outline named LED was read as a footprint and the cabinets stood up out of it.
That reading is real — it is the fascia round a stage edge — but it is the rarer of the two,
and pointing at a horizontal surface almost always means a screen lying in it. The only way to
get one was to name it a DECK, which is exactly the role that throws away pitch, cabinet count,
route and crop: the four things you point at a screen to ask about. So both readings are now
offered, and which one leads is decided by the face's own orientation rather than by the
schema's history.

**It is barely any new geometry.** A `front`-plane LED already did the hard part — take the
fitted outline as the emitting face and clip a cabinet grid to it — so a flat LED shares that
branch entirely and differs only in how the finished holder is turned: −90° about X, which
sends local +z to world +y so the face looks UP. The outline's second coordinate is DEPTH, so
it is negated on the way in; without that every flat screen came out mirrored front-to-back,
which is the same correction `SOLIDS.md` already documents for a front-plane arc.

**The two places that assumed a vertical screen are worth recording.** `ledRect` returned
`h: size.y`, which is zero for a horizontal surface — and the clip's aspect, the FILL crop and
the canvas share all divide by it. And `ledCanvas` lays one picture across a single horizontal
axis with height as the other dimension, which has no meaning for a floor; rather than let a
member take a zero share of a canvas, `linkLeds` now refuses it out loud.

### Files and components

- `scene-study-3d.html` — `buildLedSolid` (the flat branch, mirroring, holder orientation,
  `labelY`, `emitW`), `faceSolidOp`, `faceAssignMany`, `roleWord`, `faceMenu`, `ledRect`,
  `linkLeds`, `IN.promoteFace`
- `sketchpad.html` — `openFaceMenu` (the LED split), the menu click, the flash
- `HUB_5.8.html` — `sanitiseSolid` carries `lay`; the `promoteFace` relay passes it
- `SOLIDS.md`, `SCENE-STUDY-BRIDGE.md`, `AGENT-BRIDGE.md`

### Verification

Driven in a browser. In the hub against `glb/Stage/concert_stage.glb`: the menu on a flat face
offers `LED FLOOR` (`lay=flat`) then `LED WALL` (`lay=""`) then WALL then DECK; taking the
67.5 × 39.8 m ground as an LED FLOOR builds **10,800 tiles in 1 panel** lying at the right
height, and the grid is visibly horizontal. Taking an 8.5 × 8.5 m platform top **from the
Sketch Pad** — `promoteFace {faceIds:[…], role:'led', lay:'flat'}` — comes back as
**289 tiles in 1 panel**, which is 17 × 17 at a 500 mm pitch.

A standing face's menu correctly shows one LED entry, not two, in both surfaces.

Rebuilt the mock take's LED solid as a closed flat one and asked the router about it:
`cropFaces` returns exactly one face, `ledSurfaceIds` includes it, its surface is named
`LED ARC FLOOR`, its local +z in the room is `[0, 1, 0]` — the face looks up — and `ledRect`
reports `w: 12, h: 8, lying: true` where it would previously have reported `h: 0`.

### Pending

- A flat LED takes no part in a canvas. Two floors side by side as one picture is a
  reasonable thing to want and would need `ledCanvas` to lay out on a horizontal PLANE
  rather than a horizontal axis.
- The Sketch Pad still cannot draw a horizontal LED from scratch — the split is offered on a
  model's face, not on the pad's own `ROLE_STAMPS`. Naming a closed plan outline LED there
  still gives the upright reading. That is the obvious next step and touches the pad's role
  model rather than this geometry.
- `lay` is honoured on the floor plane only. `plane: 'front'` with `lay: 'flat'` is ignored,
  which is right — a front-plane outline is already its own emitting face — but nothing says so.
- No frame is drawn round a flat screen. The upright run gets truss round its panels; a floor
  gets its outline edge and nothing else, which reads fine and is not a considered decision.

## 2 September 2026 (3) — A clip lost its route on the way to every other panel

### What changed

- **A clip pushed to another panel keeps its destination.** `installClip` now reads
  `tracks[].route` from the take when the caller does not name one. This is what made video
  invisible in Camera POV panels.
- **The POV bar has a transport.** PLAY/PAUSE, beside SKY and RENDER, and only when the take
  has clips. Same reason those two are there: the control lives on a toolbar this mode hides.
- **A mesh venue's beams are re-thrown when it lands** — see the (2) entry; the same
  `syncDevices` call also fixes the stale figures that made the delete look asymmetric.
- **The board no longer keeps an allowlist of model names.** `VISION_STATE` was keyed
  `smolvlm2` / `tracer` / `off`, so the moment the service honestly reported a different
  family it fell through to `off` and the REFERENCES panel said CANNOT READ over a model that
  was answering perfectly well. It keys on the two states that mean something and treats
  "a model is named" as the test for the third.
- **`agent/vision.py` points at 4096 and prefers Qwen.** LM Studio serves on 4096 on this
  machine, not its default 1234; and the auto-picker took the first id containing `smolvlm`,
  so even on the right port it would have chosen the wrong model.
- **`5.8/agent/.venv` exists**, with the half of `requirements.txt` the LM Studio backend
  actually uses.

### Why

**The route bug is the interesting one.** The bytes and the route travel by different doors —
`mediaAsset` carries the megabytes, `scene` carries the decision — and `applyScene` adopts the
route onto clips it already holds. On a panel opening cold the host sends `scene` first and the
bytes last, so that loop ran over an empty clip map; the clip then arrived with no route and
`installClip` fell back to `canTake`, the panel's own selection. In a Scene Study you had
probably selected the wall, so it looked fine. In a Camera POV panel the selection is a camera
or nothing — and the clip was installed, `active`, seeking correctly, with its texture bound to
no mesh at all. Measured before the fix: `route: "projectors-1"`, texture on **0** meshes.
After: `route: "led-1"`, texture on `led-surface`.

An explicit `null` is kept distinct from `undefined` on purpose. "This track is thrown at
nothing" is a decision; "the take has not said" is not, and only the second one should let a
panel guess.

**Two stale servers cost most of a session.** `:3900` was serving `Productions/5.7` and the
agent on `:3904` was running `5.7/agent`, both from before this work. Every report of "the
feature does not work" was true of the code being served and false of the code on disk —
`curl localhost:3900/sketchpad.html | grep -c 'DELETE FROM THE MODEL'` returned 0 while the
file on disk returned 1. Worth checking first, next time, before reading any code.

### Files and components

- `scene-study-3d.html` — `installClip` route precedence, `setupPovChrome` transport,
  `syncPovPlay`, `IN.transport`
- `HUB_5.8.html` — `VISION_STATE` / `visionState`
- `agent/vision.py` — `LM_STUDIO_URL`, `LM_STUDIO_PREFER`, `_lmstudio_model`, `_engine_name`
- `agent/.venv` — new
- `SCENE-STUDY-BRIDGE.md`

### Verification

Face delete confirmed with real gestures on `:3900` once it was serving 5.8: in the Scene
Study, clicking the 20.47 × 15.12 m upstage face and pressing DELETE FROM THE MODEL reports
*"1 face deleted from the model · 2 triangles · 309.5 m²"* and the wall leaves the mesh; in the
Sketch Pad, clicking a candidate gives *1 OF 2 FACES HELD* and DEL posts
`deleteFace {"faceIds":["f3"]}`.

Route fix measured directly in a POV panel against a generated 5 s H.264 clip, installed the
way `IN.mediaAsset` installs one — no route argument. With `tracks[0].route = 'led-1'` the clip
resolves to `led-1` and its texture binds to the `led-surface` mesh; without the fix the same
call resolved to `projectors-1` and bound to nothing. The PLAY pill is absent on a take with no
clips, appears when one loads, and flips to PAUSE on click.

Agent: `:3904` reports `engine: local`, `stub: false`, `vision.engine: qwen`,
`model: qwen/qwen3.8-27b`, and the REFERENCES panel reads VISION · READS DRAWINGS.

**Not verified: moving video.** Chrome pauses media and throttles `requestAnimationFrame` in a
hidden page, and this session's browser pane is hidden — `video.play()` resolves without error
and the element stays paused. The routing, the texture binding and the transport wiring are all
confirmed; that the picture actually moves is not, and wants a human eye on it.

### Pending

- The venv omits `torch`, `torchvision`, `transformers` and `accelerate`. The LM Studio backend
  never imports them — they are the `VISION_BACKEND=transformers` dev fallback — and they are
  several GB. `requirements.txt` still lists them, so the venv and the manifest disagree by
  design; install them if that fallback is ever wanted.
- `installClip` hardcodes `type: 'video/mp4'` on the Blob it builds, so a `.webm` would be
  handed to the element under the wrong MIME type.
- `syncClips` calls `video.play().catch(() => {})`. A refusal — autoplay policy, an
  unsupported codec — is swallowed, and the wall shows a frozen frame with nothing said. It
  should name that state the way every other failure in this tool does.
- `LM_STUDIO_PREFER` is a substring list because `/v1/models` says nothing about a model's
  modality. A text-only model whose id matches one of those substrings would be chosen and
  would fail per-request rather than at selection.

## 2 September 2026 (2) — Faces on the front page, held in sets, and droppable

### What changed

- **An import and its faces are drawn in ELEVATION as well as on the plan.** Both were plan-only on the argument that a footprint is a fact about the floor — true of a footprint, and not of the thing casting it. A set piece is four metres tall or forty centimetres tall, and on a front page that is the one thing about it that matters: the difference between a wall you can throw over and a wall you cannot. So each view draws the two dimensions it can actually see, from the same published box — across × depth on the plan, across × height on the front — and the faces follow the same rule with their two shapes swapped over: what is a rectangle from above is a line from the front, and what is a line from above is a rectangle from the front. A face square to the front page collapses to a line there, which is the honest answer the pad already gives for anything drawn in the other view.
- **Faces are held in SETS.** Shift-click accumulates in both surfaces, exactly as it does for kit and for shapes on the paper, and the menu then speaks about the set: *"5 faces · 219.9 m² become LED WALLS"*. A plain click is still a fresh single choice, so the one-click flow is unchanged.
- **A set of LED faces can be asked for as ONE CANVAS in the same act.** A screen modelled as five flats is five walls each showing its own copy of the clip until somebody says otherwise, and the place that thought is had is the menu on the faces. `promoteFace` carries `link`, and the Scene Study answers it with `requestLink`, which already knew how to wait across pushes for solids that do not exist yet.
- **Faces can be deleted from the model.** DEL on a held set, or DELETE FROM THE MODEL in either menu. This is the step that follows almost every pick: once the modelled screen IS a real LED wall, the modelled one is standing in the same place, taking the same light and drawing the same surface twice. **The solid made from a face survives its deletion** — it is a take fact and this is a fact about a mesh, and having the delete take the LED wall with it would make the feature useless. RESTORE, per model, is in the face menu.
- **And a projector's beam is re-thrown when the room's mesh changes** — including the pre-existing case below.

### Why

Asked for directly: reproduce the imported object in the elevation view, allow multiple selection of LED walls in the object, and allow faces to be deleted when selected.

**The delete collapses triangles rather than cutting them out**, and that is the part worth reading. Rebuilding the index without them is the obvious edit and wrong twice: a mesh with several materials carries GROUPS that index that buffer by offset, so shortening it re-materialises the model; and every triangle after the hole shifts number, invalidating the one cache that makes picking fast. Collapsing a triangle onto a single vertex leaves the buffer exactly as long — groups and materials untouched, numbering fixed — and a zero-area triangle draws nothing, is never hit by a ray, joins no patch (its normal is zero, so it fails the coplanar test against everything, itself included) and carries no area, so it is already below the threshold that decides what a face is. It also makes RESTORE a single `.set()` back into the same buffer.

**A pre-existing bug, found while checking that a delete re-derives.** `finishVenue` has carried a note for a long time saying that a late mesh which skipped it "left every beam clipped to the old room" — and that was still true of the figures people actually read. `rec.landing` is solved in `updateBeam`, which only `updateDevice` calls, which only `syncDevices` calls; `finishVenue` called `updateProjection` (which rebuilds the projected IMAGE) and `scheduleMeasure` (which only re-prints what was last solved). So every mesh venue — all three `./glb` presets, arriving a second or two after the parametric fallback — left every throw distance, image size and pixel density describing the fallback that had been standing there. Deleting a face was simply the first thing in a session to re-cast them, which is why the numbers moved on the delete and would not move back on the restore: neither reading was wrong, the BASELINE was. `finishVenue` now calls `syncDevices` too.

That also cost a wrong diagnosis on the way: the first fix re-threw the beams by looping `updateBeam` directly, which solves from `rec.root`'s current world transform without the `updateDevice` step that puts the root where the take says the device is. Reusing the canonical pass is both shorter and the only version that agrees with a scene build.

### Files and components

- `scene-study-3d.html` — `faceHeld`, `faceToggleHeld`, `faceActOn`, `faceAssignMany`, `deleteFaces`, `faceRestore`, `faceGeoIndex`, `faceGeometryChanged`, `faceRecOf`, the set-aware `faceMenu`, shift on `facePress`, DEL, `IN.promoteFace` / `IN.deleteFace`, and `finishVenue`
- `sketchpad.html` — `drawRoomObjects` and `facePathsFor` in both projections, `faceHeld` / `heldFaces` / `faceActOn`, the set-aware `openFaceMenu`, the shift-band guard, DEL, and the `c-faces` chip
- `HUB_5.8.html` — `promoteFace` carrying `faceIds` and `link`; `deleteFace` relayed
- `SCENE-STUDY-BRIDGE.md`, `AGENT-BRIDGE.md`

### Verification

Driven in a browser. Scene Study standalone against `glb/Stage/concert_stage.glb`: shift-clicking the two side screens reports *2 faces held · 219.9 m²* and draws both in the accent; plain-clicking one opens *"2 faces · 219.9 m² become"* with LED WALLS · ONE CANVAS and DELETE FROM THE MODEL. Deleting them removes both from the mesh — confirmed three ways: visually, by the raycast at that point now reaching the frame behind (14.14 × 8.27 m rather than 13.81 × 7.96 m), and by the throw distances re-deriving. RESTORE appears only once something has been deleted, and delete-then-restore returns the scene to exactly its baseline: zero degenerate triangles and byte-identical beam landings.

Pad standalone, in ELEVATION: a 3 × 9 m truss tower stands on the ground line; a standing face draws as its rectangle and reads *13.8 × 8.0 m · STANDING*; a face seen edge-on collapses to a vertical line and is still hittable; a flat deck draws as a line at its height. Shift-click gives *2 OF 3 FACES HELD*, and the menu posts `promoteFace {faceIds:['f1','f2'], role:'led', link:true}`.

Full loop in `HUB_5.8.html`, both panels live: 28 faces reach the pad; a two-face `promoteFace` with `link` comes back as two LED walls and the Scene Study's own status bar reads **CANVAS OF 2**, with `ledLinks` naming both source ids; `deleteFace` from the pad is answered in the room with *"2 faces deleted from the model · 4 triangles"*. Only the AI3N agent's CORS errors in the console, which are the served port.

### Pending

- **The face count does not drop when you delete.** `FACE_MAX_PER_OBJ` is 28 and the concert stage has more qualifying faces than that, so deleting two promotes two more into the visible set and the chip reads 26 either side of the act. Honest, and confusing; the count wants to say "28 of 41" or the cap wants raising.
- Undo is per MODEL, not per face. A stack of index buffers would give per-face undo; what people want after deleting the wrong wall is the model as it arrived.
- The published footprint is still the mesh's full bounding box, so deleting a face does not shrink the box the pad draws. Bounds come from the position attribute, which a collapse does not touch.
- A held set is cleared when PICK FACE is left, and by anything that takes its faces. It is not persisted anywhere, so it does not survive a reload — the same as every other selection in the tool.

## 2 September 2026 — A model's faces are a set, not a search

### What changed

- **An import is segmented into its faces once, and the set is SHOWN.** PICK FACE could already flood-fill a coplanar patch from a raycast and turn it into a solid. What it could not do was tell you a face was there: the only way to find one was to sweep the pointer over the model and watch a highlight come and go. Entering the mode now segments every imported `.glb` into all of its coplanar patches, keeps the significant ones, and outlines them in the viewport — and the toast says how many, so an empty result is an answer rather than a silence.
- **The Sketch Pad is told that set, and can take one.** The pad already received an import's FOOTPRINT (`objects`, v5.8), which is enough to stop somebody drawing through a truss tower and nothing like enough to draw *with* a set: a stage arriving as one file was a dashed rectangle with a cross through it, while the deck and the three walls inside it were pickable in the room and nameable nowhere on the paper. The faces now travel too — `objectFaces` — as **the outline each one would become**, already in take units and already projected onto the plan. The pad draws them, counts them in a `N MODEL FACES` chip, labels the one under the pointer, and right-clicking one offers DECK / WALL / LED.
- **Either surface can take a face, and it is the same op.** The pad cannot build one: the fit is a fact about geometry and the Scene Study is the only surface holding any. So the pad names the face (`promoteFace`), the room answers it out of its own candidate set, and it leaves by the same `addSolid` door a click in the viewport uses — one op builder, one sanitiser, one id.
- **Hovering a face on the paper lights the same face in the room** (`hoverFace`), which is the point of publishing the set rather than a count: two surfaces looking at one model should agree about which part of it is meant.
- **A taken face knows it is taken.** `faceSolidOp`'s `srcId` is now the face's own id, keyed to the patch's LOCAL centroid rather than to where the model happened to be standing. Two things follow that could not work before: a picked face is ticked instead of silently re-offered, and re-picking one REPLACES its solid instead of stacking a second on top — the host's srcId rule already said so, but the old key changed the moment the model was dragged.
- **A preset venue's mesh is an import too.** `loadVenueGLB` now tags what it installs, so the three mesh venues are segmented like any other `.glb`. Without it the face SET and the face PICK disagreed about one room: you could take a face of the concert stage by hand and it was never offered as a candidate. The PARAMETRIC rooms are deliberately not tagged — their floor slab is the room itself, not a surface anybody routes a clip to.

### Why

Asked for directly: make the faces of an imported `.glb` selectable so they can become LED screens, and make that agree with the Sketch Pad — "in the scene study and in the sketch pad I don't only need to see a block, I need to see the main shapes and the main faces that I can select".

The mechanism for taking a face existed. **Discovery did not, on either surface**, and that is the whole difference between a feature and a feature somebody can use. Everything that makes a surface MEAN something here — a clip routed to it, a crop placed on it, a canvas linked across it, cabinets counted in it — belongs to a solid with a role, and until now a set arriving as a model had to be traced by hand to become the stage it already was.

Two things were harder than expected. **Adjacency has to be built by POSITION, not by index** — exported geometry splits vertices for normals and UVs constantly, so an index join stops at every seam — which 6b already knew; the new part is that a full segmentation walks it for every triangle rather than one patch, so the walk is cached on the geometry and the fitted boxes are cached against the holder's matrix. They go stale for different reasons: moving an object does not change its geometry.

And **the first pass was invisible**. 28 faces were in the scene, correct, drawn with `LineBasicMaterial` — which WebGL renders one pixel wide whatever `linewidth` says, a limitation this file already had a note about. A hairline against a lit mesh is not an answer to "what can I take", so the candidates use `Line2` at 1.6px with a very faint depth-tested fill: an outline reads as a box, a fill reads as a SURFACE, which is the thing being offered.

### Files and components

- `scene-study-3d.html` — new section *6c · THE FACES A MODEL HAS* (`faceSegments`, `modelFacesOf`, `faceRecords`, `paintFaceCandidates`, `postObjectFaces`), `faceIdFor` and `faceUnder`, `faceSolidOp`'s `srcId`, `setFaceMode`, `loadVenueGLB`, `resize`, and `IN.promoteFace` / `IN.hoverFace`
- `sketchpad.html` — `IN.objectFaces`, `drawRoomFaces`, `hitRoomFace`, `hoverRoomFace`, `openFaceMenu`, the `c-faces` chip, and the three pointer hooks
- `HUB_5.8.html` — `case 'objectFaces'` on the bridge side; `case 'promoteFace'` and `case 'hoverFace'` on the panel side
- `SCENE-STUDY-BRIDGE.md`, `AGENT-BRIDGE.md` — the three new message types

### Verification

Driven in a browser rather than asserted. Standalone, against `glb/Stage/concert_stage.glb`: 28 faces found and outlined, no console errors; hovering the upstage screen reads `2 triangles · 13.81 × 7.96 m · standing`; clicking it opens the role menu and posts `addSolid` with `srcId: "mf:venue:41c7f41e:…"` — the stable face id, which is what proves `faceIdFor` adopts a candidate's identity for a hand-picked patch. The parametric default venue correctly reports *no model faces*, which is the tag doing its job.

Pad standalone, against an injected payload: the flat deck and both standing walls draw, the `taken` one does not, the chip reads `3 MODEL FACES` of 4 sent, right-clicking the deck opens `CONCERT_STAGE · 20.0 × 12.0 m face becomes a…` and posts `promoteFace`, and hovering a wall posts `hoverFace` and prints one label — the label is held to a single face because with it on both the hovered and the held one, neither said which was which.

Full loop in `HUB_5.8.html`, both panels live: the Scene Study finds 28 and the pad's chip reads `28 MODEL FACES`; `promoteFace` from the pad comes back as a faceted LED wall standing on the model's upstage screen, and the pad's chip drops to **27** with that face marked taken. The only console errors are the AI3N agent's CORS failures, which are the served port and not this.

### Pending

- `FACE_MIN_AREA` is 0.35 m² and `FACE_MAX_PER_OBJ` is 28. Both are judgements about what "main" means and neither is exposed; a model of a small set may want the floor lower, and a stadium may want the cap higher.
- Segmentation is skipped above `FACE_TRI_BUDGET` (300k triangles) rather than done in the background — such a model gets no candidates, though hover-picking still works on it because that only ever fills the one patch under the pointer.
- A face is fitted with an ORIENTED BOX, which is right for the rectangular surfaces this is for and wrong for an L-shaped deck: it would come back as the rectangle that contains it. The pad remains the place to draw a shape that is not a rectangle.
- The candidates are drawn only in PLAN on the paper, for the same reason a footprint is. An elevation page has no place to put them.

## 25 August 2026 — The rest of it: a named shape's handles were eating the next gesture

### What changed

- **A drawing tool is no longer intercepted by the SELECTED shape's handles.** Yesterday's fix stopped the BODY of a solid grabbing a press under TRACE, PEN, LINE, RECT and ELLIPSE. It left the vertex, apex, transform-corner and rotate handles alone, on the argument that they are 8px targets on one shape and would not swallow a whole gesture. That was wrong, and the report that came back said so.
- **An open run has no phantom inside.** `pointInPoly` closes the ring implicitly, so a wall or an LED run drawn as a line claimed the whole area between its ends and answered for every right-click inside it. A run is its line.
- The crosshair now shows over a shape's handles under a drawing tool, because that is what the press does there.

### Why

Reported twice as "once an LED is assigned there is no more right-click functionality on the next shapes".

**Naming a shape SELECTS it, and selecting it is what turns its handles on.** So the first role you assign is the moment that shape's entire outline, its four corners and its rotate handles become grab targets. A stage plan is drawn edge to edge — the next shape almost always starts on or beside the last one's line — so the press resized the named shape instead of drawing. No new shape existed, and right-clicking where it should have been found only the shape that had just been quietly stretched.

Reproduced by starting a rectangle exactly on the LED wall's bottom-right corner: no new item, and the wall went from 450×180 to 630×320.

Two mistakes on my side worth recording. The first pass fixed the body and left the handles, having spotted them and reasoned they were too small to matter — the report disproved that inside a day. And the reason it took three attempts is that every repro I wrote drew shapes in clear space; the bug lives exactly where a real plan is drawn, on the line of the thing you just named.

### Files and components

- `sketchpad.html`

### Verification

34 assertions, the new ones aimed at the actual failure: a shape started on a CORNER, on an EDGE MIDPOINT and on a VERTEX of a named LED wall is drawn rather than resizing it; the wall's vertices are byte-identical afterwards; right-clicking one of those new shapes opens ITS menu with a fresh question. Guarded the other way too — SELECT still moves a solid by its body AND still reshapes it by its corners, Option-drag still cuts, right-clicking empty paper still opens nothing. Plus 45 + 36 + 20 on the other pad suites and 17 in the real Hub.

### Pending

- Reshaping now requires SELECT (V). That is what SELECT is for, but it is a habit change for anyone who was nudging vertices with the trace tool armed.

## 24 August 2026 — You could not draw on top of a shape

### What changed

- **A drawing tool draws, whatever is already there.** `pointerdown` had a branch that grabbed the BODY of any solid under the press — "select it, and drag it whole" — excluded only for erase, stamp and text. So TRACE, PEN, LINE, RECT and ELLIPSE all picked the old shape up instead of starting a new one, and the new shape simply never existed. Moving a shape is what SELECT is for; the drawing tools are excluded now.
- **Which shape you mean is the one on top.** `hitShapeForStamp` asked `hitSolidNear` first and only then looked at strokes, so an outline drawn inside an existing solid could never be reached: the solid underneath always answered. It is one pass in z-order now, taking the first thing of either kind the point is on.

### Why

Reported as "once a shape is defined as LED, the following shape doesn't respond to the right-click menu — an LED assignment stops further assignment behaviour."

It is not about LED, and it is not about stamps. **Assigning a role is what turns a stroke into a solid, and only a solid has a body to grab.** So the first role you assign is the moment the paper stops accepting new ink over that shape — draw a wall, name it, try to draw the next thing over or inside it, and nothing happens; right-click there and you get the wall's menu, because the wall is what is under the pointer. LED is simply the role people assign first, to the biggest shape on the page.

Both halves had to go: fixing only the hit test would have found a shape that could never be drawn, and fixing only the draw would have left the new shape unreachable underneath the old one's answer.

### Files and components

- `sketchpad.html`

### Verification

25 assertions in a browser, built from the reported sequence: a large LED wall, then a shape drawn wholly INSIDE it exists and is a new stroke; the hit test answers with the shape on top; right-clicking it offers a fresh question and naming it leaves the LED wall alone; all five drawing tools leave a mark over a solid; and three shapes drawn in a row after an LED are each named LED, STAGE, WALL. Guarded against over-correcting: SELECT still picks a solid up by its body, Option-drag still cuts rather than draws, and right-clicking empty paper still opens nothing.

### Pending

- A selected shape's vertex and transform handles still take a press under a drawing tool. They are 8px targets on the selected shape only, so they do not block a gesture the way a whole body did — but it is the same class of surprise, and the same argument would remove them.

## 24 August 2026 — RENDER in the Camera POV, and the diagram coming off

### What changed

- **The POV pill row carries RENDER where INFO used to be.** A POV panel is the one view that is already a picture of the show rather than a diagram of it, so a lit preview is worth more there than anywhere else — and it was the one panel that could not reach the toggle, because the toolbar it lives on is hidden in that mode. The frame guides INFO carried are on the `I` key now, and `R` renders; the button's title says so.
- **The diagram comes off in RENDER; the picture stays.** A beam cone, a halo, a floating label and the orange outline round a footprint are how the tool EXPLAINS a projector. The image landing on the wall is what a projector does. A render that kept the explanation drawn over the result is neither one thing nor the other, so `applyRenderOverlays` hides the first set and leaves the second — and runs again after `syncDevices` and after the projection rigs are rebuilt, because either of those hands the diagram back.
- Two things `setRenderPreview` was doing that only made sense when the Scene Study was the only panel that could call it: `gGrid.visible = !renderPreview` gave the POV panel a floor grid it never had on the way out of RENDER, and `renderPov`'s unconditional restore of the viewed camera's own body lit its halo and beam back up. Both now ask which mode they are in.

### Files and components

- `scene-study-3d.html`

### Verification

30 assertions driven in a browser against `?mode=pov`: INFO is gone and RENDER is in its place; toggling it blacks the room, drops the render floor in and lights the same key the Scene Study gets; every beam, halo and label goes and every projected image stays; coming back restores the working rig exactly and does NOT grow a grid; `I` and `R` work; picking another camera does not drop out of RENDER.

### Pending

- The measurements HUD stays over the picture in a POV render. It is the panel's own readout rather than scene furniture, and its toggle lives on the hidden toolbar.

## 24 August 2026 — The Sketch Pad's zoom, which was three bugs

### What changed

- **Scroll pans, pinch zooms.** Every wheel event used to zoom, so on a trackpad the gesture everybody uses to move around a drawing changed the magnification instead. The mapping is now the one every drawing tool on a Mac uses: a plain scroll moves the paper, a pinch (reported as a wheel with `ctrlKey`) zooms about the pointer, and ⌘/Ctrl-scroll zooms too for a mouse with only a wheel.
- **There is a pan.** Middle-drag, or space held. Zooming in used to trap you looking at whatever happened to be under the cursor with no way to travel.
- **The paper reaches the edges of the view.** The grid, both axes, the ground line and the caption were drawn over `[0,0 → canvas W,H]`, as if the canvas and the paper were the same rectangle. They are only the same rectangle at 1:1 and unpanned: zoom out and the grid stopped a third of the way across with the drawing floating in an empty void. Everything that describes the paper asks `viewRect()` where the paper actually is, and everything drawn at a fixed size divides by the zoom, so a one-pixel line stays one pixel and a 9px label stays 9px at any magnification.
- **A way back**, because scrolling exactly as far as you scrolled in is not one: a zoom chip in the status bar — click to fit the drawing, shift-click for 1:1 — and `0`, `F`, `+`, `−` on the keyboard.
- The fine grid stops being drawn once its squares are under about five pixels. A whole 1 m grid at 15% is thousands of lines and none of them legible.

### Files and components

- `sketchpad.html`

### Verification

20 assertions in a browser: scroll pans without changing the zoom and pinch zooms about the pointer; the grid reaches all four edges of the canvas at 1:1, panned, zoomed in and at 15%; the chip fits and resets and reports the percentage; space-drag moves the paper and draws nothing while it does; and a right-click still finds the shape under the cursor after a zoom, which is the check that the hit test and the drawing are using the same transform.

## 24 August 2026 — Saying what something is: right-click roles, dragged anchors

### What changed

Two different questions used to share one dropdown, and sharing it was the whole problem. "Where is the projector" and "what is this outline" are not the same act: the first is a POSITION and the second is a PROPERTY OF A SHAPE YOU ARE POINTING AT. They are split by what they are now.

- **A shape's role is a right-click on the shape.** STAGE / WALL / LED, on the thing itself, each with its hint, and the one it already is marked. Nothing to arm and nothing to aim. If the outline is still a stroke it becomes a solid in the same act — declaring what a drawing is and declaring it geometry are one gesture. It leaves no pin.
- **PROJ, CAM and AUDIENCE are three toolbar icons** you drag onto the paper. The press arms, the drag carries the glyph across the drawing, the release places it. Shift keeps one armed for a run of them.
- **TRACK and SCREEN are gone.** SCREEN was a second name for WALL.
- **A stamp is a one-shot.** Arming used to put the pad in STAMP mode and leave it there: every click afterwards dropped another one, so the honest answer to "why has nothing else worked since I placed that" was that the pad was still placing. Nothing was broken and nothing said so. This was the LED bug.

Three things fell out of doing it properly:

- **The toolbar was hiding controls.** It was an `overflow-x` container with the scrollbar hidden, so in a Hub-sized panel everything past the drawing tools sat off the end of a bar that did not look scrollable. It wraps now.
- **The status line was eating its own messages.** `flash`, the stroke count and the hover readout all write to `#c-strokes`, and the latter two run on every pointer move — so any message raised by a gesture that also moved the pointer was overwritten in the same tick. A flash claims the line for its 2.6 s now.
- **UNLOCK left BUILD with nothing to do.** With LIVE on, the edit reaches the take while the hand is still moving, so the revision counters agreed again and the button greyed out — and the shape could never be re-locked through the only control that locks. A shape that has been unlocked counts as in hand until BUILD confirms it.

### Files and components

- `sketchpad.html`

### Verification

36 assertions on the new model plus the 45 that were already there, and 17 in the real Hub over HTTP with the three panels loaded and an agent stub answering `/health`: draw, right-click to name, drag an anchor out of the toolbar, build, unlock, edit, rebuild. Both shapes arrive in the Scene Study.

## 24 August 2026 — The gizmo holds the room, not just the kit

### What changed

- **A shape from the Sketch Pad can be moved and turned in the viewport.** The gizmo asked `selectedDevice()` directly, so a deck or an LED wall could be selected, outlined and deleted in 3D but never moved in it — which is the one thing a spatial tool is for. `grabTarget()` holds either kind.
- **ROTATE is on by default.** Boot ran `setGizmoMode('move', true)` — the EXCLUSIVE form — which cleared the set and quietly overrode the default declared two hundred lines away. Two statements of the same default, and the far one won, which is why turning something needed a key nobody knew about.
- A solid gets three arrows and ONE ring. Its `rot` on the wire is a single angle about the vertical, so offering three rings would be offering two that snap back.
- **The rotate ring could not be grabbed.** Its invisible hit tube was 0.06, about two pixels across in a panel-sized viewport: drawn perfectly, impossible to catch. It is 0.15 now, still clearing the arrow heads, which orbit inside it.
- New **`moveSolid`** message — `at` in take units, `rot` in degrees about the vertical, the same two fields the Sketch Pad writes, so a shape nudged in 3D and a shape nudged on the pad are one fact arriving by two doors. Additive, so `BRIDGE_V` stays 1. The host writes them onto `take.solids[i]`.
- The readout names the shape and its angle instead of saying "nothing selected" while a deck sits there outlined and moving.

### Files and components

- `scene-study-3d.html`
- `HUB_5.8.html`
- `SCENE-STUDY-BRIDGE.md`

### Verification

26 assertions standalone and 12 in the real Hub: the gizmo appears on a deck built from the pad, three arrows and one vertical ring; dragging the X arrow moves it along X only and writes the new place back in take units; dragging the ring turns it and the angle reaches the take in degrees; a rebuild does not put it back; swapping between a device and a shape rebuilds the right gizmo; and the Hub keeps the new place rather than pushing the old one back.

### Pending

- A solid still has no multi-select. `selMany` holds device ids and a shift-selected pile of projectors is a thing people build; there is no equivalent for the room.
- Moving a shape in 3D and then pressing BUILD on the pad will put it back where the drawing says. The pad is authoritative about the SHAPE; this is only about where it stands, and nothing yet reconciles the two.

## 24 August 2026 — A crowd of people, instead of a crowd of cards

### What changed

- **The audience is twenty low-poly figures now, not one silhouette on a card.** `crowd.glb` (Woman01–10, Man01–10) is welded, normalised to one unit tall with feet at y=0 and footprint centred, quantised to 16 bits and embedded in `scene-study-3d.html` as `CROWD_MESH` — 2,151 vertices and 4,281 triangles for the whole cast, in 52 KB of text. Which person somebody is comes from the same deterministic `audRand` as their position and height, so the same region produces the same crowd on every frame and every reload.
- **Black material**, with a little specular (roughness 0.62, metalness 0.05): pure matte black under a diffuse light shows no form at all, and a crowd that reads as one hole in the floor is not a ruler.
- One instanced draw **per figure**, not per person and not per region — twenty draws for a crowd of any size, in any number of blocks.
- `clearAudience` no longer disposes the geometry, only the material. The cast is decoded once and shared; disposing it with the meshes would have emptied the crowd for good the first time a region moved.
- A GHOST audience keeps its `--status-info` blue in RENDER. It is the only thing saying that crowd is a proposal from the Sketch Pad rather than a fact about the take.

### Why

A card is honest from the front and a paper cut-out from anywhere else, and this tool is orbited constantly: the moment you came round the side, a thousand people turned edge-on and the room lost the scale the crowd was there to give it.

Embedded rather than fetched from `glb/crowd.glb` for the same reason `STAGE_MESH` is embedded: this panel's standing claim is that you can open it on its own, from `file://`, and every feature is live. A relative fetch would make the crowd a thing that appears only when somebody remembers to run a web server.

### Files and components

- `scene-study-3d.html`

### Verification

20 assertions driven in a browser against the real Three.js panel: twenty named figures decode with the source file's Box helpers excluded; every figure is exactly one unit tall with feet at zero and centred on its own footprint; a 24 × 16 m region fills with 500+ people in at most twenty draws under a million triangles; two regions do not double the draw count; rebuilding three times gives the identical crowd (the shared-geometry disposal bug); black in the working view, in RENDER, and on the way back. Screenshots from inside the crowd, from the stage, and under the lit preview.

### Pending

- The figures' facing is one constant (`CROWD_FACE`), because all twenty share one rotation in the source. A crowd model whose figures were individually rotated would need a per-figure offset.
- Nobody is seated. Every region is a standing crowd; a seated audience would be a second cast.

## 24 August 2026 — CROP moved onto the canvas

### What changed

- **The timeline's CROP button arms the wall instead of opening a menu.** Once armed: drag on the wall to move the clip inside it, shift-drag to rotate, wheel to scale. Shift-wheel still dollies the camera, and a drag that starts anywhere other than the wall orbits exactly as before — cropping never takes the camera away.
- A bar over the picture carries live SCALE / ROTATE / MOVE, FILL, RESET and DONE, and names the clip and the surface it is going into. Esc or DONE disarms.
- The target wall is outlined in `--status-active`, in its own group on the scene rather than under `gHelpers`, so the outline survives RENDER — judging a crop under the lit preview is a reasonable thing to want.
- The drag reads the wall's OWN axes: the face's centre and its two half-axes are projected to screen and the 2×2 is solved, so the picture follows the hand on a wall that is turned away, tilted, or one facet of a curve, perspective included, with no depth arithmetic.
- `cropMenu` is still in the file and deliberately unbound.

### Why

Every button in the old menu was a guess followed by a look somewhere else, and the thing being adjusted was on the other side of the panel.

### Files and components

- `scene-study-3d.html`

### Verification

55 assertions driven in a browser: arming from the CTA and toggling it off again; wheel scales the clip while the camera stays put and shift-wheel dollies while the crop stays put; a drag on the wall moves the picture WITH the cursor (the expected sign is derived from the same projected basis the drag used, because on a facet of a curve "right" is not simply "right"); a drag off the wall orbits and leaves the crop alone; shift-drag rotates without panning; every bar button; the crop and its outline survive a scene push from the host; RENDER and CROP coexist.

### Pending

- Crop is still per clip, not per destination.
- There is still no letterbox/contain — `repeat` above 1 stretches edge pixels under `ClampToEdgeWrapping`.
- Rotation pulls in clamped edge pixels at the corners of a non-square crop.

## 24 August 2026 — Sketch Pad: stamps, cuts, and what BUILD actually builds

### What changed

**An LED stamp no longer locks a shape out.** Two separate causes, both about the pin a stamp leaves behind:

- The pin was picked up by the NEXT stamp. `hitStamp` ran before the tool switch, fired its drag branch and returned — so `case 'stamp'` was never reached and every further stamp near an earlier one did nothing. Pins now never intercept a tool whose job is "put this here"; handles were already excluded for exactly this reason and pins had been missed.
- A role pin was outranking the shape it labels. `marker: true` pins contribute nothing to the scene, and letting one win meant the stamped shape could not be selected or dragged from its body afterwards. A marker pin now loses to a solid underneath it. It is still grabbable everywhere it stands alone, and the eraser reaches it directly.

**A cut-out survives the view switch.** `cutGeometryFor` ran in the CURRENT page: `!isShadow` dropped every cutter not in the current projection, and `solidPtsHere` reprojected the shape's own outline — a plan footprint seen in elevation collapses onto the ground line, so its ring had no area and `outers` came back empty. The opening vanished from the drawing, and a BUILD made from Elevation sent a deck with no hole in it at all. The boolean is now settled in the space the shape and its cutter were DRAWN in, where both are real polygons, so it comes out the same from either view. `solidRecord` no longer converts the result back.

**You can see the stamp you are carrying.** An armed stamp draws as a puck under the cursor with its role glyph — a deck filled, a wall's face ticks, an LED wall's cabinets, the same marks the shape itself gets. The shape it would name lights up dashed underneath, and a caption says what the drop will do: "names this shape LED", "builds a 4 m cabinet run here", "that shape is built — UNLOCK it first".

**Built shapes go recessive and lock.**

- Dimmed to the meta ink with a fine dashed keyline and no vertex handles — handles on something that will not move are a lie about what the pointer can do. Not in `clean`: the rasterised PNG is evidence for a reader.
- A locked shape can be SELECTED — it has to be, or its own UNLOCK is unreachable — but not dragged, reshaped or restamped. Its row shows a BUILT chip and an UNLOCK button, with every control that would change it disabled. DELETE stays live: removing a built shape is explicit, the payload already handles it through `drop`, and blocking it would strand the shape behind a lock.
- **BUILD 3D sends only what is not already true.** It used to send every solid on the pad every time. A shape counts as new if the take has never seen its id or its geometry has changed since it was last sent. Pressing BUILD twice now says "already built — nothing has changed", and still re-locks, because LIVE may have carried an edit into the take while the hand was still moving.

### Files and components

- `sketchpad.html`

### Verification

45 assertions driven in a browser: a cut made in Plan still reports one hole in Elevation and still leaves the pad in the payload built from there; three stamps land in a row on the same shape; the shape is selected by a click in its own middle while a pin standing alone is still grabbable and still erasable; the carried glyph is drawn, differs over a shape from over empty paper, is absent with no stamp armed and is deterministic; a build locks every shape, a second build sends nothing, a locked shape refuses a drag and a restamp but still selects, UNLOCK returns it, an edit-and-rebuild sends one shape, and a new shape drawn afterwards is the only thing the next build sends.

### Pending

- Stroke ghosts (completed basic shapes that stay strokes in the drawing UI) are tracked by `built` but never render recessive — only `t === 'solid'` items lock.
- `built` is not part of the undo record, so undoing across a BUILD leaves the lock state ahead of the map.

## 24 August 2026 — RENDER: a lit preview that comes back

### What changed

- **The render key is actually lit.** `renderSpot` was created and pinned at intensity 0, so the mode added a black floor and ACES tone mapping and no light at all. It is now aimed and sized off the room it is lighting — position, cone, throw distance and shadow camera all derived from the venue's own stage — and its intensity is computed from the throw, because r155+ lights are physical and a number that reads as a key at 16 m is black at 40 m. It re-aims whenever the venue changes.
- The working rig (key, fill, hemisphere) drops to render levels from a table, and comes back to exactly the values it started with.
- **RENDER stopped eating the background.** It called `setBg('#000000')`, and `setBg` writes `bgHex` — which `pushView` sends to the host, which stores it on the take. So one orbit in RENDER turned every panel of that take black, permanently. The render black is now a look applied at the scene, and `bgHex` — the one that travels — is never touched.
- **RENDER survives a rebuild.** The audience and the LED walls are rebuilt from scratch on every push from the host, and a rebuild handed back working-view materials while the mode was still on. The crowd's pass moved into `syncAudience`; the LED walls turned out to have TWO writers — `applyRenderMaterials` and `routeMedia`, which runs later — so the LED half was removed and `routeMedia` is the single writer, asked to run again by the toggle.
- Library LED kit gets the render treatment too. The old pass traversed `gSolids` only, so a wall drawn on the pad glowed and the identical wall taken from the library stayed grey.
- Working colours are read off the material rather than guessed from a token, which is what stops a GHOST losing its `--status-info` blue on the way back.

### Files and components

- `scene-study-3d.html`

### Verification

49 assertions driven in a browser: the working rig at boot and restored exactly; the spot lit, aimed at the deck and re-aimed on a venue change; the background untouched by RENDER, unchanged after orbiting in RENDER, and restored on the way out; LED walls white and tone-mapping-exempt in RENDER and back to their own colours after; a scene push while RENDER is on leaves the mode intact and the rebuilt walls rendered; three round trips leave every value stable.

### Pending

- RENDER is not on the wire. `view` carries `bg`, `mesh` and `grid`; adding `render` would be additive and backwards-compatible, but the host would have to store it, so the mode is per panel for now.
- The toolbar is hidden in `?mode=pov`, so RENDER cannot be reached from a Camera POV panel — arguably the panel that wants it most.

## 21 August 2026 — Video on drawn LED walls, and cropping it

### What changed

- **A clip can be routed to an LED wall drawn in the Sketch Pad.** `routeMenu` already offered LED and projectors, but only from `S.devices` — library kit. An LED surface traced on the pad is a `solid` with `role: 'led'`, so the one surface somebody had just built by hand was the one surface missing from the list. Added `ledSolidTargets()` and `routeTargets()`, and taught the four places that resolve a destination to accept both: the route menu, the route label, the default route for a newly loaded clip, and the LOAD .MP4 button.
- **Dropping an .mp4 straight onto a drawn wall in the viewport works.** The drop handler tried `deviceIdAt` only; it now falls through to `solidIdAt` and accepts the hit if it is an LED solid.
- **The tiles are one surface, not 128 copies of the clip.** `buildLedSolid` gave every cabinet its own 0..1 UV square, and `THREE.ShapeGeometry` hands back raw model coordinates as UVs — so a routed clip would have repeated once per cabinet, or once per metre. Added `faceUVsFromBBox`, which maps UVs across the emitting face's bounding box. A faceted run in Plan carves `u0..u1` per facet from the run's total width, so a curve shows one continuous picture instead of the same picture N times.
- **Added CROP.** A per-clip crop — FILL (cover the face, lose the overflow) or stretch, plus zoom and pan — on a CROP button next to ROUTE on each timeline row. It is `offset`/`repeat` on the texture, so nothing re-encodes and there is no second copy of the video. `routeAspect()` reports the shape of whatever the clip is pointed at, kit or drawn, and `applyCrop()` fits the clip to it. The button lights when a crop is not the default.
- `buildLedSolid` now records `userData.ledFaces` and `userData.ledAspect`; `syncSolids` keeps a `solidObjects` map from solid id to built group, which is what lets `routeMedia` find a wall it drew.

### Why

Routing was the visible half of the gap and the UVs were the half that would have made routing look broken: a clip that arrived on the wall as 128 postage stamps is arguably worse than a clip that never arrived, because it looks like a rendering fault rather than a missing feature.

### Files and components

- `scene-study-3d.html`

### Verification

Driven in a browser against the real Three.js panel, with an LED solid injected over the bridge as a `scene` message and a marker video (red left edge, green right edge, yellow top band, frame number centred) synthesised in-page with `MediaRecorder` and installed through `mediaAsset`:

- The drawn wall appears in the route menu as `DRAWN LED · LED WALL`. Before this change the menu reported no surfaces at all, because the take had no LED kit.
- Routed and played, the wall shows ONE image across all 128 tiles: one red left edge, one green right edge, one top band, one frame number, with the cabinet seams drawn over it.
- CROP: FILL toggles off and on, zoom runs x1.00 → x1.95, pan shifts the visible region and crops the edge markers away, RESET returns to a filled full frame, and the button lights and un-lights with the state.
- Embedded JavaScript syntax checks pass.

### Pending

- **Thickness on a shape in Plan and Elevation.** Still not implemented.
- Crop is per clip, not per destination. A clip routed to two surfaces of different aspect would be cropped for whichever one was resolved last. Today a clip has exactly one `route`, so it cannot arise — worth remembering if routing ever becomes one-to-many.
- FILL and stretch are the two modes. There is no letterbox/contain: `repeat` above 1 stretches edge pixels under `ClampToEdgeWrapping` rather than adding bars, so contain would need geometry or a shader.
- Not verified inside the Hub, for the usual reason — the Hub resolves as a `data:` URL in the preview harness and its relative iframe sources do not load.

## 21 August 2026 — Sketch Pad booleans, one build CTA, aimed stamps

### What changed

**Cut-outs became a real boolean subtraction.**

- Option-drag now draws a red cutter anywhere on the pad. It no longer has to start inside a closed solid, and it no longer has to sit wholly inside one: every closed shape it OVERLAPS is cut by it.
- A cut that lands wholly inside a shape is an opening and the outline is untouched, so the arc fit survives. A cut that crosses the outline is a bite, and the outline becomes the boolean difference — the span the cut ate becomes straight, because a polygon has no radii.
- A cut straight across a shape splits it in two. The larger piece keeps the shape's id, the remainder leaves as a sibling with a `#2` suffix.
- One cutter cuts every shape it overlaps, not just the topmost.
- Added a polygon boolean (Greiner-Hormann) to `sketchpad.html`: `boolPoly`, `polysOverlap`, `polyRingArea`, plus `segsCross`, `onPolyEdge` and `polyInPoly`.

**Cuts are cumulative and nothing is baked.**

- Each Option-drag leaves a persistent red `cutout` item. The original fit is never mutated; the geometry that leaves the pad is derived from the fit minus every cutter that overlaps it (`cutGeometryFor`, `solidTakes`, `solidRecord`).
- Adding another red shape cuts further; deleting one gives the shape its piece back; dragging one off a shape reverts that cut live.
- Red cuts are ordinary objects now — selectable, movable, erasable via `hitSolid`.
- Cuts are no longer dragged along with a shape. They are independent objects that cut whatever they overlap, so moving a shape moves it out from under its openings.

**One build CTA, and no model round-trip.**

- Removed the MAKE 3D button from the Sketch Pad. BUILD 3D is the only CTA.
- BUILD 3D now only builds: the `interpret()` half that sent the ambiguous remainder (loose strokes, the note, unstamped shapes) to be read back as a plan is no longer called. The pad stays live instead of parking in plan review, and anything drawn afterwards ghosts until it is built in turn.
- `interpret()` and `make3d()` are still in the file and deliberately unbound, so either capability is a re-attached listener rather than an archaeology exercise.

**Stamps are aimed, and every stamp leaves a pin.**

- Fixed: after an LED stamp, every other role stamp stopped working. `dropStamp` had a fallback that sent the role to whatever was SELECTED when the drop landed on empty paper. The LED stamp builds a shape and selects it, so from then on that fallback swallowed every WALL, STAGE and SCREEN stamp and quietly re-labelled the LED shape. The fallback is gone: a stamp acts where it was dropped and is never a command about the selection.
- Every stamp now leaves a labelled pin at the drop point, role stamps included. Pins from role stamps carry `marker: true` and are excluded from `stampPreviewOps`, so labelling a shape adds nothing to the scene.

**Cursor and Option feedback.**

- The Option cursor is a white dash — the crosshair with the vertical stroke removed — with a dark under-stroke so it reads on light paper. Its fallback was `not-allowed`, which told the person the gesture was forbidden at the exact moment it became available; it is now `crosshair`.
- The pad is usually in an iframe, where a key event goes where focus is rather than where the pointer is, so the Option keydown was being delivered to the Hub. The pad now takes focus on `pointerenter` and also reads `altKey` off every pointer event.

### Why

Three of these were features that could not be reached rather than features that were wrong:

- The cut-out gesture was **unreachable**. A cut had to start inside a closed solid, and that is the exact condition that made the "drag the whole solid" branch in `pointerdown` fire and return first. Every Option-drag was read as "pick this solid up and move it" — no red line, no cut, and no flash message either, which is why it read as absent.
- Baking the cut into the outline cost two things somebody notices: the red shape vanished, so there was no record on the pad of where the opening lived, and the cut could only be taken back by undo.
- BUILD 3D's second half asked a model to read a drawing that already said what it was.

### Files and components

- `sketchpad.html`

### Verification

- 17 polygon-boolean unit tests, run against the functions extracted from the shipped file: edge bite, corner bite, split, swallowed, disjoint, flush shared edge, concave subject, 180-vertex tessellated circle, and the axis-aligned degeneracy the Rectangle tool produces constantly.
- 11 containment tests for the inside-vs-crossing decision.
- Gestures driven in a browser with exact areas: 90000 → 80000 for a 100×100 overlap; one cutter across two shapes took precisely 4000 from each; a split gave 39000 + 39000; three cumulative cuts went 5625 → 5469 → 5313 → 5156 with the fit still reporting 4 verts.
- BUILD 3D: `busy` stays false, the built shape reports `built=true` and a shape drawn afterwards reports `built=false`.
- Stamps: with an LED shape selected, a STAGE stamp dropped far away leaves the LED role unchanged and pins where it was clicked; `stampPreviewOps` returns ops for PROJ and CAM only.
- Embedded JavaScript syntax checks pass for `sketchpad.html`, `refboard.html`, `scene-study-3d.html` and `HUB_5.6.html`.

### Two bugs worth remembering

- Greiner-Hormann for A−B inverts the **subject's** entry flags. Inverting the cutter's is the thing that looks right, and it silently returns the INTERSECTION — the shape you meant to remove rather than the shape you meant to keep. Both are plausible polygons, so it fails quietly.
- A split returned its two halves wound opposite ways, and the caller told outer-piece from hole by the sign of the area, so one half was discarded. The first test suite passed this: it summed ABSOLUTE areas and counted rings, so two rings totalling the right area looked correct while one was about to be dropped. The regression test now asserts matching winding.
- The clipper cannot survive exact collinearity and the Rectangle tool makes exact axis-aligned edges, so the cutter is nudged ~2e-4 px first — deterministic, four orders below the 0.5 px tessellation.

### Pending

- **Video track assignment to LED surfaces drawn in the Sketch Pad.** `routeMenu` in `scene-study-3d.html` already offers both LED and projectors, but only from `S.devices` (library kit). An LED surface drawn on the pad is a `solid` with `role: 'led'`, and `buildLedSolid` never sets the `userData.ledPanel` that `routeMedia` textures — so sketch-drawn LED cannot receive a clip. Not implemented.
- **Thickness on a shape in Plan and Elevation.** Not implemented.
- Browser interaction check of the Sketch Pad inside the Hub. The Hub cannot be loaded from the preview harness — it resolves as a `data:` URL, so its relative iframe sources (`sketchpad.html?b=…`) do not resolve. Everything above was verified against `sketchpad.html` standalone.
- The split case now sends a second solid record with a `#2` id. Nothing in `scene-study-3d.html` was changed, and it keys by id, but that path is unverified in the Hub.
- Openings no longer move with their shape. This is a deliberate behaviour change and the most likely thing to want reverted.

## 21 August 2026 — Local image interpretation

### What changed

- Added a local interpretation engine using SmolVLM2 in LM Studio/local Python tooling.
- Kept image interpretation separate from measurement: the model describes likely roles, while the deterministic tracer remains the only authority for dimensions.
- Added clear health states so the interface says whether local vision, tracer-only mode, or no vision is active.

### Why

The prototype needs to understand sketches and reference images locally without allowing a vision model to invent measured geometry.

### Files and components

- `agent/local.py`
- `agent/vision.py`
- `agent/serve.py`
- `agent/requirements.txt`
- `agent/README.md`
- `VISION.md`
- Production Hub agent/vision status UI

### Verification

- Existing local engine imports and health reporting were inspected.
- The Production Hub still sends both the raster image and deterministic vector record.

### Pending

- Complete an end-to-end live Production Hub interpretation check after the TRELLIS installation finishes.

## 21 August 2026 — TRELLIS-Silicon image-to-3D service

### What changed

- Cloned TRELLIS-Silicon into `agent/vendor/trellis-silicon` as a separate Apple-Silicon service.
- Verified authenticated access to all gated model repositories: DINOv3, RMBG-2.0, and TRELLIS.2-4B.
- Started the pinned, isolated installation, including native Metal backends.
- Added a local HTTP service contract that accepts image bytes and returns a GLB. It serialises work to one MPS generation at a time and reports useful health and output statistics.

### Why

SmolVLM should interpret an image, not manufacture a detailed mesh. TRELLIS is a separate, explicit conversion step whose GLB output can be handed to Scene Study.

### Files and components

- `agent/vendor/trellis-silicon/`
- `agent/vendor/trellis-silicon/service.py`
- `agent/vendor/trellis-silicon/pyproject.toml`
- Production Hub GLB bridge (in progress)

### Verification

- Hugging Face access returned `ACCESS_OK` for all three required repositories.
- Machine prerequisites confirmed: Apple Silicon, Python 3.11, Metal compiler, and sufficient free disk space.

### Pending

- Finish dependency installation and first model download.
- Start the service, run its health check, generate a real GLB, and load that GLB in Scene Study.
- Finish the explicit “Make 3D” controls in the Sketch Pad and Reference Board.

## 21 August 2026 — Sketch Pad corrections and modelling tools

### Requested work

- Preserve visible outlines and clear selection after applying role stamps; ensure a stamp uses the shape that was actually clicked rather than stale selection.
- Add Option-drag negative openings for Rectangle, Ellipse, and freeform Trace/Pen shapes.
- Draw negative geometry with a persistent red keyline; keep it visible above its parent solid.
- Make cut-outs discoverable, undoable, persistent, and present in Scene Study geometry. If no valid parent lies underneath, explain why instead of creating stray geometry.
- Add “Square Up / Fit to Rectangle” using the closest oriented rectangle while preserving centre, footprint, height, role, source linkage, and styling.
- Recognise handwritten CAM (including numbers), LED, PROJ, TRACK, STAGE, WALL, SCREEN, AUDIENCE, AUD, and SEATING labels as confirmable suggestions.

### Work completed so far

- Implemented backend recognition and nearest-region association for the requested handwritten label families.
- Suggestions carry their OCR source, confidence, target shape, and accept/edit/reassign/reject actions.
- Suggestions do not alter traced geometry or become normal stamps without confirmation.
- Confirmed the existing stable source-ID replacement path is sufficient for Square Up to update Scene Study immediately without losing the solid's host identity.

### Files and components

- `agent/model.py`
- `agent/vision.py`
- `agent/agent.py`
- `agent/stub.py`
- `agent/test_semantic_labels.py`
- `sketchpad.html` (stamp, cut-out, red-keyline, Square Up work in progress)
- `scene-study-3d.html` (cut-out rendering integration pending verification)

### Verification

- Semantic-label test suite: three tests passed.
- Changed Python modules compile successfully.
- Square Up message flow was traced from Sketch Pad through stable `srcId` replacement to Scene Study’s reactive rebuild.

### Pending

- Finish and interactively verify the Sketch Pad UI work.
- Verify negative openings in both 2D and 3D, including undo and persistence.
- Add the suggestion review controls in the interface.

## 21 August 2026 — Sketch Pad implementation completed

### What changed

- Fixed role stamps so the shape under the click wins over an older selection, and re-draws the ordinary outline above LED/wall decoration.
- Added Option-drag negative openings for Rectangle, Ellipse, Trace, and Pen.
- Negative openings have red live and committed keylines, move with their parent, survive the existing sketch history/state, and are undoable.
- While Option is held over Rectangle, Ellipse, Trace, or Pen, the canvas cursor changes immediately to a red circled minus (including hover and drag) and returns to the normal cursor on release or window blur.
- Invalid or uncontained cut-outs now show a useful message and create nothing.
- Added an undoable `SQUARE UP` action using a closest oriented rectangle while retaining role, dimensions, styling, and source identity.
- Added `MAKE 3D` to Sketch Pad and Reference Board.
- Preserved cut-out `holes` through the Production Hub boundary and Scene Study bridge.
- Scene Study now sends holes to Three.js extrusion paths for stage/front-wall geometry and excludes hole cells from shaped front-view LED cabinet layouts.

### Why

These changes keep 2D editing trustworthy: role decoration must not erase geometry, a void must read differently from a solid, and corrective modelling actions must update the same object rather than create disconnected replacements.

### Files and components

- `sketchpad.html`
- `refboard.html`
- `production-hub-v5.5.html`
- `scene-study-3d.html`

### Verification

- Embedded JavaScript syntax checks pass for all four HTML files.
- The payload and bridge were traced end to end: local hole vertices are converted to take units, sanitised, cloned as plain data, and consumed by Scene Study mesh builders.
- Square Up reuses stable `srcId` replacement, so the existing solid ID and reactive 3D update path are preserved.

### Pending

- Browser interaction check of the complete Sketch Pad workflow.
- A real TRELLIS conversion is currently downloading/loading model weights.
- The optional fast Metal texture baker remains unavailable until Apple’s separate Metal Toolchain component is installed; the supported KD-tree baker is active meanwhile.

## 25 August 2026 — Confirmed stage height in the Elevation view

### Requested work

- A stage height confirmed in the Scene Study must be visible in the Sketch Pad's Elevation view.
- Switching between Plan and Elevation must not return the 3D stage to its original height.

### What changed

- `solidPtsHere` no longer projects a plan-drawn solid onto the ground line when the pad is in Elevation. A new `elevationProfile` draws it as what it is from the front: a band its own width, standing from `baseM` to `baseM + hM`. Width is the outline's X extent, which is what a draughtsman means by the elevation of a deck; a concave footprint's notch is not pretended to.
- `drawSolid` treats that band as a closed face regardless of whether the footprint was closed, so a plan-drawn run also reads as a solid from the front. LED cabinet decoration is skipped on a profile — the grid belongs to the plan and would collapse onto the ground under the band.
- The solid payload now carries `hFree`: whether the height is a stated fact or the pad admitting it cannot know.
- `solidHeight` (a height arriving back from the room) now refreshes the pad's `built` keys and re-locks. The pad used to keep describing the ankle-high deck the shape used to be, so the next gesture — changing projection included — counted it as changed and re-sent it.
- Hub: a solid rebuilt from the pad keeps two fields the pad has no opinion about — a height set in the room (`hSet`, unless the pad states `hFree`), and rotation. Rebuilding replaced the solid whole, so a deck pulled to 2 m dropped back to its default and a deck turned to face the audience snapped back to 0°.

### Why

From directly above there is nothing to judge a height against, so the height is chosen in 3D — which makes the take the only holder of that answer whenever the Sketch Pad is not open to hear it. The pad's next post must not overrule it by default, and the Elevation view is the one place that number should be readable on paper.

### Files and components

- `sketchpad.html` — `solidPtsHere`, `elevationProfile`, `drawSolid`, `solidRecord`, `solidHeight`
- `HUB_5.8.html` — `agentApplyOp` case `solid`, `moveSolid`

### Verification

- Browser round trip through the Production Hub with the local agent: traced a 6x4 m deck in Plan, BUILD 3D, pulled the height to 4.70 m in the Scene Study and pressed DONE, then switched Plan/Elevation repeatedly. The deck held 4.70 m and the pad sent nothing on the switch (previously it re-applied the shape each time).
- Elevation view checked with a plan deck (8x5 m, H 1.80 m, and again at base 1 m / H 4 m), a plan LED run and an elevation-drawn wall: bands stand at the right height on the ground line, the elevation-drawn wall is unaffected, and the Plan view is unchanged.
- Height authority checked both ways: a pad that never heard the pull (`hFree` false) no longer resets the take's 4.70 m; a pad that states 0.90 m deliberately still wins.
- Rotation set to 30 degrees in 3D survives a pad rebuild.
- Both files pass `node --check` on their embedded scripts.

### Pending

- The reverse collapse is untouched: an elevation-drawn solid still reads as a line in Plan rather than a band of its own depth.
- A solid moved in 3D still snaps back to the pad's position on the next rebuild — `at` remains the pad's to state.

## 25 August 2026 — The height is an object in the Elevation, not a picture of one

### Requested work

- A height okayed in the Scene Study stays fixed there and is recorded and synced in the Sketch Pad.
- The stage's rectangle in Elevation must read as BLOCKED once the height is okayed, and be unlocked before it can change, like every other built shape.
- The height must be transformable in the Sketch Pad's Elevation too, moving the Scene Study as it is dragged, until BUILD makes it final.

### What changed

- A plan solid seen in Elevation is no longer a shadow. `hasProfile` names the case and `isUntouchableHere` replaces the blanket `isShadow` guard in `hitSolid`, `hitSolidNear`, `hitShapeForStamp` and `lockedAt`, so the band answers for itself: it selects, it opens the solid row, and it reports its own lock.
- Locked, it draws with the same recessive ink and dashed keyline as any other built shape, and offers no handle. UNLOCK is reached the same way it is everywhere else.
- Unlocked, the top edge is a handle — `hitHeightHandle` / `dragHeight`, alongside the vertex and apex handles in the same pointer branch. Dragging it sets `hM`, marks the height as deliberately stated (`hFree`), and calls `liveNow()`, so the Scene Study follows the pull. BUILD 3D re-locks.
- The body of a profile selects but does not drag: the outline belongs to the Plan, and a footprint pushed sideways through a view that cannot see where it lands is not an edit anybody asked for. The footer says where the outline is edited instead.
- The 0.5 m cap on the `H` field is lifted while the Elevation is open. The cap is about what a view can judge, not about the field, and somebody typing a height while looking at the elevation is making the same claim as somebody pulling the top edge.

### Why

The cap exists because a plan cannot judge height. The Elevation can — that is what it is for — so it should carry the same authority as the 3D, and the same lock discipline as every other shape on the pad. Treating the band as a picture rather than an object was what made the height feel like something that happened to the drawing rather than something stated in it.

### Files and components

- `sketchpad.html` — `hasProfile`, `isUntouchableHere`, `heightHandleAt`, `hitHeightHandle`, `dragHeight`, `drawSolid`, `paintCursor`, pointer down/move/up, the `sol-h` handler

### Verification

- Browser round trip through the Production Hub with the local agent: traced a deck in Plan, BUILD 3D, switched to Elevation — band drawn blocked, no handle, `H` field disabled. UNLOCK, pulled the top edge: the pad read 3.00 m and the Scene Study read 3.00 m while the drag was live. BUILD 3D re-locked it, the handle stopped answering and the field went dead again.
- The reverse still holds: pulling to 5.50 m in the room updated the band (220 px at 40 px/m), left it locked, left nothing pending, and survived switching Plan/Elevation.
- Checked that a drawing tool still puts ink down over the band rather than grabbing the handle — same rule the vertex handles have always had.
- `node --check` passes on the embedded script.

### Pending

- A cut drawn in Elevation still does not cut a plan solid, which is correct — but there is no way yet to cut a deck's profile from the front, and no message saying so.
- `S.groundLine` is fixed at the box height it was first measured at, so resizing the panel leaves the ground line off-screen. Pre-existing, and it makes the Elevation unreadable until the view is reset.

## 26 August 2026 — The approved height, written down; and BUILD 3D for one object

### Requested work

- Represent the height established and approved for the stage in the Sketch Pad's Elevation.
- BUILD 3D must work after just one object has been drawn on the pad.

### What changed — representing the height

- The profile carries a **dimension**: witness lines, arrows, the metres knocked out of the line, and one word saying which it is — `BUILT` when the shape is locked, `PROPOSED` while it is in hand and drawn in the active accent. A band the right size is not the same as a height that has been stated, and a reader has to be able to see the number and whether anybody agreed to it.
- **A height now makes a drawing an object.** A rectangle from the shape tools is a `stroke` — buildable, but with no role, no lock and nowhere to keep a height — so a number approved in the room had nothing on this side to land on: the pad went on believing the default and the Elevation had no height to draw. `solidHeight` now promotes a matching stroke through `convertStroke` (same source id, so the take's object is replaced rather than duplicated) and then applies the height. This was the case that made the whole feature invisible for the shapes most drawings are made of.
- An off-paper ground line is corrected on resize, once it has actually fallen outside the canvas. It is pinned on purpose — moving it changes what every height drawn against it means — but it was pinned to whatever the panel measured the first time the Elevation was opened, so a panel later made shorter put the ground, and everything standing on it, below the bottom edge.
- A band taller than what is on screen is reported in the footer with its height and `press F to fit`, once per change and measured against the viewport rather than the canvas. Silence there looks exactly like a height that was never recorded.

### What changed — BUILD 3D

- The stroke-commit path never moved `S.solidRev`, and that counter is the whole of what greys the button out. One rectangle on an empty pad therefore left BUILD 3D dead: there was something to build and the only thing that says so had not been told.
- `strokeGhostsOut` returned nothing whenever LIVE was off. Right for the ghost lane, wrong for BUILD — its other caller — so with LIVE off a drawn rectangle was invisible to the button, and pressing it reported nothing to build while the thing to build was on the paper. The lane decides what it previews, not what exists.
- The button's title counted solids only, so it read "Build 0 shapes" over a pad with a rectangle on it. It counts strokes too.

### Files and components

- `sketchpad.html` — `drawHeightDim`, `drawSolid`, `draw`, `resize`, `strokeGhostsOut`, `convertStroke`, `solidHeight`, the stroke-commit branch of `pointerup`, `status`

### Verification

- Browser, standalone and through the Production Hub with the local agent.
- One rectangle drawn with the RECT tool, LIVE on: BUILD 3D lights, title reads "Build 1 shape into the scene", pressing it puts a 6x4 m deck in the Scene Study and the button goes quiet. Same with LIVE off — the payload was checked in the dev log.
- Height approved at 3.10 m in the room on that rectangle: the pad's stroke became a locked `stage` solid at 3.10 m with the same source id, the Elevation drew a 124 px band at 40 px/m with `BUILT` on the dimension, the height field was disabled and no handle answered. Plan/Elevation switching left the room at 3.10 m.
- Unlocked, the dimension turns to the accent and reads `PROPOSED`, and the value tracks the top-edge drag.
- An 18 m deck in a short panel reported "taller than the paper · press F to fit"; FIT brought it in and the notice cleared.
- `node --check` passes on the embedded script.

### Pending

- A cut drawn in Elevation still does not reach a plan solid's profile.
- Promotion on height uses role `stage` (`wall` in a front view) because the room says how tall a thing is, not what it is for. A stroke that was going to be named LED has to be re-named after a height is approved.

## 26 August 2026 — The drawing follows the room

### Requested work

- Anything moved or resized in the Scene Study after it has been built must show in the Sketch Pad at its new size and position, in Plan and in Elevation.

### What changed

- The bridge only ever sent the HEIGHT back. `moveSolid` now also fans out a `solidPlaced` message — the shape's centre in take units and its angle in degrees, the same two fields the pad writes — so the drawing stops describing a scene that has moved on, and stops putting the shape back where the paper said on the next BUILD.
- The pad's handler is the exact inverse of `solidRecord`: that function is the only thing that decides what a page pixel means out there, so this reads its arithmetic backwards rather than inventing its own. A floor shape takes X and depth on the page and its `at[1]` as `baseM`, which is what the Elevation draws it standing at; a front shape takes X and height on the page.
- **A front page has no depth axis**, so a front-drawn shape's depth is not in its outline and never can be. It used to leave as a flat 0 — a wall pushed upstage in the room was pulled back to the setting line by the pad's next post. It is carried on the item now (`depthM`), stated only by the room, and `worldOf` is the one place that puts it back when the shape is seen from above.
- **Rotation has one home at a time.** The pad has no rotation field — its own rotate handle turns the vertices — so a turn from the room is baked into the geometry the same way, and the record reports which turn was absorbed (`rotTaken`). If that matches the angle the take is holding, the take's copy has become a duplicate of something now in the outline and goes to zero; if they disagree the pad is describing a stale turn — it was not open when this one happened — and the take keeps its own. Not applied to a front-drawn shape: `rot` is about the vertical, which is a change to a plan angle, and turning a front outline would tilt a wall that is still standing upright.
- `solidFor` and `agreeWithScene` factored out of the height handler, since every message from the room needs the same two things: resolve the shape (promoting a stroke, because saying where a thing is or how tall it is IS saying it is a thing), then agree with the scene so the pad does not count the shape as changed and rebuild something already right.

### Why

The bridge's own comment said a shape nudged in 3D and a shape nudged on the pad are one fact arriving by two doors. Only one door was open.

### Files and components

- `HUB_5.8.html` — `case 'moveSolid'` fan-out, `case 'solid'` rotation reconciliation
- `sketchpad.html` — `IN.solidPlaced`, `solidFor`, `agreeWithScene`, `spinSolid`, `worldOf`, `solidPtsHere`, `solidRecord`

### Verification

- Browser round trip through the Production Hub with the local agent.
- A 6x4 m deck built from the pad, then moved in the room to `[40, 15, 30]`: the pad's centre went 600,350 → 760,470 (4 m right, 3 m upstage at 40 px/m), `baseM` became 1.5, and the record read back `[40, 15, 30]` exactly — the inverse is exact, not approximate.
- Raised to 1.2 m and moved 6 m right: the Elevation band moved 240 px across and its foot lifted to 48 px above the ground line, both correct at 40 px/m.
- A front-drawn wall pushed 8 m upstage: its line in Plan moved 320 px off the setting line and the record read back `[0, 19.63, 80]`.
- Turned 30 degrees in the room: the pad baked it, reported `rotTaken: 30`, and on the pad's next post the take's own `rot` went to 0 — the turn lives once, in the geometry, with no double rotation.
- The stale case checked deliberately by making the pad deaf to `solidPlaced` (what a closed sketch panel is), turning 45 degrees in the room, then having the pad re-send: `rotTaken: 0` against a take holding 45, and the take kept 45.
- One message carrying both a height and a move, on a shape still only a stroke: promoted to a locked stage solid at 2.80 m, `at` round-tripping `[10, 0, 20]`, a 112 px band in Elevation, nothing pending, and the room still reading 2.80 m after switching views three times.
- Earlier work re-checked in the same session: one rectangle still lights BUILD 3D and builds.
- `node --check` passes on both files.

### Pending

- A shape DELETED in the Scene Study is not removed from the drawing, and the pad will not notice the divergence. Deleting somebody's drawing because the scene dropped a solid is not obviously right, so it is left alone deliberately.
- A front-drawn shape still reads in Plan as a line at its depth rather than a band of its thickness. Now that depth is carried, the band is the obvious next step.
- Devices and blocks moved in 3D still do not travel back to the pad's anchors; only solids do.

## 26 August 2026 — SCALE in the gizmo

### Requested work

- Add a scaling function to the Scene Study's gizmo.

### What changed

- A third gizmo mode, `scale`, beside move and rotate — same toggle rules, same both-on-at-once behaviour, `R` on the keyboard.
- **Only on a drawn shape.** A projector is a real model of a real product and stretching it is a lie about what turns up on site; a deck, a wall or a screen is a shape somebody drew, and trying a size in the room is exactly what the room is for. The button goes dead when the selection is not a shape, and its tooltip says why.
- **Only in the plane of the shape's own outline** — X and Z for a floor deck, X and Y for a front wall. The third axis is always a named field with its own control: a deck's height is what the yellow extrude arrow pulls, a wall's is the depth it is swept through. A scale handle there would be a second control for one number and the two would disagree the moment either was used.
- Two axis cubes plus a corner cube on the diagonal that scales both — which is the one that keeps a fitted arc an arc. The cubes sit outside the arrows and the rotate rings, because `handleAt` takes the first thing the ray hits and a cube sharing a radius with a ring's hit tube is a coin toss between resizing a deck and turning it. The corner is deliberately NOT at the origin: move puts its free-drag dot there, and from most camera angles an axis handle's hit box passes in front of the centre.
- A scale is a RATIO, so what the drag captures is a reach — how far along the axis the pointer was when it grabbed — and the factor is how far it is now over how far it was. A delta cannot express it: the same 30 cm of travel has to mean a lot on a 1 m shape and very little on a 20 m one.
- The take holds it as a TRANSFORM (`scale`), the way it already holds `rot`, rather than having the Scene Study rewrite vertices. The Sketch Pad holds the fit and is the only surface that knows whether a non-uniform stretch may keep an arc an arc, so it is the only one entitled to rewrite the outline. The room records the ask, shows it, and tells the paper.
- The pad absorbs it through `stretchSolid`, which follows `scaleItem`'s rules for the same geometric reasons — a non-uniform stretch re-runs the fitter over the rescaled ink; a shape whose arcs were moved by hand is held proportional and the footer says why — and reports `scaleTaken`, reconciled exactly like `rotTaken`.
- The readout prints the footprint in METRES, not the factor, highlighted while the shape is standing at a scale the paper has not absorbed yet. Nobody works in ratios.
- The standalone debug handle gained `gizHandles()`, `gizHitAt()` and the gizmo itself, so a handle can be aimed at from a test instead of guessed at from a screenshot. It measures against the same box `pointerRay` does — the canvas and the element the pointer is measured in are not the same box, and a pixel that answers a different question is worse than no pixel.

### Bug found by driving it for real

`dragPoint` had no branch for the new handle, so a scale cube fell through to the plane branch, which returns a point IN the plane the axis is normal to. The distance along the axis therefore came out as exactly zero, the reach was zero, and the drag refused to start at all — silently, because a gizmo handle that declines hands the press to the camera and the view just orbits. Only a real drag surfaces that; the handles were drawn perfectly and hit-tested correctly the whole time.

### Files and components

- `scene-study-3d.html` — `i-scale`, `b-scale`, `gizModes`, `gizScalePlane`, `buildGizmo`, `dragPoint`, `scaleReach`, `dragMove`, `dragEnd`, `sendSolidScale`, `syncSolids`, `updateReadout`, `window.SS`
- `HUB_5.8.html` — `case 'scaleSolid'`, `sanitiseSolid`, `case 'solid'` reconciliation
- `sketchpad.html` — `IN.solidScaled`, `stretchSolid`, `solidRecord`

### Verification

- Standalone Scene Study, driven through its own pointer handlers at pixels read off the gizmo: all three handles hit-test as themselves, and doubling the reach on the X cube took a 6 m deck to 11.68 m live, committed `[1.9462, 1, 1]`, and printed the new footprint in the readout.
- Through the Production Hub with the local agent: a gizmo-equivalent `[1.5, 1, 2]` took a 6 x 4 m deck to 9 x 8 m on the pad — correct in Plan, and a 9 m band in Elevation — while it stayed locked with nothing pending.
- Reconciliation both ways: with the pad having absorbed the size, its next post returned the take's transform to `[1, 1, 1]`, so the size lives once, in the geometry, with no double scaling. With the pad deliberately made deaf, a `[1.25, 1, 1.25]` asked for in the room was KEPT by the take against a pad reporting a stale `scaleTaken`, and the room went on showing the size that was asked for.
- `node --check` passes on all three files.

### Pending

- Scale is footprint-only by design, so there is no gizmo path to a deck's height other than the extrude arrow. That is deliberate but worth revisiting if anyone reaches for a Y cube.
- An imported GLB still resizes only through the numeric field in its readout, not the gizmo.
- A non-uniform stretch of a shape with hand-edited arcs is held proportional. Correct, but the only place it says so is a footer flash on the pad, which the person doing the dragging in 3D is not looking at.

## 26 August 2026 — Rotation, in both views, for both kinds of shape

### Requested work

- Sync all rotations of shapes in the Sketch Pad, in Plan and in Elevation.

### What changed

A turn about the vertical lands in one of two places, and which one is not a preference — it is what the page the shape was drawn on is able to say.

- **A FLOOR outline is drawn in the plane the turn happens in**, so the turn IS the drawing. It is baked into the vertices, the same thing the pad's own rotate handle does, and `rotBaked` says how much is in there so a repeat of the same angle cannot turn it twice. This already worked in Plan; what was not obvious is that Elevation was already right too — `elevationProfile` takes the X extent of the turned footprint, so the band narrows or widens by exactly the foreshortening a turned deck has.
- **A FRONT outline is drawn in a plane the turn is NOT in.** This was previously skipped altogether, with a comment explaining that baking would tilt a wall that is standing perfectly upright. True, but the conclusion was wrong: the answer is not to drop the turn, it is to carry it (`yawDeg`) and let each view show what it can honestly show.
  - **Plan**: the footprint swings. Every point of a front outline is at one depth, so from above the shape is a line — and a line is exactly the thing a turn about the vertical is visible on. `yawWorld` turns those world points about the vertical through the shape's own centre. Before this, a wall swung 40° in the room went on lying flat across the plan, which is the one view that could have shown it.
  - **Elevation**: the face foreshortens. In its own view the outline is still drawn as drawn — it is the drawing, and it stays the thing you edit — but a dashed silhouette scaled by cos of the turn is drawn over it, labelled SEEN FROM THE FRONT, and the caption names the angle. An elevation that showed a swung wall at full width would be the one view lying about the one thing it is for.
- On the wire, a front shape STATES its `rot`, because for these shapes the pad has a rotation field and is the author of it. The hub's reconciliation is now checked in an order that says so: a stated angle wins; only when nothing is stated does the question of who holds the turn arise, and then the `rotTaken` bargain settles it as before.

### Files and components

- `sketchpad.html` — `IN.solidPlaced`, `solidPtsHere`, `yawWorld`, `drawSolid`, `drawYawGhost`, `solidTitle`, `solidRecord`
- `HUB_5.8.html` — `case 'solid'` rotation reconciliation, reordered

### Verification

- Browser round trip through the Production Hub with the local agent.
- FLOOR: a 6 x 4 m deck turned 30° in the room bakes to a plan span of 7.20 x 6.46 m (6cos30+4sin30 and 6sin30+4cos30, both exact) and an Elevation band of 7.20 m. The pad's next post returned the take's own `rot` to 0, so the turn lives once, in the geometry, and the deck in the room did not turn twice.
- FRONT: an 8 m wall turned 40° gives a plan footprint spanning 6.13 m across and 5.14 m deep — 8cos40 and 8sin40 — where before it stayed a flat horizontal line. Elevation draws the true 8 m outline with a dashed 6.13 m silhouette inside it and the caption reads `40° IN PLAN`. The record states `rot: 40`, and the take kept 40 rather than zeroing it, because the pad is the author for these shapes.
- `node --check` passes on both files.

### Pending

- The pad's own rotate handle on a FRONT-drawn shape turns the outline in the front plane — a tilt, not a yaw — and the take has no field for a tilt, so that rotation does not reach the room at all. Pre-existing, and now the more visible of the two gaps.
- `yawDeg` can only be set from the room. There is no way to type an angle for a wall on the pad, which is the obvious next control now that the drawing can show one.

## 26 August 2026 — A person is an object you can select

### Requested work

- Selecting a solo person should not live in the Import .glb menu. Selecting the person object — in the Sketch Pad or in the Scene Study — should enable the position, rotation and scale gizmo commands.

### The actual cause

`addSolo` never set `holder.userData.objectId`, and `objectHitAt` climbs from the hit mesh until it finds exactly that. A solo figure was therefore invisible to every raycast in the tool: clicking one did nothing at all. That is why picking a person out of a menu looked like the natural place for it — it WAS the only place, because the obvious way did not work. Imported .glb objects have always been tagged; this path simply forgot to.

### What changed

- `addSolo` tags its holder, so a person is pickable like anything else in the room.
- The list of already-imported objects is gone from the Import .glb menu. That menu is about importing; picking out somebody already standing in the scene is not an import, and putting it there said the opposite of what the room offers.
- A stamped person is pickable even though they are a ghost. This file already argues why they are drawn as the figure itself rather than a cheaper preview — there is nothing provisional about where somebody is standing — and the same reasoning makes them a pick target. Other ghosts stay unpickable. Without the exception a person could be selected from the paper and not by clicking them, which is two rules for one object.
- Selecting a PERSON stamp in the Sketch Pad selects the figure, and clicking the figure selects the stamp. Shapes travel by the id of their trace; a person travels by `personGhostId`, which is what the 3D keys them on and what the take records as their source, assigned on first use from either side so the two can never name the same person differently. The hub now forwards `srcId` to the 3D as well — it used to drop it, harmlessly while only shapes were selectable, because the take's own solid id said everything. A person has no take solid.
- SCALE now applies to an imported object, a person included: ONE corner handle, uniform in all three axes. A drawn shape has an outline with two axes on its own page and gets a cube each; an object is a mesh whose size is one number — the longest side in metres, which `setObjectSize` reads a single factor back off — so two handles writing to one number would be two handles that disagree. Kit is still not scalable: a model is the size the product is.
- A person moved, turned or resized in the room stops being re-placed from their stamp on the pad's next push (`rec.placed`), the same rule `facePerson`'s `turned` already applied to facing. The stamp still decides whether they exist — withdraw it and they go.

### Files and components

- `scene-study-3d.html` — `addSolo`, `objectHitAt`, `menuItems('object')`, `updateGizmo`, `buildGizmo`, `dragMove`, `dragEnd`, `handSized`, `syncPeople`, `personFor`, `personSrcId`, `IN.selectSolid`, `pickAt`
- `HUB_5.8.html` — `fanOutSolidSelection`
- `sketchpad.html` — `announceSelection`, `personGhostId`, `stampPreviewOps`

### Verification

- Standalone Scene Study: clicking a stamped person now selects them — readout `PERSON 1 imported · 0.00 · 1.40 · 0.00 m · 0.61 × 1.78 × 0.62 m` — and the SCALE button goes live. Before the fix the same click selected nothing.
- With all three modes on, a person offers three move axes, three planes, the free dot, one yaw ring and one uniform scale corner. Dragging the corner took them from 0.61 x 1.78 x 0.62 m to 0.89 x 2.58 x 0.91 m — all three axes by one factor — and set `placed`.
- Through the Production Hub: stamping PERSON on the pad and selecting the stamp selects the figure in the 3D, with all three transform buttons on and enabled.
- The Import .glb menu now reads only `+ ONE PERSON`, `+ IMPORT .GLB OBJECT …`, `IMPORT AS THE VENUE …` with a person standing in the scene.
- Re-checked that a drawn shape still gets its two axis cubes and corner, and that the SCALE button is still dead for kit.
- `node --check` passes on all three files.

### Pending

- An imported object is still not in the take, so a person's position, facing and size in the room do not survive a reload. `rec.placed` keeps them where they were put for the session only. This is the same gap the bridge comment has always named — "an imported object goes nowhere: the bridge has no word for one" — and a person moved in 3D is now the most likely way for somebody to notice it.
- Moving a person in 3D does not move their stamp on the pad, so the two disagree until the stamp is dragged. The reverse now defers to the room rather than fighting it, which is the safer half of the asymmetry.

## 26 August 2026 — A name is not part of the thing it names

### Requested work

- Scaling an object must not scale its label.

### What changed

A label sprite is a CHILD of the group it belongs to, which is what makes it follow the shape around the room — and it therefore inherited the group's scale. Resizing a deck stretched its name along with it, and a non-uniform stretch skewed the text besides. `unscaleLabels` divides the group's scale back out of every `isLabel` sprite under it; `labelSprite` now records the size it was built at so there is something to divide back to.

Called at all three doors to a scale: the live gizmo drag, `syncSolids` (a group may be rebuilt already standing at a size somebody tried in the room), and `setObjectSize`, which nothing labelled goes through today but would be the next place to get this wrong.

The label's POSITION is deliberately left scaled. It sits at the top of the shape, and a shape that has grown taller should carry its name up with it — that part of the inheritance is the label following the object, which is the whole reason it is parented to one.

### Files and components

- `scene-study-3d.html` — `labelSprite`, `unscaleLabels`, `syncSolids`, `dragMove`, `setObjectSize`

### Verification

- A 6 m deck scaled to 17.06 m: the label's local scale drops from 0.932 to 0.328 and its WORLD size stays 0.932 x 0.34 — unchanged, live during the drag.
- The same after a full rebuild from a take carrying `scale: [2.844, 1, 1]`, which is the other way a group arrives already scaled.
- Measured at scale 1 against scale 3 through `applyScene`: identical world width both times, where before it would have tripled.

## 26 August 2026 — The actual LED bug: an elevation LED face could not be drawn, so nothing could

### What changed

- **`drawLedTiles` now draws an elevation LED as a face.** In Elevation, `ledGrid` returns ONE facet carrying a tile count and nothing else — no `a`, no `b` — because an LED seen square on is not a run of cabinets between two points, it is a wall of tiles. The drawing code only ever had the Plan branch: it read `f.a` off that facet, got `undefined`, and threw. The face is now drawn as what it is — its seams, clipped to its own outline, so a notched or curved face shows tiles only where it carries cabinets.
- **A frame always starts from a known state.** `draw` resets the canvas state stack and re-applies the canvas's base transform, so a step that throws after a `save` can no longer leave every later frame dimmed or tinted by an orphaned state.
- **One shape that cannot be drawn is one shape.** Each solid's draw is now caught and reported once to the console, rather than aborting the frame.
- Belt and braces: a facet with no endpoints is skipped rather than drawn as a line.

### Why

Reported three times, and my first three attempts were all aimed at the wrong thing. The report was "once an LED is assigned, there is no more right-click functionality on the next shapes", and each time I read it as a hit-testing problem: the pins, then a pad stuck in stamp mode, then handle grabs. Each of those was a real defect and each fix was worth keeping — but none of them was this, which is why the report kept coming back.

The user's fourth message gave the discriminating condition: *only in elevation mode*. That is the whole answer. `draw` is called by every gesture, and the right-click handler calls it ONE LINE BEFORE it opens the menu:

```js
selectItem(i);
draw();               // threw, every time, from the moment an LED existed in Elevation
openRoleMenu(e, i);   // never reached
```

So the menu never opened, the canvas never repainted, and the pad looked frozen — with the exception that anything not routed through `draw` still worked, which is exactly the shape of "nothing else works". No error was visible anywhere the person could see it.

The lesson to keep: three rounds of reasoning about hit tests, and the console had been saying `Cannot read properties of undefined (reading '0')` the entire time. I never reproduced in the view the user was working in. A repro that does not use the failing view is not a repro.

### Files and components

- `sketchpad.html`

### Verification

49 assertions in `test-led.mjs`, section 7 of which is the report performed in Elevation: name a shape LED, assert nothing was thrown, assert the face actually drew, then draw a second shape, hit-test it, right-click it and assert its own menu opens with a fresh question; a third after that; then switch back to Plan and assert the same faces draw as shadows without throwing. Guarded the Plan branch too — a traced LED run still exists and still draws its cabinets. 45 + 36 + 20 on the other pad suites and 17 in the real Hub, all green.

### Pending

- Nothing — the audience's black RENDER texture and the on-canvas crop handles were both done in the same session, and have their own entries above.
## 26 August 2026 — Black means unlit: the crowd in RENDER

### What changed

- The audience `.glb` now carries **two** materials. The working view keeps a black `MeshStandardMaterial` with a little specular, so a crowd being placed shows its shoulders. RENDER mounts an unlit black `MeshBasicMaterial` with tone mapping off it.
- `applyRenderMaterials` swaps between them instead of recolouring one; `clearAudience` disposes both.

### Why

Asked for: *"make the audience .glb have a black texture in render mode."*

The crowd was already black in both views, and the previous entry recorded that as a no-op. It was not. A black STANDARD material is still a lit surface: its diffuse contributes nothing, but every dielectric has a specular response and at a grazing angle Fresnel takes that to white. So the crowd came back from RENDER wearing a bright rim and reading as pale grey figures. No roughness value removes it — the only material that is black under any light is one that is not lit at all.

A silhouette is also what an audience IS from the stage, so the render material is the more truthful of the two.

### Files and components

- `scene-study-3d.html`

### Verification

26 assertions in `test-crowd.mjs`: in RENDER every real figure is unlit and not tone-mapped, and carries both materials so the swap is a swap; a GHOST is untouched and keeps its blue and its shading; the working view is lit again on the way back; and **a rebuild during RENDER comes back unlit**, which is the failure this function exists for — the host pushes a scene constantly and each push hands back fresh working-view materials.
## 26 August 2026 — The clip is an object on the wall now, and the wall is its mask

### What changed

- **The crop model is inverted.** It was a WINDOW ONTO THE CLIP — `offset` and `repeat` choosing which part of the video the wall sampled. It is now a PLACEMENT: the clip is a rectangle with a width, a height, a centre and an angle, all in the wall's own units, and the wall shows the part of that rectangle that lands on it.
- **The picture has a transform box.** Four corners scale it and keep its aspect; four edge handles stretch one axis; a knob on a stem above it rotates it; dragging inside moves it. Shift-drag still rotates and the wheel still scales, so nothing that already worked was taken away. The nearest handle to the pointer wins, rather than the first one tested.
- **The wall is the mask.** Two lines of GLSL injected at the map read: anything outside the placed rectangle is black, because an LED panel with no signal on it is black. Clamped sampling would have smeared the edge pixel across the rest of the wall instead.
- **The floating bar is a readout.** It shows SIZE, ANGLE and AT, plus FILL, WHOLE and RESET. The ± scale and rotate buttons are gone — the picture has handles. The dead `cropMenu` (PAN LEFT / PAN RIGHT / ZOOM IN), kept unbound since the last pass, is deleted.
- **A drawn LED run's UVs were laid down backwards.** Fixed, and it is the more serious of the two bugs here.
- The stats panel's VIDEO OUT counted LED kit only, so a clip on a wall drawn in the Sketch Pad read as "loaded, but nothing is showing it" while it was plainly on screen.

### Why

Asked for directly: *"Rethink the crop handles in a more intuitive way on the LED canvas rather than in a floating menu. The video track should have transform corners for scaling and rotation at the edges of the video and should be rescalable on the canvas but within the constraint of the LED shape which becomes the video cropping mask."*

The old model could not express that, and two things fell out of it that were both wrong. Rotation happened in UV space, so on a wall that is not square a "rotation" **sheared** the picture. And there was no such thing as a video smaller than its wall: `repeat` below 1 was the only size available, so a clip could be cropped INTO a wall but never placed ON one. Both are gone because the placement is a rectangle in the wall's own units and the texture matrix is its inverse, written whole — `offset`/`repeat`/`rotation` cannot express a rigid rotation on a non-square canvas, which is precisely the shear.

Two things found on the way that were not part of the request:

**The UVs of a faceted run ran backwards.** `faceUVsFromBBox` lays u from a facet's own −x to its +x, and the yaw the builder gives each facet, `Ry(atan2(dx,dz) + π/2)`, points its local +x *against* the direction of the run. So a clip on a curved LED wall was being drawn as reversed slices in scrambled order — u walked −3.2 → −8, then +1.7 → −1.7, then +8 → +3.2 across a wall running −8 → +8. It is now one continuous sweep. This was live before any of today's work and would have made the new handles nonsense: the frame's corners were landing on three different parts of the room.

**The transform box was being drawn inside the wall.** A face's local +z is the run's normal, which on half the facets of a curve — and on any wall you have walked round — points away from the camera, so lifting the outline 2 cm along it buried it. The overlay ignores depth now, which is what a control drawn over the thing it controls should do anyway.

### Files and components

- `scene-study-3d.html`

### Verification

79 assertions in `test-crop.mjs`, rewritten for the new model and driving real pointer gestures at the handles' own projected screen positions: a corner scales and keeps the aspect while its opposite corner stays put; an edge stretches one axis and leaves the other untouched; the body follows the hand; the knob turns the picture about its own centre without resizing it, and the result is **still a rectangle** — the assertion that would have failed under texture rotation. The mask is asked the only question that matters, which is where the wall samples the clip: the middle is inside the picture, all four extremes are outside it, and a picture blown up past the wall covers every corner while showing only its middle. Plus the run's u walking monotonically across every facet; the fits; a scene push mid-crop; RENDER; disarming. 26 + 49 + 26 + 30 on the other Scene Study suites, 49 + 45 + 36 + 20 on the pad, 17 + 12 in the real Hub.

### Pending

- Headless Chromium has no video decode, so every clip test runs against a marker canvas texture standing in for the video. The crop path is identical, but nobody has yet watched a real .mp4 being dragged around a wall by its corners.

> These three entries record work done in a parallel session on the same day and merged in
> afterwards. They sit here because the linked-canvas entries below are built on the crop model
> the last of them introduces.


## 26 August 2026 — LINK LEDS: several screens, one canvas

### Requested work

- Shift to multi-select LED screens; a right-click option LINK LEDS that makes them one canvas, so a video plays across three separate screens as one image.

### What changed

- **The canvas is read off the room, not typed.** The screens' own positions and sizes say where each one sits in the whole, GAPS INCLUDED — 1 m between two walls is 1 m of canvas that falls on thin air, which is what a real processor does and what somebody linking three walls wants to see. `ledRect` takes each screen's rectangle off the meshes the clip is actually painted on (a faceted run is several meshes and the record does not say where they ended up); `ledCanvas` lays them out along ONE axis taken from the two screens furthest apart, because a corner wrap is the commonest reason to link three and no single screen's own direction describes it.
- **Each member gets its own VideoTexture over the same video element**, with a matrix that is the clip's crop composed with that member's window: `crop * window`. The window maps the screen's own 0..1 into canvas space; the crop maps canvas space into the video. So the crop is placed ONCE against the whole canvas and each screen shows its share. A clone would share the matrix, which is the one thing each member needs its own of.
- Shift-select now takes a DRAWN LED wall as well as kit. `selMany` was kit-only, so a canvas made of two library screens and one wall traced on the pad could not be selected as the thing it is. The gizmo's multi-drag filters to ids of the same kind as the thing being held, so a projector still does not tow a deck.
- A right-click INSIDE a selection leaves it alone. It used to clear `selMany` every time, which made "select three, then right-click one of them" impossible — and that is the whole gesture.
- A drawn LED wall has a right-click menu now, because it is one of the things a canvas is made of and the menu is where a canvas is made. Both menus render through one `openItemMenu`.
- Groups are pruned in `routeMedia`, where everything else re-reads the room: a wall deleted in the pad or the room takes its share of the canvas with it, and a group down to one member is not a canvas.

### Files and components

- `scene-study-3d.html` — `ledLinks`, `ledGroupOf`, `ledSurfaceIds`, `ledRect`, `ledCanvas`, `linkTexFor`, `paintLinkedLed`, `paintOneLed`, `routeMedia`, `ledPaint`, `syncClips`, `installClip`, `pickAt`, `gizmoPointerDown`, `contextmenu`, `ledLinkItems`, `linkLeds`, `unlinkLeds`, `ledSolidMenu`, `openItemMenu`, `updateReadout`, `window.SS`

### Verification

- Three 6 m walls with 1 m gaps: canvas 20.0 x 4.0 m, aspect 5.00, windows u 0.00–0.30 / 0.35–0.65 / 0.70–1.00. The 0.05 gaps ARE the 1 m physical gaps.
- With a clip routed to the CENTRE wall only, all three painted: each carries its own texture and a matrix with u-scale 0.30 at offsets 0, 0.35, 0.70.
- Rendered for real, with a video recorded in the browser — ten numbered colour bars across one 1280x256 frame. The three walls read `0 1 2` / `4 5` / `7 8 9`, and `3` and `6` are missing because they land in the physical gaps. One image across three screens.
- Link → unlink → link: unlinked, each wall goes back to showing only what is routed to it and its per-member texture is disposed; re-linking brings the canvas back.
- Pruning: deleting the right-hand wall left the group as two members and a 13 m canvas (6 + 1 + 6).
- The whole gesture through the real handlers: shift-select three walls, right-click one of them → `Link LEDs · 3 screens as one canvas`; pressing it links them; right-clicking a linked screen offers `Unlink · 3 screens`.
- Member order follows the clicks, and the layout follows the ROOM — a group stored as [centre, left, right] still lays out left, centre, right.
- `node --check` passes.

### Pending

- **A link is tool-side and does not survive a reload**, like the clips themselves. It is a wiring fact about the show and belongs in the take; that is plumbing across three files and was deliberately not started here.
- One video is uploaded once per linked screen per frame. For three walls in a preview that is the right trade against re-encoding anything, but it is not free and it scales with member count.
- The SPILL colour still reads the clip's whole frame rather than each screen's window, so three linked walls throw the same average light. Wrong in principle, invisible in most content.
- Unlinking leaves the crop fitted to the canvas rather than re-fitting to the single screen. Consistent with the existing rule that a re-fit is a deliberate act, but worth knowing.
- Only LED surfaces can be linked. A projector pair sharing a canvas — a blend — is the obvious next thing somebody will ask for and is a different problem.

## 26 August 2026 — Multi-select in the Sketch Pad, and LINK LEDS from the paper

### Requested work

- LED objects could not be multi-selected in the Sketch Pad once assigned.

### The actual cause, and it was two things

The pad had ONE selection — `S.sel`, an index — and no gesture that added to it. So the canvas could be picked out in the 3D and not on the paper, which is the surface people are actually drawing the walls on.

And underneath that, a plainer bug: the RIGHT BUTTON fired `pointerdown` before `contextmenu`, so every right-click ran the whole pointer dispatch first and selected whatever was under it. Harmless while there was only ever one selection; fatal the moment a SET could be held, because it collapsed the set on the way to the menu that was about to offer an action on it. Right-click has exactly one meaning on the pad and it is handled where that meaning lives.

### What changed

- `S.selMany` holds ids, not indices. An index is a position in a list that erase, undo and the interpreter all reorder, and a selection that silently comes to mean a different shape is worse than no selection.
- SHIFT adds and takes away, and the shape already held joins the set on the first shift — otherwise "click one, shift-click a second" gives a set of one and a selection that is not what anybody is looking at. Checked BEFORE the ordinary body branch, because that branch also starts a drag and shift-clicking a third wall must not move the second one on the way.
- Every shape in the set reads as held — a keyline in the active ink — and only the ONE carries handles, because a set is named and sent somewhere rather than reshaped vertex by vertex.
- The role menu gains LINK LEDS when more than one LED wall is held. Offered there because it is the menu that is already on the shape, and because the alternative — go to the 3D and pick the same three walls out again — is doing the work twice.
- The whole set travels: `selectSolid` carries `srcIds`, the hub relays it, and the Scene Study holds the same three walls. A new `linkLeds` message carries the request itself — the pad names the walls, and only the Scene Study holds the geometry that says where each one sits in the canvas, so the request is relayed rather than answered.

### Files and components

- `sketchpad.html` — `S.selMany`, `idOf`, `isSelected`, `selectedItems`, `selectItem`, `toggleSelect`, `heldLeds`, `pointerdown`, `draw`, `drawSolid`, `openRoleMenu`, the role-menu click handler, `contextmenu`, `announceSelection`, `IN.selectSolid`, `reset`
- `HUB_5.8.html` — `case 'selectSolid'`, `case 'linkLeds'`, `fanOutSolidSelection`
- `scene-study-3d.html` — `IN.selectSolid`, `IN.linkLeds`, `routeForSrc`

### Verification

- Three LED walls drawn in the pad: click one, shift-click the other two — all three outlined, the last carrying handles, and the posted `selectSolid` grows `srcIds` to three.
- Right-clicking one of the three no longer collapses the set, and the menu reads `LINK LEDS · 3 screens as one canvas in the Scene Study`. Before the right-button guard it collapsed to one and the item did not appear at all.
- Pressing it posts `linkLeds {srcIds:[…3 ids]}` and the footer confirms.
- Through the Production Hub end to end: holding three walls on the paper and pressing LINK LEDS made the Scene Study read `CANVAS OF 3` on the selected wall.

### Pending

- The set is solids-only. Shift-clicking anchors or labels into a selection is not offered, and neither is a marquee.
- LINK LEDS on the pad requires the walls to be BUILT — the Scene Study answers with a message saying so if they are not. That is honest but late; the pad could tell before sending.
- Nothing in the pad DRAWS the link. Three walls that are one canvas look exactly like three walls until you look at the 3D.

## 26 August 2026 — A LINK IS A ROUTE: one source, three masks

### Requested work

- Shift-selected LED screens must STAY highlighted.
- The timeline's ROUTE button needs a LINKED SCREENS option, feeding the interlinked LEDs.
- The crop must operate across the linked screens at once — one video source and three masks.

### What changed

- **The highlight was simply missing.** `paintSolidSelection` lit `S.selSolid` and nothing else, so a shift-selection of drawn walls was held and invisible — which is the one thing a selection exists to save you from. It now lights every shape in `selMany` too.
- **A link is a ROUTE, not a property of three routes.** That is the whole design of this change: a group has an id a clip can be sent to like any other surface, and everything downstream already asks "what is this route?" — so `cropFaces`, `routeAspect` and `wallCanvas` needed ONE branch each and the entire crop system, its handles, its hit tests and its drags started working across the canvas for free.
- `wallCanvas` for a group is the members' own canvases RENUMBERED: each member already knows its 0..1 across itself, and the link says which slice of the whole that is. Remapping the u's (and v's, so a short screen in a tall canvas takes its own band rather than being stretched) is all it takes. `wallToWorld` maps canvas v back to the member's own.
- The route menu lists linked canvases FIRST, labelled `LINKED · N SCREENS` with the members named underneath. It is the destination somebody who has just linked three walls is looking for, and offering only the members would be offering the three things they linked precisely so they would stop being three. Choosing it holds the canvas as the set it is — every member lit.
- Unlinking re-routes a clip that was on the canvas to the first of its former members. A picture that vanishes without being sent anywhere is the tool losing somebody's work quietly.

### Files and components

- `scene-study-3d.html` — `paintSolidSelection`, `ledGroupById`, `isLinkRoute`, `ledGroupLabel`, `cropFaces`, `routeAspect`, `wallCanvas`, `wallToWorld`, `routeMenu`, `paintLinkedLed`, `removeLink`, `loadOntoDevice`, `window.SS`

### Verification

- Three 6 m walls, 1 m gaps, linked: `wallCanvas('ledlink-1')` gives spans u 0–0.30 / 0.35–0.65 / 0.70–1.00 at aspect 5 and height 4 m, against 0–1 at aspect 1.5 for one wall alone. So the crop's handles lay out across the whole 20 m canvas, gaps included.
- The route menu reads `Send CANVAS.webm to · LINKED · 3 SCREENS (LED L + LED C + LED R) · LED L · LED C · LED R`. Choosing the linked entry set `route: 'ledlink-1'`, lit all three walls, and held all three in the selection.
- ONE SOURCE, THREE MASKS, measured: panning the canvas (`crop.x` 0 → 0.5) moved all three windows by the same −0.25; zooming (`crop.w` 5 → 2.5) spread them 0/0.35/0.70 → −0.5/0.2/0.9, each screen covering twice as much of the picture.
- Rendered: with the ten-bar test video on the canvas the walls read `0 1 2` / `4 5` / `7 8 9`; panning right slid the whole picture across all three together to `0` / `2 3 4` / `5 6 7`.
- Multi-selected walls stay lit — all three report a line colour changed to the active yellow.

### Pending

- Still tool-side, so a link and a clip routed to one do not survive a reload.
- Spill still averages the clip's whole frame rather than each screen's window, so three linked walls throw the same light. More visible now that a canvas can be panned so that one screen is dark and another is bright.
- The crop OUTLINE across a linked canvas draws on the members' faces; the part of the frame that crosses a gap has no mesh to be drawn on, so the rectangle reads as broken. Correct, and it looks like a bug until you think about it.

## 26 August 2026 — Yellow in both panels, and a link that is a route everywhere

### Requested work

- Multi-selected LEDs must stay yellow in the Sketch Pad AND the Scene Study.
- The video asset still had no option to load into the linked LEDs, and the crop was not working across them.

### What was actually wrong

- **The pad drew the keyline and then painted over it.** `drawSolid` reasserts the silhouette after role decoration — a line that exists so an LED's cabinet grid cannot swallow the outline — and my held-keyline was drawn BEFORE it. So a set of three read as one yellow shape and two white ones. Moved after; the set is yellow.
- **A link was a route in the MENU and nowhere else.** `routeTargets()` did not include groups, so every other place that turns a route into a name fell through: the timeline's ROUTE button printed a raw `ledlink-1`, `selectClip` set `S.sel` to an id no device has, and the toast said the same. One list now holds every destination a clip has, linked canvases first, and the button prints a short `LINKED ×3`.
- **And the checklist said it was not showing anywhere.** `VIDEO OUT` counted LED kit and drawn walls whose OWN id the clip was routed to. A clip routed to the GROUP matched neither, so three walls plainly carrying a picture were reported as "loaded, but nothing is showing it" — the same defect the drawn-wall count had once, one layer further out. Anybody reading that would conclude the routing had not worked, which is exactly what happened.

### What changed

- `routeTargets()` = linked canvases + devices + drawn walls, in one list. `routeMenu` filters that list instead of building its own.
- `routeLabelOf` prefers a route's `short` name, so the timeline chip reads `LINKED ×3` rather than a sentence or an id.
- `selectClip` on a canvas route holds the canvas as the set it is — every member lit — instead of setting a device selection to a group id.
- Arming the CROP on a linked route lights every member and says so: the handles are on the CANVAS, so a drag moves the picture across all of it rather than on the screen it started over.
- `paintSolidSelection` lights `selMany` as well as `selSolid` (from the previous entry, verified here).

### Files and components

- `sketchpad.html` — `drawSolid` keyline order
- `scene-study-3d.html` — `ledGroupLabel`, `ledGroupShort`, `linkRouteTargets`, `routeTargets`, `routeLabelOf`, `routeMenu`, `selectClip`, `armCrop`, the `videoOut` count

### Verification

- Sketch Pad: three LED walls, click + shift + shift — all three outlined in `#FEFF34`, the primary carrying handles.
- Scene Study, through the real pointer handlers: shift-clicking three walls leaves all three reporting a changed line colour, and the readout says `CANVAS OF 3`.
- The ROUTE menu reads `LINKED SCREENS · 3 (LED L + LED C + LED R)` above the three members; choosing it sets `route: 'ledlink-1'`, holds all three, and plays the canvas across them — `0 1 2` / `4 5` / `7 8 9`.
- `cropFaces`, `wallCanvas` and `routeAspect` all answer for the group route: 3 faces, 3 spans, aspect 5.
- The HUD now reads `VIDEO OUT · 3 WALLS` where it read "loaded, but nothing is showing it".

### Pending

Unchanged from the previous entry — persistence, spill colour, and the crop frame reading as broken where it crosses a gap.

## 26 August 2026 — The crop moved everything except the picture

### Requested work

- The crop does not quite work on a linked canvas.
- Selections must be synced between the Sketch Pad and the Scene Study.

### The crop bug, exactly

`commitCrop` — what every frame of a crop drag calls — did `applyCrop(clip, aspect)` and then redrew the outline. On ONE wall that is the whole of placing a picture, because the wall's map IS the clip's texture and changing its matrix changes the picture. On a LINKED canvas it is not: each member has its own texture carrying `crop * window`, and nothing recomputed those. So dragging the frame moved the outline, moved the numbers in the crop bar, and left the picture exactly where it was.

Measured before the fix: with `crop.x` taken 0 → 0.4, `applyCrop` alone left the three members' u-offsets at 0 / 0.35 / 0.70 — unmoved. A full `routeMedia` moved them to −0.2 / 0.15 / 0.50. The crop was calling the first and not the second.

`relinkMatrices` is that recompute on its own — the members' windows written against the clip's current matrix, no rebuild — and `commitCrop` calls it for a linked route. `paintLinkedLed` now uses the same function rather than its own copy of the arithmetic.

### The selection sync

- The Scene Study announced ONE id, and only from the ordinary click: the shift branch of `pickAt` posted nothing at all. So shift-selecting in the room reached the paper as "one thing is selected", and it silently replaced a set somebody had just built there.
- `announceSelection` in the Scene Study now names the whole set (`srcIds`), the hub relays it pad-ward as well as scene-ward, and the pad applies it — holding the ids it recognises and ignoring the ones it does not, because a shape built from a plan the pad never drew has no outline there to light.
- A drawn wall shift-clicked FIRST had no `selSolid` to be the one on top, so the set had no primary and the pad could not name it. The first one taken becomes it.

### Files and components

- `scene-study-3d.html` — `relinkMatrices`, `paintLinkedLed`, `commitCrop`, `announceSelection`, `pickAt`
- `HUB_5.8.html` — `fanOutSolidSelection`, `case 'selectSolid'`
- `sketchpad.html` — `IN.selectSolid`

### Verification

- `commitCrop` on a linked canvas now moves all three: pan 0 → 0.4 gives −0.2 / 0.15 / 0.50; halving the width spreads them to −0.5 / 0.20 / 0.90. The same call before the fix moved nothing.
- Rendered with the crop armed: the frame spans all three walls with handles at the canvas corners, the crop bar reads `CANVAS.webm → LINKED ×3 · SIZE 5.00 × 1.00 · AT 0.30 · 0.00`, and the picture has panned across all three to `0` / `2 3 4` / `5 6 7`.
- Pad → Scene: holding three walls on the paper lights all three in the room and names the top one in the readout.
- Scene → Pad: the payload a shift-selection now posts lands in the pad as three held shapes — `LED L`, `LED C`, `LED R`.

### Pending

- Persistence, spill colour and the gap-crossing crop frame, all unchanged.
- The two panels agree about WHICH shapes are held, not about which is primary — each keeps its own idea of the one on top. Harmless today because the primary only decides which row the pad opens.

## 27 August 2026 — A band you sweep, and a picture that opens from the middle

### Requested work

- Replace shift-clicking with a click-and-drag marquee: a dashed rectangle that selects every shape it CROSSES.
- With several LEDs held, right-click → LINK LEDS; then one video track plays across them as a single masked source rather than three tracks.
- The picture starts in the CENTRE and grows outwards as it is resized; cropping from the edges of the video content.

### What changed — the marquee

- A drag that starts on empty paper with SELECT armed sweeps a band. Dashed, in the active ink, with a faint fill — the fill earns its keep: a crossing selection takes what it TOUCHES, so the band has to read as a region passing over things rather than a box drawn around them.
- **Crossing, not window.** Anything the rectangle touches is taken: a vertex inside it, an edge that crosses one of its sides, or the band lying wholly inside a big closed shape. The reason is what the gesture is for — the LED walls that are about to become one canvas are long and spread across the plan, and sweeping a band through the middle of a row of them is the gesture. Being made to enclose each one entirely would be the tool asking for precision it does not need.
- What the band has taken lights up AS IT IS SWEPT. A crossing selection that only shows its result on release is a gesture done blind.
- A click on empty paper still clears the selection: below a few pixels of travel the gesture was a click, and it has already done that. SHIFT-dragging adds to what is held instead of replacing it.
- A LOCKED shape is still taken. It cannot be dragged or reshaped, but it can be NAMED — and naming a set of built walls as one canvas is the main thing anybody does with a set of built walls.

### What changed — the picture as a masked source

- **On a linked canvas the clip arrives CONTAINED, not covering.** A clip covering one wall is right: the wall is the picture's frame and you want it full. A canvas of three screens and two gaps is not a frame, it is a region the picture lives IN — so the clip arrives at its own shape, centred, and the screens show whatever falls on them. Cover on a 5:1 canvas from a 16:9 source means blowing the picture up 3x and throwing most of it away before anybody has asked for anything.
- The masking itself was already real and did not need writing: `ledDrive` has always zeroed emissive outside the transformed UV, so a screen the picture does not reach is dark rather than smeared with a clamped edge pixel.
- **A CORNER resizes from the middle.** The opposite corner is the right anchor on a single wall — you are placing a picture against an edge you can see. A canvas has no such edge: its middle is the only landmark three screens and two gaps agree on. Both edges move, so the size changes by twice the drag and the handle still tracks the pointer.
- **AN EDGE still crops that side**, opposite edge fixed, which is what pulling one edge of a picture in means and what every wall already did. The two gestures part company only on a linked canvas.
- Linking screens that already had a clip on one of them re-fits it: a crop sized against one wall is not a placement on a canvas of a different shape.

### Files and components

- `sketchpad.html` — `marquee`, `marqueeRect`, `marqueeTakes`, `marqueeUp`, `drawMarquee`, `draw`, pointer down/move/up
- `scene-study-3d.html` — `applyCrop`, `cropMove`, `linkLeds`

### Verification

- Three LED walls and a deck below them: a band swept through the walls took all three and left the deck alone. Footer read `3 SHAPES SELECTED · 3 LED — RIGHT-CLICK TO LINK LEDS`, and the shapes lit while the band was still moving.
- Right-clicking one of the three kept the set and offered `LINK LEDS · 3 screens as one canvas in the Scene Study`.
- A 16:9 clip routed to a 5:1 linked canvas arrived as `w 1.78 · h 1.00 · x 0 · y 0 · cover false` — its own shape, centred on the middle screen, with the outer two DARK.
- Growing it 2.4x about the centre spread it symmetrically across all three: `0 1` / `3 4` / `6 7`, with `2` and `5` falling in the physical gaps.
- End to end through the Production Hub: sweeping the band in the pad, sending LINK LEDS, and the Scene Study reading `CANVAS OF 3` with all three walls yellow.

### Pending

- The marquee is the PAD's. The Scene Study still needs shift-clicking; a marquee there is a different problem (a 2D rectangle over a perspective view).
- Persistence, spill colour and the gap-crossing crop frame, all unchanged.
- An edge drag on a linked canvas changes the frame's aspect, which STRETCHES the source rather than revealing more of it — the frame is what is shown, not a window onto a larger picture. That is the existing crop model and it is not obviously what "crop from the edge" means to everybody.

## 27 August 2026 — The set as one object

### Requested work

- Dragging across shapes selected only one of them.
- A multi-selection needs to stay yellow AND carry transform handles on its edges — resize, rotate, move the group.

### Why only one got selected

The marquee only started on EMPTY paper. Press on a wall meaning to sweep three and the press went to the single-shape branch, which selects that wall and starts moving it — so the gesture ended as "one shape selected, and nudged". A marquee you can only start on empty paper is a marquee you cannot use on a crowded plan.

SHIFT-DRAG now sweeps a band from anywhere. Shift already means "add to what is held", so shift-drag means "add a band", and a shift-press that never travels still just toggles the shape under it. A drag from empty paper still marquees, and a plain drag on an unselected shape still moves that shape — both checked.

### The group box, and the bug it exposed

The set gets the same furniture a single shape gets: a dashed box, a square at each corner, a rotate tick outside each one. A press inside the box moves the whole set — without that, grabbing one of three held walls dropped the other two and dragged that one, so the selection was real and the drag was not about it.

**Both boxes are on screen at once**, and their corners sit within a few pixels of each other: the set's, and the one belonging to whichever member is on top. Asked in the wrong order, grabbing the SET's rotate zone turned ONE wall out of three and left the others where they were — which looks exactly like the group transform not working. Caught by driving it: tops went from `[320, 320, 320]` to `[227, 298, 369]` for one wall only. The set's furniture now outranks the member's, in the hit test and in the cursor, and the member's own transform box is not drawn at all while a set is held — two boxes over one thing is a question with no answer on screen.

**Both group transforms are uniform, and that is geometry rather than restraint.** A bulge describes a circular arc: it survives a uniform scale and a rotation untouched, and a non-uniform scale turns the arc into an ellipse, which a bulge cannot express. A single shape can afford the non-uniform case because it re-fits its own raw ink; doing that to every member would re-fit shapes nobody touched. So a corner scales the set about the opposite corner and keeps its shape, and no refit is needed for either transform.

A LOCKED member does not move — it stays in the set, because naming is what a set is mostly for, but a built shape is a fact about the scene and a group drag is not the place to change one silently. The footer says how many were held back.

### Files and components

- `sketchpad.html` — `groupBox`, `groupCorners`, `hitGroupCorner`, `hitGroupRotate`, `inGroupBox`, `mapHeld`, `scaleGroup`, `rotateGroup`, `moveGroup`, `drawGroupBox`, `marqueeUp`, `drawSolid`, `paintCursor`, pointer down/move/up

### Verification

- Shift-drag starting ON the left wall took all three — the case that previously moved one shape.
- The box spans all three with corner squares and rotate ticks; the member's own box is gone while the set is held.
- MOVE: pressing inside the box and dragging +20,+30 moved the box exactly that far, all three together.
- SCALE: the bottom-right corner took the box from 640x50 to 720x58 about the opposite corner, uniformly.
- ROTATE: all three turned about the group centre — tops `[320, 320, 320]` → `[227, 298, 369]`, and the row reads as one diagonal rather than one turned wall among two straight ones.
- Regressions checked: a marquee from empty paper still takes three; a plain drag on one unselected shape still moves just that shape.

### Pending

- No edge handles on the group box, only corners. Deliberate — an edge handle means a non-uniform scale, which a set of fitted arcs cannot take honestly.
- The group box is the PAD's. The Scene Study has no equivalent.
- Nothing snaps: a group scale or rotation is free, where a single shape's drag has SNAP available.

## 27 August 2026 — The canvas took its handedness from the mouse

### Requested work

- Linking LEDs from the Sketch Pad should visibly happen in the Scene Study.
- The video's position on a linked canvas, and the crop, are still wrong. Read the objects' ABSOLUTE position in space, centre the video on the middle of that, let the LEDs mask it there, and crop against the whole spread.

### The bug, and it was one line

`ledCanvas` takes its axis from the two screens furthest apart, as `b.centre - a.centre` — and `a` and `b` are the EARLIER and LATER members of the pair in the group's member list. That list is the order somebody clicked them in. So selecting three walls right-to-left produced an axis pointing the other way, and the canvas came out MIRRORED: the picture ran backwards across the room. Every complaint about the positioning being wrong was this, and it was invisible in testing because I had always selected left-to-right.

The room has a handedness of its own — X runs stage-left to stage-right — so the canvas takes it rather than the mouse's. One negate, and the layout is the same whichever way the walls were picked.

Verified both ways: selecting `[L, C, R]` and `[R, C, L]` now both give axis `[1, 0]`, `L` at u 0.00 and `R` at u 0.70, and a canvas centred at `0 · 4 · 0` — the true middle of the three walls in space.

### What else changed

- `ledCanvas` reports its `axis` and its `centre` in the room. The origin cancels out of the windows but not out of "where does the picture start", which is the whole question — and a number nobody can read is a number nobody can check. The link toast now names it.
- Linking holds the set: lit, primary set, named in the readout, announced back to the paper. Asked for from the Sketch Pad this was the only thing missing — the pad named the walls and the geometry is in the Scene Study, so without it somebody presses LINK LEDS on the paper and the 3D sits there looking identical.

### Files and components

- `scene-study-3d.html` — `ledCanvas`, `linkLeds`

### Verification

- Axis orientation: `[L, C, R]` and `[R, C, L]` give identical windows and an axis of `[1, 0]`.
- Linked RIGHT-TO-LEFT on purpose, a 16:9 clip on the 5:1 canvas read `1 2 3 4 5 6` LEFT to right, centred on the middle wall with the outer two dark. Before the fix that was mirrored.
- Grown 2.6x about the centre: `0 1` / `3 4` / `6 7`, correct order, `2` and `5` in the physical gaps, offsets −0.04 / 0.34 / 0.72 about a canvas centred at `0 · 4 · 0`.
- Through the Production Hub: sweeping the marquee RIGHT-TO-LEFT in the pad and pressing LINK LEDS left the pad holding three and the Scene Study reading `CANVAS OF 3` with all three walls yellow.

### Pending

- Persistence, spill colour and the gap-crossing crop frame, all unchanged.
- The axis is a single horizontal direction, so a canvas whose screens wrap a corner is laid out by their projection onto it. Right for a shallow wrap, increasingly wrong as the corner tightens, and there is nothing yet that says so.

## 27 August 2026 — Naming one of three, and announcing a set that did not exist yet

### Requested work

- Sketch Pad selection and assignment still do not match the Scene Study.

### Two separate faults, both real

**1 · ASSIGNMENT NAMED ONE SHAPE.** The role menu called `nameSolid(i, …)` with the single shape that was right-clicked. So holding three walls, choosing LED, and watching ONE of them become an LED wall while the other two stayed decks was the whole of "the assignment does not match" — the Scene Study was showing exactly what it had been told.

`nameHeld` applies the role to every shape in the set, and the selection SURVIVES it — which `nameSolid` alone cannot manage, because it ends with `selectItem`, and a plain select means "this one and only this one". Naming a set and then losing it means picking the same three walls again before they can be linked, which is the next thing anybody does. Locked members are left alone and counted in the footer. The menu head now reads `3 shapes are…` and a role's tick means "all of them are", not "the one under the pointer is".

**2 · THE SELECTION WAS ANNOUNCED BEFORE IT WAS SAYABLE.** The pad names shapes by the trace they came from; the Scene Study resolves those against the TAKE. A set named and announced BEFORE BUILD therefore names shapes the take does not have yet — `routeForSrc` finds nothing, the room holds nothing, and the two panels disagree about a selection the person is looking at. Measured: pad held 3, scene readout empty, take had the three LED solids.

BUILD now restates the selection. Nothing else re-announces, and nothing needs to: the selection did not change, the world it is expressed in did.

### Files and components

- `sketchpad.html` — `nameHeld`, `applyRole`, the role-menu click handler, `openRoleMenu`, `postSolids`

### Verification

- Three traced shapes, marquee-swept, role menu opened on a member: head reads `3 shapes are…`; pressing LED left all three `led`, the set still held at 3, footer `3 LEDS`.
- BUILD sent all three to the take as `role: 'led'` (`A`, `B`, `C`).
- After BUILD the Scene Study holds all three — three walls yellow, readout naming the primary as `led`. Before the fix the readout was empty with the pad holding three.
- LINK LEDS from the pad then read `CANVAS OF 3` with the pad still holding three.

### Pending

- Unchanged: persistence, spill colour, the gap-crossing crop frame, the single-axis canvas on a tight corner wrap.
- Naming a set does not name it in the ROOM directly — the roles reach the take on the next BUILD, which is the existing contract for every other shape edit but means the two panels are briefly out of step by design.

## 27 August 2026 — A set is a set for every function, in both panels

### Requested work

- Every function should apply to all selected objects — unlock, move, delete.
- The LAST object selected should be yellow like the others.
- Rotation should rotate the whole set, not just the last one. In the Sketch Pad AND the Scene Study.

### What changed — the Sketch Pad

- **The last one picked is yellow too.** It was left in the ordinary ink on the grounds that its handles are already yellow — but handles are small and an outline is not, so a set of three read as two held shapes and one that looked dropped. Everything in the set looks the same, because everything in the set IS the same.
- **While a set is held, the SET owns the transforms.** `hitCorner` and `hitRotateCorner` now decline outright. A member's own box is not drawn then, and a handle that cannot be seen but can be hit is how grabbing the group's rotate zone ended up turning one wall out of three.
- DELETE takes the set, highest index first — every splice moves the ones still to come, so the wrong shapes go otherwise.
- UNLOCK takes every built shape in the set. Unlocking two of three and then wondering why the group will not move is a puzzle the tool has no business setting.
- The height field applies to every held solid. Typing one number into a row that is naming three walls and having it land on one of them is the row lying about its own scope.

### What changed — the Scene Study

- **A gizmo drag on a set moves the set.** `ids` was `[t.id]` for anything that was not kit, so with three walls held and lit, turning the gizmo turned one and left the other two — the selection was real and the transform was not about it. A drag now takes everything in `selMany` of the same KIND as the thing held: a pile of projectors moves together, three linked walls move together, and a projector does not tow a deck.
- **A set turns as one object**, which means about the SET's pivot and not each member's own. Turning each in place leaves three walls facing a new direction in the same three places — a row that has been twisted rather than swung. Each member's start offset from the pivot is carried round by the same rotation.
- DELETE takes everything held, across all three kinds, and the button lights for a set rather than only for a single primary.
- `removeSolidById` factored out so the set-wide delete and the single one are the same removal.

### Files and components

- `sketchpad.html` — `drawSolid`, `hitCorner`, `hitRotateCorner`, `sol-del`, `sol-unlock`, `unlockHeld`, the `sol-h` handler
- `scene-study-3d.html` — `gizmoPointerDown`, `dragMove`, `b-del`, `removeSolidById`, `removeSelectedSolid`, `refreshSelection`

### Verification

- Pad: three built LED walls marquee-swept — all three yellow INCLUDING the last picked, group box with corner squares.
- UNLOCK: `[true,true,true]` → `[false,false,false]`, set still held at 3, footer `3 SHAPES UNLOCKED`.
- Group rotate through the real handles: tops `[260,260,260]` → `[167,238,309]` — all three, about the set's centre.
- DELETE: 3 items → 0, footer `3 SHAPES DELETED`.
- Scene: three walls held, the gizmo's rotate ring dragged — all three turned −14.1° and were carried round the pivot (`-7,0` → `-6.79,-1.70`; `7,0` → `6.79,+1.70`; the middle one stayed put). Before the fix only the middle one turned.
- Scene DELETE: 3 solids → 0, selection cleared; the button enables for a set when the selection arrives through the real path.

### Pending

- Unchanged: persistence, spill colour, the gap-crossing crop frame, the single-axis canvas on a tight corner wrap.
- The Scene Study has no group BOX — the gizmo sits on the primary and transforms the set. It works, but where the pivot is has to be inferred from where the gizmo is.
- The Scene Study's camera keeps a broken aspect if the panel is ever measured at zero width; the Sketch Pad guards against exactly that and the 3D does not. Found while testing, not caused by this change.

## 27 August 2026 — A canvas you can see, leave, and join

### Requested work

- A way of recognising when screens are linked, and a function to unlink them.
- Unlinking should REPLICATE the loaded video individually onto each screen.
- A screen designed later should be able to join an existing canvas by being selected with it and linked.

### What changed — recognising one

A canvas was invisible. Three screens that are one picture look exactly like three screens until something is playing on them, and even then only if the content happens to cross a join.

- **In the room**: a bar along the run at the foot of the screens with a tick up into each member, in `gHelpers` because it is a statement about the scene rather than a thing in it — same reason the gizmo lives there, same reason it goes dark in RENDER. Ordered along the canvas's own axis, not the order the screens were picked.
- **On the label**: a member reads `LED C · 2/3` in the active ink. The bar says a canvas is there; the label says which screen of it this is, which is what you want when you are looking at one wall and wondering whether it is in the set.
- **On the paper**: the pad cannot work a canvas out for itself — it takes the geometry of the room to say what one is — so it is TOLD, by source id, and draws its own dashed tie labelled `ONE CANVAS · 3 SCREENS`.

### What changed — leaving one

- The pad's shape menu offers UNLINK whenever the held set touches a canvas, and the request goes back through the bridge by the canvas's own id.
- **Unlinking REPLICATES.** It used to fall the clip back to the first screen and let the other two go dark, which reads as the tool losing most of somebody's work. Three screens that were one picture now each show THE WHOLE picture — which is what they would each be doing if they had never been linked, and the state anybody unlinking is asking to get back to. `clip.replicate` is the list carrying the copy; the ROUTE stays a single id so the crop, the label and the aspect all go on meaning what they meant.
- `cropMatrix` pulled out of `applyCrop`, because a replicated clip is one picture fitted to EACH screen and each screen has its own aspect — so the placement has to be computable against more than one shape.
- Routing the clip somewhere by hand clears the replication: a copy left on two other screens after somebody has picked a destination is the tool remembering a state they just replaced. Linking screens that were replicating does the same — the copies are what the canvas replaces.

### What changed — joining one

`linkLeds` read its argument strictly, so selecting a canvas plus one new wall made a NEW canvas out of the selection and quietly broke up the old one. A wall drawn after the canvas was made is the commonest thing there is, and holding it together with the screens it is joining is how anybody expects to add it. The members of any group being touched now come along and the result is the union. The menu says `JOIN THE CANVAS · add 1 to a canvas of 3` rather than LINK, and LINK is not offered at all over a set that is already exactly one canvas.

### Files and components

- `scene-study-3d.html` — `gLinks`, `refreshLinkMarks`, `postLinks`, `cropMatrix`, `clipReplicatedOn`, `paintReplicaLed`, `routeMedia`, `linkLeds`, `removeLink`, `routeMenu`, `syncSolids` label, `IN.unlinkLeds`
- `HUB_5.8.html` — `case 'ledLinks'`, `case 'unlinkLeds'`
- `sketchpad.html` — `ledCanvases`, `canvasOf`, `heldCanvases`, `IN.ledLinks`, `drawCanvasTies`, `openRoleMenu`, the role-menu click handler

### Verification

- Four walls, three linked: the tie bar is drawn under exactly those three, the fourth stays dark and out, readout `CANVAS OF 3`, `VIDEO OUT · 3 WALLS`.
- JOIN: holding the new wall with ONE member and linking gave `CANVAS OF 4` and a canvas 27.0 m wide, up from 20.0 — all four lit, one group, not two.
- UNLINK: `links: 0`, `replicate: [all four]`, and each screen rendered the WHOLE picture `0 1 2 3 4 5 6 7` fitted to itself rather than a slice of a canvas.
- Pad: the `ledLinks` message drew the dashed tie labelled `ONE CANVAS · 3 SCREENS` under the first three only; the menu over the three read `UNLINK · 3 screens go back to showing the video each`, and over the three plus the new one read `JOIN THE CANVAS · add 1 to a canvas of 3`.

### Pending

- Unchanged: persistence, spill colour, the gap-crossing crop frame, the single-axis canvas on a tight corner wrap, no group box in the 3D, the zero-width camera aspect.
- The pad's tie is drawn from what the Scene Study last said. With no 3D panel open the pad shows no canvases at all, which is honest but means the paper can look like nothing is linked when something is.

## 27 August 2026 — JOIN dropped the wall it was there to add

### Requested work

- JOIN THE CANVAS does not properly work.

### What was wrong

The whole point of JOIN is a wall drawn AFTER the canvas was made — and a wall drawn a moment ago has not been built. The pad names walls by the trace they came from; the Scene Study resolves those against the TAKE. So the one wall the gesture exists to add was the one wall that could not be resolved, and `IN.linkLeds` filtered it out, linked the three it already had, and said nothing. Press JOIN, watch nothing change.

Reproduced through the real menu action: pad held 4, sent 4 source ids, canvas stayed at 3, no message either way.

There is a second ordering fault underneath it. Even when the wall IS built in the same breath, it reaches the Scene Study through the host's reactive push, which does not land in the same tick as the message asking for the link — so resolving on arrival would still miss it.

### What changed

- **The pad builds what it is about to link.** A canvas is a fact about the room, so naming walls as one canvas is asking for them to be in it. `isBuiltShape` asks whether every take a shape produces is already in `built`; anything missing triggers a BUILD, and the footer says so — `1 WALL WAS NOT IN THE SCENE — BUILT IT FIRST` — rather than doing it silently.
- **The Scene Study holds a link request until every wall in it exists.** `requestLink` / `tryPendingLink` keep the named source ids and retry on each take push, up to three. What is still missing after that is NAMED in a toast instead of quietly left out.

### Files and components

- `sketchpad.html` — `isBuiltShape`, the role-menu link action
- `scene-study-3d.html` — `requestLink`, `tryPendingLink`, `IN.linkLeds`, `syncSolids`

### Verification

- Three walls built and linked, then a fourth drawn and NOT built, joined through the real menu item: pad canvases `[3]` → `[4]`, footer `1 WALL WAS NOT IN THE SCENE — BUILT IT FIRST`, Scene Study `CANVAS OF 4`. Before the fix the same sequence left it at 3 in silence.
- The ordering fallback tested on its own: a `linkLeds` naming a wall the scene did not have linked NOTHING on the first push, then linked all three the moment the wall arrived — `[] → [sol-1, sol-2, sol-9]`.

### Pending

- Unchanged from the previous entry.
- JOIN builds everything the pad has pending, not only the walls being joined — `postSolids(true)` is all-or-nothing. Right often enough, and it is announced, but it is a bigger act than the gesture asked for.

## 27 August 2026 — The crop was correct and unreadable

### Requested work

- Cropping in the Scene Study has issues.

### What was wrong, and it was not the geometry

Measured first: the frame's corners sat at canvas u 0.322 and 0.678 — both inside GAPS between screens — and `wallToWorld` extrapolated them 0.44 m and 0.56 m past the neighbouring wall's edge, which is exactly where 6.44 m and 13.56 m across a 20 m canvas are. Projected to screen they bracketed the middle wall correctly. The placement, the hit tests and the drags were all right.

**What was wrong was that none of it could be seen.** `armCrop` added the canvas members to the selection — my own addition, meant as a kindness: "these are the screens you are cropping across". But a selected LED wall has EVERY line in it recoloured to the active accent, cabinet grid included. Three selected walls turn the viewport into a wash of yellow, and the one thing that matters — the picture's own frame, its eight handles and its rotate knob, all also in the accent — is lost in it.

Two more marks were competing in the same colour: the crop's own wall hint, and the link tie bar added earlier the same day.

### What changed

- Arming the crop CLEARS the selection instead of setting it. The crop already draws the walls itself.
- The wall hint is drawn in the meta ink rather than the accent. The mask is not the picture, so it is not the picture's colour — a wall is a boundary and draws like one.
- The link tie is hidden while cropping and comes back on DONE. It and the wall hint say the same thing, and saying it twice in the accent is two more marks in front of the frame.

### Files and components

- `scene-study-3d.html` — `armCrop`, `disarmCrop`, `cropWallMat`, `refreshLinkMarks`

### Verification

- Rendered before and after: the same crop went from a field of yellow grid with handles scattered through it to a clear frame over neutral grey masks.
- All four gestures then driven through the real handlers and measured:
  - CORNER — `w 1.778→2.883`, `h 1.000→1.622` (same ratio, aspect kept) with `x`/`y` still 0: grown about the centre.
  - EDGE — `w 2.883→3.401`, `h` unchanged, `x` moved to +0.104: the opposite edge stayed put, which is cropping that side.
  - BODY — size unchanged, `x`/`y` both moved.
  - KNOB — `0° → 22.7°` with the size untouched.
- The frame extending past the end walls is correct and now legible as such: the picture is larger than the canvas and the part off the screens falls on nothing.

### Pending

- Unchanged: persistence, spill colour, the single-axis canvas on a tight corner wrap, no group box in the 3D, the zero-width camera aspect.
- The earlier note that the crop frame "reads as broken where it crosses a gap" was wrong and is withdrawn — for coplanar screens the extrapolation puts the frame exactly where it belongs and it draws continuous. It would break on a corner wrap, which is the single-axis limitation already listed.

## 26 August 2026 — Where the test suites actually stand

### What changed

Nothing in the panels. This is a note about the ground under them.

### Why

Three of today's entries — the elevation LED draw bug, the crowd's RENDER material, and the crop
becoming a placement with handles — were written and verified in a session working from an earlier
checkout. Their suites were green **against that checkout**:

| suite | assertions |
|---|---|
| `test-crop.mjs` (rewritten for the placement model) | 79 |
| `test-led.mjs` (extended with an Elevation section) | 49 |
| `test-crowd.mjs` | 26 |
| `test-render.mjs` · `test-gizmo.mjs` · `test-pov.mjs` | 49 · 26 · 30 |
| `test-pad.mjs` · `test-pad2.mjs` · `test-zoom.mjs` | 45 · 36 · 20 |
| `hub-full.mjs` · `hub-gizmo.mjs` (the real Hub, agent stub on 3904) | 17 · 12 |

**None of them has been run against the merged files that are now on disk** — the ones that also
carry LINK LEDS, the linked-canvas crop fix, elevation profiles, gizmo SCALE and multi-select. The
crop suite is the one to distrust most: it asserts against a single wall's own canvas, and a linked
route puts a second matrix (`relinkMatrices`) between the placement and the picture that the suite
never sees. Re-running the set against the current files is the first thing worth doing.

### Files and components

- None. `DEVELOPMENT-LOG.md` only.

### Pending

- Re-run every suite against the merged panels and record the result here.
- Extend `test-crop.mjs` with a linked route, so the two crop paths are both covered.
- Headless Chromium still has no video decode; every clip test stands a marker canvas texture in for
  the video, and nobody has yet dragged a real .mp4 around a wall by its corners.

## 27 August 2026 — CROP after a JOIN was cropping one wall of the canvas

### What changed

- **A clip aimed at one screen of a linked canvas is aimed at the canvas.** Normalised in one
  place — `routeMedia` — so a wall joined *after* a clip was sent to it, a clip dropped straight
  onto a member, and a member picked by hand in the ROUTE menu all end up on the group.
- **The crop therefore works on the whole picture after a JOIN**: the frame is drawn across every
  screen of the run, it is fitted to the CANVAS's aspect, the corner gesture grows from the middle,
  and `commitCrop` reaches `relinkMatrices` so dragging it moves what is on the walls.
- **The re-fit no longer depends on the playhead.** `linkLeds` re-fitted the placement and collapsed
  the replicas only for clips that were ACTIVE at that instant, so a link made with the playhead
  parked off the clip did neither. That work is now done for every clip on the way through
  `routeMedia`, whatever the clock says.
- **A copy is lifted too.** `removeLink` leaves the picture replicated across the screens that were a
  canvas; re-joining some of them — without the one holding the route — used to come up dark. The
  copy becomes the new canvas's own picture, and any screen outside the group keeps its copy.
- **The readouts follow the route.** The lane's ROUTE chip and the crop bar's "clip → wall" were
  still naming one screen after a join, and still naming the canvas after an unlink.

### Why

Reported as cropping not working on the linked LED after joining the LED canvas.

`paintLinkedLed` has always honoured a clip left on one member and put it across the whole run —
that is the right behaviour and it is why the join *looks* like it worked. But every other reader
asked the ROUTE what surface this was, and the route still said one wall: `cropFaces` returned one
mesh, `wallCanvas` built that wall's own canvas, `routeAspect` gave that wall's shape, `applyCrop`
answered "not linked" and cover-fitted a 16:9 source to a 3.2:1 wall, and `commitCrop` never found a
group so it never called `relinkMatrices`. So CROP armed itself on one screen of three, drew its
frame at the wrong scale, and dragged a texture matrix that nothing on the walls was reading.

Five readers of one fact, disagreeing with the painter. The fix is not five branches: it is that the
canvas IS the route, said once (`routeCanvas`) and enforced at the one place every change to the
room already passes through.

### Files and components

- `scene-study-3d.html` — `routeCanvas` (new), `routeMedia` (normalisation + readout repaint),
  `linkLeds` (its per-member fiddling removed), `unlinkLeds`, `routeMenu`, `installClip`, `window.SS`

### Verification

Standalone on `:3907`, driven through the real handlers with a clip on `sequence-1`:

| stage | route | crop faces | aspect | chip / crop bar |
|---|---|---|---|---|
| one wall | `led-1` | 1 | 3.20 | LED 1 |
| JOIN led-1 + led-2 | `ledlink-1` | 2 | 6.40 | LINKED ×2 |
| UNLINK | `led-1`, replicate `[led-1, led-2]` | 1 | 3.20 | LED 1 |
| re-JOIN led-2 + mock-led | `ledlink-2`, replicate `[led-1]` | 4 | — | LINKED ×2 |

- The placement arrives contain-fitted and centred on the canvas — `1.78 × 1.00` on a 6.40 canvas,
  `cover: false` — which is the linked default, not the single wall's FILL.
- Dragging the frame (`crop.x → 0.25`, through `commitCrop`) moved **both** members' texture
  matrices, by the 0.45 in u the arithmetic says: one picture, dragged as one.
- FILL on the canvas gives `6.40 × 3.60`, and the frame's world corners span x −11.10 → 3.70 — the
  full 14.8 m of the two walls, hanging off the top and bottom, which is what FILL means on a 6.4:1
  canvas fed a 16:9 clip.
- No console errors on boot or through any of it. `node --check` on the module clean.

### Pending

- Still no video decode in this environment: the clip above is a stub texture, so the numbers are the
  placement's and nothing here proves a frame of picture landed on a pixel.
- The suites in the 26 August note remain un-run against these files, and `test-crop.mjs` is now
  further out of date: it asserts a single wall's canvas, and the linked path is the one that just
  changed. Extending it with a JOIN is the obvious next thing.
- A canvas's id crosses the bridge in `media.route` (as it already did when somebody routed to a
  canvas by hand), and links are per-panel: a Camera POV panel cannot resolve `ledlink-1`, so it
  cannot show what that canvas is playing. Unchanged by this, worth a decision.

## 27 August 2026 — An unlink gives each screen its own clip, and the light panel is three tabs

### What changed

**The unlink splits.** A canvas coming apart used to REPLICATE: one clip, one crop, one lane,
drawn whole on each of the screens that had been the canvas. Now each screen takes the piece of
the picture it was actually showing, as its own clip on its own track — own video element, own
texture, own crop, own lane. The room looks identical at the instant of the unlink, which is the
proof it is a split and not a reset, and from that instant every wall crops by itself.

- **Tracks are asked for, not invented.** An EMPTY lane is used first; only when there is none does
  the tool `post('addTrack')` and finish the fork when the take hands one back — the same two-step
  `pendingDrop` has always used, now with a `pendingForks` queue beside it.
- **A join PARKS what it cannot show.** Two screens each carrying a clip and then joined is a
  collision: `paintLinkedLed` can only show one. The first claim wins and the rest are parked —
  off the wall, still on their own lane, crop intact — and `removeLink` gives them straight back.
  So join → unlink → join → unlink moves one clip in and out of one lane instead of growing the
  timeline every time round.
- **A clip keeps the bytes it was made from**, because a fork needs a second video element and two
  elements cannot share one object URL's lifetime. The Blob already held a copy; this keeps a
  reference to the buffer rather than a second one.
- **The timeline holds more lanes**: rows 22px instead of 26 and the name column 96 instead of 108,
  so the same 168px shows seven lanes rather than six. A clip that shares its file with other lanes
  prints which one it is — `1/3`, `2/3`, `3/3` — because three lanes all saying OPENER.mp4 is the
  split's own work made unreadable. New lanes are scrolled to and selected as they appear.

**The light panel is three tabs.** Ten sliders in one column was a list, and it scrolled. They are
not ten things: they are three sources — the ROOM the show is in, the one hard SUN in it, and the
light the SHOW itself makes — and every trim belongs to exactly one. Each tab has an icon, one line
saying what its dials are for, and three or four rows; inside a tab the labels lose the prefix the
tab already carries (SUN · STRENGTH / ANGLE / HEIGHT / SIZE). GLOW's on/off switch moved next to
the GLOW slider — a bloom amount over a bloom that is off is a dial that does nothing, and the two
were a panel apart. RESET ALL stays in the footer, and the tab survives the rebuild a preset change
forces.

### Why

Reported as: unlinking should make the track unique to that object, so cropping is that LED's alone.

The replica model had one placement behind every copy, so cropping one of those screens cropped all
of them — the wall somebody had just separated out was the one wall they could not work on alone.
There is no way to fix that inside one clip: one clip is one texture and one texture is one matrix.
The fix has to be more clips, which means more tracks, which is why the split asks the take for them.

### Files and components

- `scene-study-3d.html` — new section *8c-2*: `placementOnMember`, `splitPlan`, `applySplit`,
  `forkClip`, `consumePendingForks`, `freeTrack`, `addLocalTrack`, `revealTracks`; plus
  `unlinkLeds`, `removeLink`, `routeMedia` (the parking), `installClip` (`bytes`, `parked`),
  `buildTimeline` (sibling index), the `.tl-*` metrics, `LOOK_TABS` / `openLook`, `#i-screen`
  and `#i-glow`, and the `.menu.panel .tabs` CSS.

### Verification

Standalone on `:3907`, driven through the real handlers, one run start to finish:

| step | result |
|---|---|
| clip on LED 1, CROP armed | route `led-1`, 1 face |
| JOIN LED 1 + LED 2 + LED ARC | route `ledlink-1`, 5 faces, aspect 4.00, bar and chip say LINKED ×3 |
| drag the frame | all three members' matrices moved |
| UNLINK | 3 lanes — LED 1 · LED 2 · LED ARC — labelled 1/3, 2/3, 3/3, each with its own placement |
| crop LED ARC's lane | **only** that clip's matrix changed |
| re-JOIN LED 1 + LED 2 | lane 1 claims the canvas, lane 2 parked, LED ARC untouched, no new track |
| UNLINK again | all three back on their own walls, still 3 tracks, nothing pending |

- The split's arithmetic checks out by hand on the two-wall case: a 16:9 clip contain-fitted to a
  6.40 canvas of two 3.20 walls comes apart as the same picture at `x = +1.00` on the left wall and
  `x = −1.00` on the right — one half-width either side of the join, which is where it was.
- The EMBEDDED half was driven too: a fork queued with no free lane, then a scene push carrying a
  new track — `pendingForks` 1 → 0 and the clip installed on the new lane.
- Light panel: 300 × 261 px and no longer scrolls (it was hitting the 320px cap); a slider drives
  `LOOK.sun` live; RESET ALL resets the trims and stays on the tab you are in; the yellow
  "only in RENDER" line disappears in RENDER.
- No console errors through any of it. `node --check` clean.

### Pending

- Still no video decode here, so every clip in the runs above is a stub texture: the split is proven
  on routes, placements and matrices, and nobody has yet watched a real .mp4 come apart across three
  walls and stay put.
- `clip.bytes` means a clip's file is held in memory twice over its lifetime (Blob + buffer). Fine
  for a prototype with a handful of clips; a real one would keep one Blob and refcount it.
- A parked clip is tool-side, like the links themselves: it does not survive a reload, and the host
  is told only that the track's route is now null.
- The suites still have not been re-run, and `test-crop.mjs` now has two more paths to cover: the
  split's placement conversion and the parking round-trip.

## 27 August 2026 — The split re-fits each screen instead of inheriting the canvas

### What changed

- **An unlink now RESETS each screen's placement**: covered, centred, square, fitted to that
  screen's own aspect. The entry above carried the canvas's placement over — each wall kept the
  exact piece it had been showing — and that is withdrawn. `placementOnMember` is gone;
  `resetPlacement` replaces it.
- **A placement that has never been fitted is fitted when the frame is drawn.** `applyCrop` fits at
  PAINT time, so a lane the playhead has not reached had `w = h = 0` and CROP drew a zero-by-zero
  frame with all eight handles on one pixel. `refreshCropOutline` now fits first. Pre-existing —
  any clip routed while the playhead sat outside it did this — and the split is what made it likely,
  because only the live lanes have painted at the instant of an unlink.
- A parked clip is still not touched: its placement was made on that very wall, in that wall's own
  units, and was never fitted to a canvas.

### Why

Asked for directly: on unlink the cropping should reset to fit the individual LED's dimensions.

And it is the better answer. Pixel-identical across the unlink is a nice property and the wrong one:
a canvas placement is stated in canvas units — 6.4 wide, hanging off the top and bottom, centred on
a join that no longer exists — so inheriting it opens every lane on a fragment scaled to a canvas
that is gone, and the first thing anybody does to all three is reset them by hand. A canvas is a
region a picture lives IN; a screen is a frame the picture belongs full on. The join re-fits in one
direction, so the unlink re-fits in the other.

### Files and components

- `scene-study-3d.html` — `resetPlacement` (replacing `placementOnMember`), `splitPlan`,
  `refreshCropOutline`, the unlink toast, `window.SS`

### Verification

- A clip rotated 0.4 rad and panned to `x 0.35` on a 4.00 canvas, then unlinked: every lane came
  back at `rot 0`, `x 0`, `y 0`, `cover`, sized to its own wall — `3.20 × 1.80` on the two 3.20:1
  walls, `3.67 × 2.06` on the 3.67:1 arc.
- CROP armed on a lane the playhead has never been inside: bar reads `3.67 × 2.06`, the frame's
  corners span the full wall, 14 objects in the crop group. Before this it was `0.00 × 0.00`.
- The lazy fit is kept where it belongs: a lane that has neither painted nor been armed still holds
  an unfitted placement, so the fit uses the video's real aspect once it is known rather than the
  16:9 fallback.
- No console errors. `node --check` clean.

## 27 August 2026 — A real sky for NIGHT, weighed against the gradient it replaces

### What changed

- **RENDER can light the room with a real radiance map.** A preset may now name an `hdr`, and
  NIGHT names `HDR/dikhololo_night_2k.hdr` — 2048 × 1024, loaded once, PMREM'd exactly as the
  generated skies are, so it lights the crowd, the deck and the truss from every direction and
  the audience's speculars finally have something with SHAPE to reflect.
- **The generated sky stays, as the fallback in three senses**: what a preset without an `hdr`
  uses, what is shown while one downloads, and what is shown if the download fails. Picking
  NIGHT is instant and gets better a moment later; nothing waits on 7 MB.
- **`RGBELoader` is imported dynamically**, so a session that never asks for a real sky never
  downloads the loader, and a boot with no route to the CDN still boots.
- **A loaded map is WEIGHED against the sky it stands in for** — `skyLum`: mean luminance over
  the sphere, weighted by solid angle, because a row near the zenith covers far less sphere
  than a row at the horizon. The ratio becomes the map's gain, and every place brightness is
  set multiplies by it.
- The ROOM tab marks a preset that has a real sky with a dot, and names the file in its tooltip.
  The load toast prints the measured gain.
- Failure is named, not swallowed: from `file://` a fetch of a sibling `.hdr` is cross-origin and
  Chrome refuses it, so the toast says so and gives the one line of shell that fixes it.

### Why

Asked for: an HDR sky map for the environment on RENDER, NIGHT loading that file.

**And then the interesting half.** Dropped in at the preset's own `env`, the map lit the room
roughly five times too hard: the floor went white, the rig lost its edges and the night read as
an overcast afternoon. The map is not at fault and neither were the presets — a gradient's
numbers were tuned by eye against this rig and a radiance map's are absolute radiance. Measured,
`dikhololo_night_2k` weighs **0.084** over the sphere against the night gradient's **0.027**:
three times the light, and the preset's `env: 0.55` was multiplying that instead of correcting
for it.

That is a ratio, not a taste, so it is measured rather than guessed — which also means the next
.hdr anybody drops into a preset is calibrated by arithmetic on load instead of by eye over an
afternoon. The preset's own numbers go on meaning what they said, and the ENVIRONMENT trim's
100% is still "as the preset says", whichever sky is behind it. `lift` is there for taste, and
its only defensible default is 1.

### Files and components

- `scene-study-3d.html` — the `ENVS` note and `night.hdr`, `skyLum`, `hdrFor`, `hdrGain`,
  `hdrTex` / `hdrState`, `applyEnvironment`, `applyEnvAmount`, `paintBg`, `envLive`, the env
  pills in `openLook` and their CSS, `window.SS`
- `HDR/dikhololo_night_2k.hdr` — 7.0 MB, and `HDR/syferfontein_6d_clear_2k.hdr` — 6.3 MB,
  both served from the project folder

### Verification

Standalone on `:3907`, RENDER on, NIGHT selected:

| | |
|---|---|
| loaded | 2048 × 1024, HalfFloat, equirect, linear |
| measured luminance | 0.0841 over the sphere (the gradient it replaces: 0.0266) |
| gain | ×0.317 — and `environmentIntensity` lands at 0.174 = `0.55 × 0.317` |
| ENVIRONMENT at 200% | 0.348, exactly twice — the trim still means what it says |
| switch to GREY STUDIO and back | same cached texture, still alive, gain reapplied, no second download |
| a preset pointed at a missing file | state `failed`, the gradient on screen, dusk's own `env` restored |

- The same `skyLum` reading comes off the HalfFloat and Float32 versions of the file (0.0841
  both ways), which is what says the half-float decode in it is right.
- Before and after are unmistakable in a screenshot: a flat white-grey wash with the rig barely
  visible, against a dark night with cloud shape in the sky and the horizon glow reflected in
  the floor.
- No console errors. `node --check` clean.

### And DAYLIGHT, which arrived mid-session

`syferfontein_6d_clear_2k.hdr` appeared in `HDR/` while this was being written, and a clear-sky
map has exactly one preset it can be, so DAYLIGHT names it — a cloudless day is the case a
gradient cannot do at all: a small hard sun and a graded dome, with everything on the deck
reading by which of the two it caught.

It weighs **0.365** against that gradient's 0.400, so the gain is **×1.10** and DAYLIGHT is as
bright as DAYLIGHT already was. Which is the finding worth writing down: DAYLIGHT is blown out,
and it was blown out before this — the generated gradient and the real sky produce the same
white haze in the same frame, because `env: 1.25` on a sky that weighs 0.4 is thirty times the
night preset's floor of light. That is a preset to re-tune, not a map to blame, and it is not
part of this.

### Pending

- **DAYLIGHT's own level.** See above: it needs re-tuning, at which point the real sky will
  follow it automatically, because the gain is a ratio and not a brightness.
- The floor's specular reflection of a bright horizon band is the strongest thing in the frame
  now. It is physically what a glossy deck under that sky does, but `renderReflection` tone-maps
  its target and the result is tone-mapped again on the way out, so bright reflections are
  probably exaggerated. Worth a look, and not part of this.
- NIGHT and DAYLIGHT have real skies. The other four are still gradients; each one is a file
  and a licence away, and the gain machinery means adding one is now two lines.
- The map is fetched per panel: two panels of the same take on NIGHT download it twice. The
  browser's cache covers the second, but the bytes do not travel over the bridge the way a
  `.glb` or an `.mp4` does.

## 27 August 2026 — The map is the light: read it, reveal it, and let the folder be the list

### What changed

**The map was upside down, and that is why nothing found the moon.** A `.hdr` stores its
scanlines from the top, so its first row is the zenith; three samples an equirect with
`v = asin(dir.y)/pi + 0.5` and a DataTexture is not flipped on upload, so v = 0 is data row 0
and v = 0 is straight DOWN. Opposite conventions: every loaded sky was on its head, the
ground overhead and the moon of a moonlit night below the horizon. `flipY` is not the fix —
WebGL ignores UNPACK_FLIP_Y for ArrayBufferView uploads — so `flipSkyRows` turns the rows over
once on load, after which the map, the generated skies, three's shader and everything that
reads them mean the same thing by "up". `buildSky` was bitten by exactly this once and carries
the note; this is the same bug arriving through the other door.

**A map is READ now, not just sampled.** `skyMeasure` returns four things in one pass:

| | |
|---|---|
| `lum` | mean luminance over the sphere, solid-angle weighted (the gain, as before) |
| `sky` / `ground` | the mean colour of each hemisphere — which is what an ambient pair IS |
| `dir` | where the light comes from: the brightest sample if the map holds a disc, otherwise the luminance-weighted centroid of the whole sphere |
| `dir.tint` | the colour found there, normalised, so a sodium horizon aims a sodium key |

**ENVIRONMENT reveals the map.** The trim moved the light only, which made it a slider whose
effect you could not see unless something shiny happened to be in frame. It now brings the sky
up with it: 0% is no sky at all — the flat colour, not a dimmed rectangle, because a horizon
line at 2% is a seam across the frame — and 100% is the map as it is. Past 100% the light goes
on climbing and the sky stays fully visible, which is what the headroom to 200% is for. The
bounce and the key ride the same number, because they are the same sky.

**The map is the ambient.** RENDER's hemisphere pair was two hex values typed by hand — a cool
sky over a navy ground, identical in a stadium at dusk and under a clear noon — at a fixed
0.09. It is now the map's own two hemispheres at `pi * radiance * 0.34`: pi because that is
what turns radiance into the irradiance a hemisphere light is measured in, and a third because
this is the bounce and the IBL is already lighting everything the map faces. The old constant
was **six times brighter than a night sky's entire light** (0.09 against 0.015), so the
hardcoded pair was the room's main source and the environment was a tint on it. A night now
reads as a night, and what lights the show is the show's own key.

**The map aims the key.** The one shadow-casting source takes its BEARING and its COLOUR off
the map — and its height too, until somebody touches SUN HEIGHT, which is an override and stays
one. Its intensity stays authored: a map's peak is absolute radiance and a moon at 216 would
put a noon key in a night scene. What the map decides is where the light is and what colour it
is; how much of it there is remains a decision.

**The HDR folder is the list of skies.** Naming one file in one preset was fine for one file
and is not a system. On the first press of RENDER the tool reads `HDR/` and every map becomes a
preset, named after the file, built on the template its filename points at — night, dusk,
sunrise, overcast, arena, and a clear day for anything unrecognised — so it arrives with a
sensible key, a sensible trim, and a gradient to stand in for it while it loads and to be
weighed against when it lands. It costs ONE request: the listing, and the manifest
(`HDR/index.json`) only if the listing mentions one — a 404 printed on every boot is a tool
crying wolf about its own design. A file a preset has already claimed by hand is skipped, so
NIGHT stays wired to `dikhololo_night_2k` and does not also appear twice.

**Two levels changed, both because they were measured.**
- DAYLIGHT's `env` 1.25 → 0.45 and its sun 3.2 → 1.6. That sky weighs 0.40 over the sphere, so
  1.25 asked for 0.50 of mean radiance and ACES at the fixed 1.25 exposure saturates not far
  above it — before a 3.2 sun and a bounce pair are added. It read as an overexposed photograph
  rather than a bright day, and it is the template every unrecognised map is built on, so it
  had to mean something. 0.45 puts the mean at 0.18, where a grey card sits.
- DAYLIGHT also gave up its claim on `syferfontein_6d_clear_2k`. Read, that map's sun is **8
  degrees** above the horizon and the colour of it is [1, 0.76, 0.27]: it is a golden hour, not
  a midday, and a preset called DAYLIGHT showing it would be the label lying about the light.
  The folder names it correctly by itself.

Also: every slider in the light panel now carries a one-line title saying what it does.

### Files and components

- `scene-study-3d.html` — `flipSkyRows`, `skyMeasure` (replacing `skyLum`, kept as a wrapper),
  `skyRead`, `envReveal`, `applySkyLights`, `HEMI_WORK`, `aimSun`, `paintBg`, `applyEnvAmount`,
  `applyEnvironment`, `SKY_DIR` / `SKY_KINDS` / `skyLabel` / `skyKey` / `skyPresetFor` /
  `discoverSkies`, the `daylight` preset, `LOOK_ROWS` tips, `window.SS`

### Verification

Standalone on `:3907`, RENDER on, both maps read:

| | NIGHT · dikhololo | discovered · syferfontein 6d clear |
|---|---|---|
| weighed | 0.0841 → gain ×0.317 | 0.365 → gain ×1.10 |
| sky hemisphere | 0.176 / 0.155 / 0.131 | 0.565 / 0.651 / 0.711 (blue) |
| ground hemisphere | 0.016 / 0.009 / 0.005 | 0.137 / 0.084 / 0.040 (warm earth) |
| light found | a disc, 37° up, bearing −125°, tint [0.71, 0.92, 1.00] | a disc, 8° up, bearing 55°, tint [1.00, 0.76, 0.27] |
| ambient pair | #fff1e0 over #ffc992 at 0.0156 | at 0.192 |

- Sky above and ground below in both, and the moon 37° UP: before the flip that same map
  measured its bright half as the lower hemisphere and its peak search above the horizon found
  0.1 — the moon was under the floor.
- A row-band scan of the clear-sky map confirms the horizon: mean rises from 0.042 at the nadir
  to 1.279 with a peak of 419 just above the middle, then falls to 0.14 at the zenith.
- The reveal, driven through the real slider: **0%** → background is a flat colour (not a
  texture), `environmentIntensity` 0, hemisphere 0, sun down to its 6% floor. **200%** → env
  0.348, hemisphere 0.031, sun full, background still 0.317 — visible, not more than visible.
- Discovery: `sky:syferfontein_6d_clear_2k` appears as the pill SYFERFONTEIN 6D CLEAR with the
  real-sky dot and the filename in its tooltip, selecting it loads and lights, and the network
  log for a clean boot shows `HDR/` and the map — no `index.json`, no 404.
- `node --check` clean; no console errors from a clean load.

### Pending

- STUDIO and ARENA have not been re-levelled. Nothing is wired to them, but they are templates
  for `overcast|studio` and `arena|indoor` filenames, so the first map named that way will
  inherit whatever they are worth — worth measuring the same way DAYLIGHT just was.
- The exposure is still a constant 1.25 for every preset. An auto-exposure driven by the
  measured irradiance is the obvious next thing and deliberately not done here: the LED walls
  are judged against the room in that frame, and changing exposure per sky would change what
  LED DRIVE means between presets.
- A discovered preset's key is `sky:<filename>`, which two panels of the same take agree on
  because they read the same folder — but a look published before the other panel has
  discovered is ignored rather than queued.
- The manifest is read and never written. `HDR/index.json` is the place to name a sky properly
  or keep one out of the row, and nothing in the tool offers to make one.

## 27 August 2026 — "The sky is not visible": a plate, a gain, and an undeclared uniform

### What changed

Three separate things were hiding the map, and only the third was a bug.

**1 · THE GROUND WAS IN FRONT OF IT.** The render floor is a 4000 m plate at y = 0. At the view
this panel opens with — 28 m up, pitched 26 degrees down, a 38 degree lens — that plate fills the
frame to SEVEN DEGREES BELOW the skyline, so a sky could be loaded, weighed, read, aimed at the
rig and lighting every surface, and still not appear in one pixel. Measured by raycasting a grid
over the frame: sky fraction **zero**. So the ground now FADES: solid out to a radius sized off
the room and gone by three times it (24 m and 65 m in the mock's concert stage), which is how an
HDRI-lit shot is always put together — the floor is there to catch the shadow and carry the
reflection, and the far field is the environment itself. Only in RENDER, and only when there is
an environment: in BLACK the plate stays a plate, because fading it would reveal the flat
background behind it.

**2 · AND IT WAS BEING SHOWN AT A THIRD OF ITS BRIGHTNESS.** The gain exists to make a map
deliver the same LIGHT as the gradient it replaces. It was also being applied to the backdrop —
so dikhololo, which weighs three times the night gradient, was drawn at 0.32: a black rectangle
with a faint seam where the horizon is. A backdrop is a PICTURE, not a lamp. It is now shown at
what the map holds, and the light stays calibrated separately.

**3 · THE SHADER DID NOT COMPILE.** The fade was injected into the floor's fragment shader
without declaring its three uniforms in the same shader's header, so three logged
`'uGroundOn' : undeclared identifier`, the program failed, and the ground did not fade. Every
symptom pointed at the sky; the fault was in the floor. An unused uniform declaration costs
nothing and an undeclared one costs the whole program, so all three are declared for every
reflective material and read by the one that fades.

**.EXR AS WELL AS .HDR.** Radiance and OpenEXR are two containers for the same thing — linear
radiance, above 1.0 where the light is — and the loader is picked off the extension. Both arrive
as a linear float DataTexture, both are turned over, both are weighed, and the EXR loader is only
downloaded if a file needs it. Suggested as a workaround for `.hdr` not working; `.hdr` was
working, and this is worth having anyway because half of every HDRI library is EXR.

**A load says so when it starts.** 7 MB at 2k is a blink and 91 MB at 8k is eight seconds of the
gradient sitting there looking like the answer.

### Verification

Standalone on `:3907`, the folder as it stands — and it filled up while this was being written,
which is the discovery system's own test:

| file | format | size | weighed | light found |
|---|---|---|---|---|
| `dikhololo_night_2k.hdr` | Radiance | 2048 × 1024 | ×0.32 | disc, 37° up |
| `syferfontein_6d_clear_2k.hdr` | Radiance | 2048 × 1024 | ×1.10 | disc, 8° up, warm |
| `moonless_golf_4k.exr` | OpenEXR | 4096 × 2048 | ×0.25 | disc, 8° up |
| `table_mountain_1_4k.exr` | OpenEXR | 4096 × 2048 | — | — |
| `dusk.hdr` | Radiance | **8000 × 4000**, 91 MB | ×2.01 | disc, 8° up |

- All five appear as pills without being named in code; the two EXRs were classified by filename
  onto the night and daylight templates, and `dusk.hdr` onto dusk.
- The 8k, 91 MB map loads, measures and renders in **8.0 s** with no console error and no crash.
- The fade, proven by reading the frame back out of a render target rather than by eye: with
  `uGroundOn` at 1 the top of frame is [87, 86, 79] and the band under it [166, 159, 147] — sky
  and cloud; at 0 the same pixels are [49, 43, 37] and [43, 39, 35] — plate.
- A clean load in RENDER on NIGHT: no console errors, and the map is visible as a picture —
  tree silhouettes, cloud, the horizon glow, the stage on its own patch of ground.

### Files and components

- `scene-study-3d.html` — `FLOOR_U` (three ground uniforms, declared and used),
  `reflectionMaterial`, `applyGroundFade`, the `renderFloor` material, `paintBg`, `hdrFor`
  (EXR + the loading toast), `skyLabel` / `skyKey` / the listing filter

### Pending

- **The sky can now read brighter than the light in the room implies**, because the backdrop is
  the map's own values and the light is the preset's. That incoherence is the price of the map
  being visible at all, and the lever is ENVIRONMENT: above 100% it raises the light without
  touching the sky. If it ever needs resolving properly, the answer is an exposure driven by the
  measured irradiance, which is the note two entries up.
- Nothing downsamples a very large map. 8k at half-float is about 260 MB on the GPU and it
  worked here; 16k would be four times that and would not.
- The fade radius is read off the venue bounds, so a take with no venue gets the 34 m default.
  A very wide stadium floor plus a low camera can still put the fade edge in shot.

## 27 August 2026 — The folder in the menu, and the 404 that was never the tool

### What changed

**THE PYTHON ERROR WAS `favicon.ico`.** `python3 -m http.server` prints
`code 404, message File not found` for `/favicon.ico` on every page load, because no browser
can help asking for one and nobody ever made one. It reads as the tool erroring, on every
reload, right underneath the requests that matter. A `<link rel="icon" href="data:,">` is a
favicon, so the browser stops asking. Nothing about the HDRs was ever in that log — the
requests for the maps are all `200`.

**THE MENU DID NOT LIST THE FOLDER UNTIL RENDER WAS PRESSED.** Discovery ran on the first
press of RENDER, on the argument that the working view has no environment so the folder is
nobody's business yet. That argument is wrong in the one way that matters: **the pill row IS
the folder**, so anybody who opened the light panel first — which is the obvious order, you
choose a look and then look at it — saw six built-in presets and no sign that five real skies
were sitting next to the file. It is now read at boot and again whenever the panel opens
(idempotent, one request), so the row is right the first time it is seen.

**ALL FIVE MAPS ARE IN THE MENU, `.hdr` AND `.exr` ALIKE**, in two labelled groups: `from HDR/`
first — the row somebody who has just dropped a file in is looking for — then `generated`.

**EACH PILL SAYS WHERE ITS SKY IS UP TO**: `○` not loaded, `◌` loading, `●` on screen, `✕`
could not be read. A map is a download of 7 to 91 MB, so a preset backed by one is in a state,
and that state is the answer to "why does it still look like the gradient".

**AND THE PANEL SAYS WHAT THE FOLDER GAVE IT** — "5 maps in HDR/", or the reason there are
none: unreachable, no listing and no manifest, or the page being on `file://`, which is named
with the one line of shell that fixes it. Every version of "the map does not show" so far has
had a different cause and every one of them was invisible from inside the panel.

**A MAP NAMED AFTER A PRESET IS THAT PRESET'S SKY.** `dusk.hdr` made a second pill also called
DUSK, next to the gradient one — the tool asking a question instead of answering it. Somebody
who names a file `dusk` means the dusk preset, and standing in until a real one arrived was the
gradient's whole job. Wired in; only a name that matches nothing becomes a preset of its own.

**`HDR/index.json` is written**, and MERGED with the directory listing rather than preferred.
Preferring it was a trap with the same shape as the one this system exists to remove: a manifest
written today would quietly hide the map dropped in tomorrow. Regenerate it with:

```sh
cd ~/Documents/Productions/5.8 && python3 -c "import json,os;print(json.dumps(sorted(f for f in os.listdir('HDR') if f.lower().endswith(('.hdr','.exr')) and not f.startswith('.')),indent=2))" > HDR/index.json
```

### Verification

- **Standalone**, panel opened WITHOUT pressing RENDER first: `from HDR/` lists NIGHT ·
  DUSK · MOONLESS GOLF · SYFERFONTEIN 6D CLEAR · TABLE MOUNTAIN 1, `generated` lists BLACK ·
  ARENA BOWL · GREY STUDIO · DAYLIGHT, and the note reads "5 maps in HDR/". One DUSK, not two.
- **In the Hub**, same folder, the tool in its iframe at `scene-study-3d.html?mode=scene`: the
  same five maps, NIGHT selected, its pill goes `○` → `●`, and the map is on screen in the
  panel — verified with the take empty, so what is in the viewport is nothing but sky.
- The server log for a clean load is now the requests and nothing else: no favicon 404, no
  `index.json` probe (the listing names it), and `200` for the map.

### Files and components

- `scene-study-3d.html` — the favicon link, `discoverSkies` (boot + panel open, merged
  manifest, attach-by-name, `skiesNote`), `openLook` (two pill groups, `skyMark`, the note),
  `.pillrow` / `.skynote` CSS
- `HDR/index.json` — new, five entries

### Pending

- If a map still does not show, the note line in the ROOM tab now names the reason. The one
  cause it can only report and not fix is `file://`: Chrome refuses every fetch from a
  file:// page, so neither the folder nor the maps can be read there, and no amount of code
  changes that.
- The ROOM tab scrolls now that it carries two pill groups and three sliders. Fine at five
  maps; at twenty it wants its own list.

## 27 August 2026 — /HDR, and the folder deciding what the presets are

### What changed

**THE FOLDER IS LOOKED FOR IN MORE THAN ONE PLACE.** `HDR/` is relative to the document, which
is right when the page and the folder sit side by side — the standalone file and the Hub's
iframe both do. `/HDR/` is relative to the SERVER ROOT, which is right when the root is the
project and the page is reached by some other path. Reported as `/HDR`, so both are tried in
turn, plus a `?sky=/any/path/` override, and the first one that answers WITH MAPS IN IT becomes
the folder for the session. A folder that answers but is empty is not the folder, or an empty
`HDR` at a server root would shadow the real one beside the page. The panel prints which paths
were tried when it finds nothing, because a wrong path produces an empty pill row and an empty
pill row looks nothing like a wrong path.

**A HAND-WIRED MAP THAT IS NO LONGER IN THE FOLDER IS DROPPED.** NIGHT was wired by hand to
`dikhololo_night_2k.hdr`. Rename that file and the preset went on claiming a map that does not
exist — a pill with a cross on it, and a preset that could not be handed the file now sitting in
the folder under a better name. The folder is the truth about what is gone as well as what is
there.

**A MAP NAMED AFTER A PRESET IS THAT PRESET'S SKY** — exactly, or as the START of its name.
`night.hdr` is NIGHT and `day.exr` is DAYLIGHT, both obviously meant. The file's name has to be
the prefix and not the other way round, or every numbered variant would swallow the preset it is
a variant of: `night2.exr` is not NIGHT, and becomes its own preset. So a folder of five files
named for what is in them produces exactly five presets and no duplicates:

| pill | file | how |
|---|---|---|
| NIGHT | `night.hdr` | exact name |
| DUSK | `dusk.hdr` | exact name |
| DAYLIGHT | `day.exr` | name is the start of the preset's |
| NIGHT2 | `night2.exr` | its own preset, on the night template |
| TWILIGHT | `twilight.hdr` | its own preset, on the dusk template |

**AND THE FAVICON 404 IS ACTUALLY GONE.** Declaring `<link rel="icon" href="data:,">` did not
stop it: `data:,` is an empty text/plain document, Chrome rejects it as an image and falls back
to `/favicon.ico`. The link is now a real 1x1 PNG, and — because Chrome asks for the file
anyway in some contexts — there is now a `favicon.ico` in the project: 112 bytes, the app's own
dark surface with the accent dot on it, built by hand in the log entry's own script rather than
downloaded from anywhere. The server log for a clean load is now the page, the folder, the
manifest and the map, all `200`, and nothing else.

### Verification

- Served at the root, page at `/scene-study-3d.html`: note reads **"5 maps in HDR/"**.
- Served so that the page is at `/panels/scene-study-3d.html` with no sibling folder — the
  sub-path case, reproduced with a symlink and then removed — note reads **"5 maps in /HDR/"**,
  same five presets. That is the fallback doing its job.
- `from HDR/` lists NIGHT · DUSK · DAYLIGHT · NIGHT2 · TWILIGHT; `generated` lists BLACK ·
  ARENA BOWL · GREY STUDIO. One NIGHT, one DUSK, one DAYLIGHT.
- NIGHT (`night.hdr`, 7 MB) and TWILIGHT (`twilight.hdr`, 8000 x 4000, 91 MB) both render as
  visible maps behind the rig, and the pill goes from ring to filled dot as each lands.
- Server log, clean load: `200` for the page, `/HDR/`, `/HDR/index.json`, the map, and the
  favicon. No 404 of any kind.

### Files and components

- `scene-study-3d.html` — `SKY_DIR` / `SKY_DIRS` / `askDir`, `hdrUrl` (a preset stores its
  FILE, not a path), stale-claim pruning and prefix matching in `discoverSkies`, the favicon link
- `favicon.ico` — new, 112 bytes
- `HDR/index.json` — regenerated for the renamed files

### Pending

- The candidate list is two paths and an override. A project served under a deep path with the
  maps somewhere else again needs `?sky=`, and nothing in the UI offers to set it.
- `index.json` is written by hand (the one-liner is in the entry above). Renaming the files makes
  it stale — harmless, because it is merged with the listing rather than trusted over it, but a
  stale manifest on a server with listings OFF would still be wrong.

## 27 August 2026 — Choosing a sky is a request to see it

### What changed

**PICKING A SKY NOW TURNS RENDER ON.** This is the whole of "it still doesn't load". `envLive()`
requires the preview — the working view is a diagram with a grid for a floor and no environment
at all — so choosing a sky in the working view set a variable and did nothing else: no light, no
backdrop, **no download even started**. The panel said so in one yellow line, and that line lost
three times over to the reasonable expectation that choosing a sky shows you the sky. So the
choice now brings the lit view with it, in one toast: *"NIGHT · OPEN AIR · RENDER on — a sky only
exists in the lit view — key trimmed to 85%"*. A look arriving from another panel does not do
this (`setEnv`'s quiet flag) — one panel's choice must not drag another into RENDER.

**THE PANEL COUNTS THE DOWNLOAD.** `loading night.hdr — 100% of 6.7 MB`, patched into the note
line in place rather than by rebuilding the menu. Twenty seconds of silence on a 91 MB map is
indistinguishable from a map that is never coming, and that is most of what this has been.

**A MAP OVER 4k IS HALVED BEFORE IT REACHES THE GPU.** `twilight.hdr` is 8000 × 4000 — about
260 MB of half-float texture and a PMREM pass over all of it. Halved to 4000 × 2000 it is a
quarter of that and indistinguishable behind a backdrop blur in a panel this size. Box-averaged
2 × 2, which preserves the total light exactly, and — the part that matters — the READING is
taken at full resolution BEFORE the halving, because an average spreads a sun disc over its
neighbours and would cost the peak that finds the key. Measured both ways: `lum` 0.0661 and gain
×2.01, identical before and after.

**AND THE FAVICON IS HIS NOW.** A proper icon set arrived in `favicon/` — svg, 96px png,
apple-touch — so the links point at those, and `favicon/favicon.ico` is copied to the project
root because a browser asks for `/favicon.ico` by path whatever the document declares. The
112-byte placeholder built here yesterday is gone.

### Verification

Driven exactly as a first-time user does — open the light panel from the WORKING view, pick a
sky, touch nothing else:

| | |
|---|---|
| RENDER button | `RENDER` → `WORKING VIEW`: the preview came on by itself |
| note line | `loading night.hdr — 100% of 6.7 MB`, then `5 maps in HDR/` |
| pill | `NIGHT ○` → `●` |
| viewport | the map: tree silhouettes, cloud, the horizon glow, the rig standing in it |

- `twilight.hdr` (8k, 91 MB): note line counted to 100% of 86.8 MB, texture landed at
  4000 × 2000, gain ×2.01 unchanged, and the violet dusk is on screen behind the rig.
- Server log for a clean load: page, `/HDR/`, `index.json`, the map, favicon — every one `200`.

### Files and components

- `scene-study-3d.html` — `setEnv` (auto-RENDER + one merged toast), `hdrProg` and the loader's
  `onProgress`, `halveSkyTo`, the favicon links
- `favicon.ico` — replaced with the real one from `favicon/`

### Pending

- The auto-RENDER is one-way: leaving RENDER does not put the sky back to BLACK, because the
  preset is a choice and the view is a view. That is the right asymmetry but it is worth
  watching — a working view that remembers a sky it cannot show is a small surprise waiting.
- The cap is 4096 and the reading is taken before it. A 16k map would be read at 16k, which is
  8 seconds of arithmetic on the main thread before anything appears.
- `localhost:3904` CORS errors in the console are the Sketch Pad's agent health check with no
  agent running. Nothing to do with the skies, and not from this file.

## 27 August 2026 — A simulation of the map, and a loader on every pill

### What changed

**THE STAND-IN IS NOW A SIMULATION OF THAT MAP, not a generic gradient.** A real sky is 7 to
91 MB and something has to be on the walls meanwhile. Until now that was the preset's own
gradient — a generic night, a generic dusk — which meant the room's LIGHT changed when the map
landed, sometimes by three times. Two skies for one preset, and a jump between them.

So every real load leaves its reading behind — sphere-weighted luminance, both hemisphere
colours, where the light comes from and what colour it is — and a sky drawn from those four
numbers is the map: at the map's brightness, in the map's colours, with its sun in the right
place. Unrecognisable next to the photograph and identical in every respect the LIGHTING depends
on. Where a reading comes from, in order: the manifest if whoever wrote it put the numbers in,
this browser's memory of every map it has ever measured, and failing both the kind the filename
points at — which is where this started and is now only the first sight of a file nobody has
ever opened.

**AND THE PILL IS THE LOADER.** A ring that fills as the bytes arrive — `○ ◔ ◑ ◕ ●` — so every
map in the row shows its own progress at once, in one character, with no layout to reflow. A
cross is a map that could not be read; a plain ring on a map-backed pill means measured and
being simulated. The note line under the row counts the one you are waiting for:
`loading dusk.hdr — 100% of 6.0 MB`. Patched in place, not by rebuilding the menu — a ring that
fills twenty times a second inside a panel that redraws itself is a panel nobody can click.

**AND THE FOLDER GETS LEARNED, ONCE.** A background queue loads every map the browser has never
measured, one at a time, only in RENDER — to LEARN the folder, not to hoard it. After the first
session every map in the row can be simulated the instant it is picked, and the download only
sharpens the picture. A map the user picks jumps the queue by definition, because picking it
calls the loader directly.

**Also fixed: `pumpSkies is not defined`.** The previous patch landed the queue's CALLERS and
lost its definitions — a write that never happened because the same script threw on a later
edit — so entering RENDER threw inside `applyRenderOverlays`, before the line that updates the
button. Which is why the tool sat in a state no user could explain: `renderPreview` true, the
button still saying RENDER, and no map ever requested. `node --check` cannot see an undefined
reference, so there is now a static scan for it in the verification below.

### Verification

Memory wiped, then a sky picked from the WORKING view — the first-sight case:

- RENDER came on by itself, the pill went `○ → ◔ → ●`, the note counted
  `loading night.hdr — 45% of 6.7 MB`, and the map appeared. No errors on `window.onerror`.
- The queue then measured `dusk.hdr`, `day.exr` and `night2.exr` on its own, one at a time,
  without being asked, and all four readings are in `localStorage`.

Then reloaded, so the readings are remembered and nothing is downloaded, and DUSK picked:

| | simulation, before any bytes | the map, landed |
|---|---|---|
| `environmentIntensity` | 0.2922 | **0.2922** |
| hemisphere (the bounce) | 0.1138 | **0.1138** |
| sun | 2.1, `#ffe28e` | **2.1, `#ffe28e`** |
| `backgroundIntensity` | 1.0 | **1.0** |
| reading behind it | lum 0.3646, sky [0.565, 0.651, 0.711], light 8° up | identical |

Every lighting number identical across the swap; the only thing that changed is the picture
sharpening from a gradient into the photograph. That is the whole of what this entry is for.

- A static scan for names used but never defined (the `pumpSkies` class of fault) over every
  function this session introduced: clean.

### Files and components

- `scene-study-3d.html` — `SKY_MEM` / `skyRemember` / `skyRecall` / `skySimOf`, `simPreset`,
  `buildSimSky`, `envSim` / `envSimGain` and their use in `applyEnvironment`, `skyRead`,
  `hdrGain`, `skyQueue` / `queueSkies` / `pumpSkies`, `paintSkyPill`, the ring in `skyMark`

### Pending

- The manifest could carry the readings, so a browser that has never seen the folder still gets
  exact simulations. Nothing writes them there yet — the numbers are in the dev log line after
  each load, ready to be copied in.
- A reading is remembered per FILENAME. Replace a file with different content under the same
  name and the first pick of it is simulated wrongly, until it lands and overwrites the memory.
  Keying on size as well would fix it and has not been done.
- The queue is silent about itself. Five maps learning in the background is five downloads with
  no indication beyond the rings quietly filling in a panel that may not be open.

## 27 August 2026 — "Nothing has changed" was literally true: the panel was running an older file

### What this entry is

Four rounds of "it still doesn't work" against a tool that worked in every test. So this time the
question asked was not *what is broken in the code* but *what is reaching the browser*, and the
answer was: not the code.

| checked | found |
|---|---|
| both running servers' working directory | `/Users/igorpancaldi/Documents/Productions/5.8` — correct |
| the file each one serves | contains `buildSimSky`, `paintSkyPill`, `pumpSkies` — 12 matches, correct |
| other copies of the tool on disk | five, all in older project folders, none newer than 24 Aug |
| the tool loaded fresh in a browser | works: five maps in the menu, sky on stage, no errors |

Which leaves the one thing a developer cannot see from the outside: a tab open since before the
edit. The Hub already knows about this — `TOOL_STAMP` busts the iframe URL on every Hub load and
there is a RELOAD TOOL button whose tooltip says *"use this after editing the tool, the browser
will not do it on its own"*. That mechanism only helps if the HUB itself is reloaded.

### What changed, so it cannot happen again

- **`BUILD` is printed in the light panel**, bottom left, beside RESET ALL: `build 27 Aug 18:25`.
  One line that settles "has this file changed" in a glance. If the stamp is older than the edit,
  the tool on screen is not the tool on disk and a reload is the whole fix.
- **`serve.py`** — a dev server that sends `no-store, no-cache, must-revalidate` on everything
  and keeps directory listings on (the sky discovery needs them). `python3 serve.py 8731`. With
  it, every reload is a real reload and this class of ghost is gone.

### Verification

Served through `serve.py`, loaded once, and driven exactly as a user would:

- The panel prints `build 27 Aug 18:25` and `5 maps in HDR/`; the row is NIGHT · DUSK ·
  DAYLIGHT · NIGHT2 · TWILIGHT over BLACK · ARENA BOWL · GREY STUDIO.
- TWILIGHT picked from the WORKING view: RENDER came on by itself, the note counted
  `loading twilight.hdr — 5% … 100% of 86.8 MB`, **and a warm dusk sky was already on stage at
  5%** — the simulation — with the photograph replacing it at 100%, halved to 4000 × 2000.
- `window.onerror` empty throughout.
- Response headers confirmed `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`,
  and `HDR/` still lists.

### Pending

- The stamp is written by hand at edit time. It is honest but it is not automatic, so an edit
  that forgets to touch it leaves the stamp lying — the same fault it exists to catch.


## 27 August 2026 — file://, and a filename that outlived its file

### The report that solved it

> NIGHT · OPEN AIR — could not load HDR/dikhololo_night_2k.hdr · a file:// page cannot fetch it
> — serve the folder (python3 -m http.server 3900)

One line, two faults, both named in it, and neither one guessable from this side of the screen.

**1 · The page is a `file://` document.** Chrome refuses every request a local page makes: not
the folder, not the maps, nothing. So `discoverSkies` finds nothing, no map-backed preset can
exist, and every explanation printed in the panel was correct and useless. No code change makes
a local page able to fetch.

**But a file the USER PICKS is not a fetch.** So the panel now has `+ LOAD .HDR / .EXR…` under
the pill rows, and `loadSkyFile` takes the bytes straight from the file — `file.arrayBuffer()`
into `RGBELoader.parse` or `EXRLoader.parse`, which is what those loaders' own `load` calls once
the bytes are in hand. Same decode, shorter road, no network layer at all. Everything downstream
— the flip, the reading, the gain, the memory, the simulation, the stage — never learns the
difference. It is also, incidentally, how anybody tries a sky that is not in the folder.

**2 · `dikhololo_night_2k.hdr` was hardcoded in the NIGHT preset**, and that file had been
renamed to `night.hdr` in the folder hours earlier. So NIGHT went on asking for a name nothing
answers to, and the error blamed the folder for a string in the source. **No preset names a file
any more.** The folder is the only thing that knows what is in it; `night.hdr` is attached to
NIGHT by name the moment the folder is read; and a page that cannot be told what is in the folder
keeps its gradient and asks for nothing — which is the honest answer rather than a 404 dressed up
as a diagnosis.

### Verification

The by-hand path, driven with the bytes in hand and no fetch by the tool — exactly what the
button does on a local page:

| | |
|---|---|
| result | `state: ready`, `2048 × 1024`, `gain ×0.32`, `lum 0.0841` |
| against the fetched path | identical — same decode, same reading, same weighing |
| side effects | RENDER came on, the map went on stage, the reading was remembered |
| errors | none on `window.onerror` |

The in-app browser cannot open `file://` URLs, so the origin itself could not be exercised here;
what was exercised is every line the button runs, which is the part that was missing.

### Files and components

- `scene-study-3d.html` — `adoptSky` (the shared tail, now used by both doors), `loadSkyFile`,
  the `f-hdr` input, the `+ LOAD .HDR / .EXR…` row, the `file://` note, and the removal of the
  last hardcoded filename. Build stamp `27 Aug 18:29`.

### Pending

- Drag-and-drop of a `.hdr` onto the viewport would be the other obvious door and is not built;
  the input is.
- A map loaded by hand is not remembered as a PATH — only its reading is kept, under its
  filename. Reload a local page and the pill is a ring again until it is picked once more.

## 27 August 2026 — The port is not arbitrary: :3900 or the agent is deaf

### What was wrong

"localhost:8731 doesn't load the sketchpad." It loaded perfectly. What it could not do was
reach its agent, and a Sketch Pad that cannot reach AI3N greys out every tool it has and prints
*"The agent is not running, so a sketch has nowhere to go"* — which is indistinguishable, from
the outside, from not loading.

The agent WAS running. `curl http://localhost:3904/health` → 200. The block is CORS, and the
allow-list is in the agent's own source:

```python
allow_origins=["http://localhost:3900", "http://127.0.0.1:3900", "null"]
```

`"null"` is the origin of a `file://` page. So the Sketch Pad has only ever worked in two
places: a local file, and port 3900. Serving the project on 8731 fixed the sky maps (a served
page can read the HDR folder) and broke the Sketch Pad (a page on 8731 cannot reach the agent) —
two halves of the tool, each working only where the other did not.

Nothing was wrong with either half. The port was wrong.

### What changed

- **`serve.py` defaults to 3900** and says why in its own docstring: the port satisfies the
  agent's CORS AND serves the folder, so both halves work at once for the first time. Given any
  other port it prints a warning naming exactly what will break.

### Verification

`python3 serve.py` then `http://localhost:3900/HUB_5.8.html`, one page load:

| panel | state |
|---|---|
| SKETCH PAD | `SKETCH READY · AI3N · LOCAL MODEL QWEN/QWEN3.0-27B` — every tool live, LIVE ON, BUILD 3D |
| REFERENCES | `AI3N · VISION · READS DRAWINGS` — live |
| SCENE STUDY | `5 skies in HDR/ · DAYLIGHT · DUSK · NIGHT · NIGHT2 · TWILIGHT`, build 27 Aug 18:29 |
| the sky | NIGHT picked in the panel → RENDER on by itself → `loading night.hdr — 100% of 6.7 MB` → the map on stage |

### Pending

- The Sketch Pad's OFFLINE state says the agent is not running. It cannot tell "not running"
  from "running and refusing this origin", and the difference is the whole answer. A health
  check that failed with `TypeError: Failed to fetch` on a page whose origin is not 3900 could
  say so, and that is in the Sketch Pad rather than here.
- Both `python3 -m http.server` instances from earlier today are still up on 8731 and 3907.
  Nothing needs them.


## 27 August 2026 — SKY is a tab, and a dot says whether a file is real yet

### What changed

**THE SKY TAB.** The maps were in ROOM and the sun was in SUN, which split one subject down the
middle — a map IS the sun in it, since the bearing, height and colour of that light are read off
the file — so choosing a sky and trimming its sun sat two tabs apart for no reason anybody could
give. SKY now holds all of it and opens first: the map pills, the way in, ENVIRONMENT, SKY BLUR,
and the sun's STRENGTH / ANGLE / HEIGHT / SIZE. ROOM keeps what is genuinely the room's — the
lamp on the stage, and what the surfaces are made of.

**SKY BLUR, on a slider.** Every map carries its own (2k of cloud is worth seeing; a cloudless 8k
up close bands), and the slider overrides it while you stay on that preset, exactly as SUN HEIGHT
does — picking a preset hands it back. 0 reads SHARP. It changes the PICTURE and not the light: a
blurred sky lights the room precisely as a sharp one does, which is worth knowing before reaching
for it.

**A DOT PER MAP, in the palette's own colours.** `--status-progress` (#FF8559) for a map the
folder has and the GPU has not; `--status-active` while it arrives, as a ring that fills so the
progress is IN the dot; `--status-complete` (#6BFFDC) once it is on stage; `--status-failed`
(pink) and a cross for one that could not be read. Not loaded is not a failure, so it does not
wear the failure colour — and the dot is deliberately not recoloured when the pill fills in,
because the selected sky is the one whose state you most want to read.

**THE WAY IN, GIVEN PRESENCE.** `LOAD .HDR / .EXR` was a pill among pills, which is exactly what
it looked like: one more sky. It is the only control in the panel that ADDS something, and on a
local page it is the only way to get a map at all — so it is now its own full-width row, in the
accent, with an icon.

**And every readout refreshes when a sky changes it.** A row is read once, when the panel is
built. That was fine while every number in here was set from in here, and wrong the moment a map
started deciding one: pick a sky and BLUR is its blur, while the printed value was whatever was
true when the panel opened. `paintLookValues` re-reads them all — except a slider being dragged,
because moving the thumb under the hand moving it is worse than a stale number.

### Verification

Served on :3900, sky memory wiped, panel opened without pressing RENDER:

| | |
|---|---|
| tabs | **SKY** / ROOM / SHOW, SKY selected |
| SKY rows | ENVIRONMENT / BLUR / STRENGTH / ANGLE / HEIGHT / SIZE |
| dots, five maps | all `rgb(255,133,89)` — the folder has them, the GPU does not |
| pick TWILIGHT | its dot went to the accent ring at 20% of 86.8 MB, then **`rgb(107,255,220)` green** with the map on stage |
| BLUR | `0.06` (the map's own), `0.45` at 45%, `0` reading SHARP; the readout followed the map from 28% to 6% by itself |
| errors | none |

Build stamp 27 Aug 18:57.

### Files and components

- `scene-study-3d.html` — `LOOK_TABS` (SKY first, ROOM trimmed), `LOOK.blur` / `effSkyBlur` and
  the `blur` row, `paintBg`, `setEnv` and RESET, `skyMark` / `paintSkyPill` (the dot),
  `paintLookValues`, the `.pick` CTA and the dot colours in CSS

### Pending

- SKY carries six sliders and three pill rows, so the panel scrolls on a short viewport. At five
  maps it is comfortable; at twenty the pill rows want their own scroller rather than the panel's.
- The blur trim is global, not per map: it overrides whichever sky is showing and is handed back
  on the next pick. Making it stick per map means writing it somewhere, and nothing writes to the
  folder.


## 27 August 2026 — The light panel, at its own height

### What changed

- **NO SCROLLER.** `.menu` caps itself at 320px because a MENU is a list of rows and a long list
  should scroll. The light panel is not a list — it is a panel with three tabs — and a scrollbar
  through the middle of it hid the sliders under the pills. It takes the height its content needs
  (441px on the SKY tab with five maps), and `openLook` MEASURES it after appending and lifts it
  if its foot would fall off the bottom of the viewport. Only if it cannot fit at all does it get
  a scroller, as a last resort rather than as the normal case. Measured after appending because
  the height depends on the tab, the number of skies in the folder and whether the RENDER warning
  is up — none of which is knowable before the thing exists.
- **The caption under the CTA is gone.** "5 maps in HDR/" was printed always, and once the dots
  said which maps and what state each was in, a line repeating the count was one more thing to
  read for nothing. It stays for the one case where it is the only useful thing on screen — when
  the folder answers with NOTHING, which is where every unexplained version of this went wrong.
  The count is on the button's own tooltip either way.
- **The section labels are readable.** `from HDR/` and `generated` were in `--text-disabled`:
  11px, uppercase, at the lowest contrast in the palette, over a raised surface — a rumour. They
  are the only thing saying that one row of pills is the folder and the next is not, so they are
  in `--text-meta` now, with a hairline over the second one, because a heading should look like it
  belongs to what is under it.
- **The CTA is aligned.** `.menu button` sets `align-items: baseline`, which is right for a row of
  text and wrong for a button with an icon in it: the glyph sat on the text's baseline and the
  label rode high in the box. Centred on both axes, `line-height: 1`, 26px.

### Verification

| | |
|---|---|
| panel | 441px tall, `overflow: visible`, `scrollHeight === clientHeight` — no scrollbar |
| caption | absent |
| section labels | `rgb(133,143,162)` — was `rgb(71,84,103)` |
| CTA | box centre 284px, icon centre 284px — same pixel |
| in the Hub's iframe | 441px inside 849px, still no scroller, same labels |
| errors | none |

Build stamp 27 Aug 19:46.

### Files and components

- `scene-study-3d.html` — `.menu.panel` height rules, the `fit()` measure in `openLook`, the
  conditional `skynote`, `.pillrow` and `.envrow button.pick` CSS

### Pending

- In a genuinely short panel — the Hub's Scene Study at under ~450px — the panel still has to
  scroll, and then it is pinned to the top with its own scroller. The way out is fewer rows per
  tab, not more height.


## 27 August 2026 — Two panels, one room, two views — and EXR is stored the other way up

### 1 · The render is each panel's own

`look` carried `render`, and the host both fans a look out AND replays the last one to any panel
that connects later. So pressing RENDER in the Scene Study put every Camera POV of that take into
RENDER, a POV opened afterwards came up in RENDER, and — since choosing a sky now brings the lit
view with it — one panel picking a sky put every other panel into a lit preview, each with its own
maps to download and its own composer to run.

The flag is no longer published, applied or stored. Everything else about the look still travels:
the environment, the trims, the glow, the drives and the surfaces, because two panels of one show
under a different sun is not a choice anybody made. An arriving look is applied with the RECEIVING
panel's own view state — `setRenderPreview(renderPreview)` rather than the sender's flag, which
still does the heavy half (lights, materials, composer, environment, surfaces) so a trim from next
door takes effect where it should. A panel in the working view stays there, downloads nothing, and
adopts the room the moment it enters RENDER itself.

`SCENE-STUDY-BRIDGE.md` gains the `look` row it never had, and the rule under it.

| step | Scene Study | Camera POV |
|---|---|---|
| both connected | working view | working view |
| RENDER pressed in the Scene Study | **render** | working view |
| a sky picked in the Scene Study | render | working view |
| RENDER pressed in the POV | render | **render** |
| POV reconnected while the Scene Study is in render | render | **working view** |

Driven through a host stub that reproduces the Hub's fan-out and its replay-on-connect. The look
itself still crosses — the stub logged `look from a · fields: mode, env, trims, glow, emit, gain,
surf`, with no `render` in it.

### 2 · An EXR is stored the other way up from a Radiance map

Reported: the daylight map is inverted, the landscape overhead and the sky at the horizon.
Measured, and it was: `day.exr` read upper hemisphere **0.097** against lower **0.642** — the sky
under the floor.

A Radiance `.hdr` stores its scanlines from the TOP and three samples an equirect with v = 0 at
the NADIR, so it has to be turned over. An OpenEXR arrives the other way round and must not be.
`flipSkyRows` was applied to both, which was right for the two `.hdr` files this was built against
and wrong for every `.exr` since.

So the FORMAT decides — and then the MEASUREMENT checks it, because a rule about file formats is a
rule about libraries and libraries change. A sky carries more light than the ground under it: true
of every outdoor map ever shot, including a moonlit night (0.176 against 0.016). If the two come
out the wrong way round by half again, the format's answer was wrong and the map is turned over,
with a line in the dev log saying so. The threshold is loose on purpose — a studio map with a lit
floor is allowed to be brighter below without being flipped.

**And the two doors became one.** `hdrFor` had its own copy of the mapping, the flip, the reading,
the weighing, the memory and the toast, and `adoptSky` had another — which is exactly how the flip
rule got fixed in one of them and not the other. There is one tail now; the only thing the URL
door knows that the file door does not is whether the bytes came out of an `.exr`.

**The remembered readings are versioned.** `ss.sky.v1.` → `v2.`: every reading taken before this
is upside down, sky and ground the wrong way round and the key aimed at the land. A version in the
key is cheaper than a migration and cannot be got wrong.

| | before | after |
|---|---|---|
| `day.exr` upper / lower | 0.097 / 0.642 | **0.642 / 0.097** |
| the sun in it | 8° (found in the land) | **13°** |
| `night.hdr` | 0.176 / 0.016 | unchanged |

Build stamp 27 Aug 19:59.

### Files and components

- `scene-study-3d.html` — `lookState` / `applyLook`, `adoptSky` (the flip rule and the shared
  tail), `hdrFor`, `loadSkyFile`, `SKY_MEM`
- `SCENE-STUDY-BRIDGE.md` — the `look` row and *The look travels, the render does not*

### Pending

- The measured check can only catch an upside-down map, not a mirrored one: nothing here would
  notice a map flipped in u. A sun measured on the wrong side of the room would, and nobody has
  built that check.
- `LOOK_BY_TAKE` in the host still stores whatever the tool sends. It no longer contains a
  `render` field, but the host does not know that and would replay one if an older tool sent it.


## 27 August 2026 — PICK FACE: a face of an imported model, given a role

### What changed

An imported `.glb` could be put in the room and could cast a shadow, and that was all. Everything
that makes a surface MEAN something here — a clip routed to it, a crop placed on it, a canvas
linked across it, spill thrown off it, cabinets counted in it — belongs to a SOLID with a role,
and a solid could only be drawn on the pad. So a stage that arrived as a model had to be traced
by hand to become the stage it already was.

**PICK FACE** (toolbar, or `F`). Hover a flat face of an imported model and it lights up with its
own fitted outline and a readout — `2 triangles · 18.00 × 12.00 m · lying flat`. Click and it
asks what the face becomes: **LED WALL**, **WALL**, or **DECK**.

- **What a "face" is.** A raycast returns ONE TRIANGLE; what a person means is the connected run
  of triangles in the same plane. So the hit triangle is flood-filled across its neighbours while
  the normal holds within 4° and the plane offset within 2 cm. Adjacency is built by POSITION and
  not by index — exported geometry splits vertices for normals and UVs constantly, and an index
  join stops at every seam — and it is cached on the geometry, because a mesh is walked once and
  picked many times. Measured: an 11-triangle patch out of a 6,904-triangle mesh, 24 ms on the
  first pick of that mesh and 0.1 ms after.
- **What it becomes.** The patch is fitted with an oriented box in its own plane, which is all
  three roles need: a vertical patch becomes a run standing on the floor with that width, height
  and bearing; a horizontal one becomes a closed deck of that outline at that height.
- **Who builds it.** Not the tool. `addSolid` asks the host, which puts it through the same
  `agentApplyOp` the pad's BUILD uses, so the sanitising, the id and the `srcId` replacement rule
  are one implementation. The solid comes back in the next `scene`, which is why it persists,
  appears on the paper, and is treated as what it now is.

### Three things the build only learned by being tried

- **A window-level `pointerdown` closes every menu.** The role menu opened during the press was
  dead before it was drawn. It opens on RELEASE now — and only if the pointer stayed within 3px,
  so a drag over a face is somebody looking around rather than somebody choosing.
- **From inside a room every face is back-facing**, and three's raycaster honours `material.side`:
  a grid sweep over a concert venue returned zero hits from geometry plainly on screen. The mode
  makes what it can pick double-sided while it is on and puts every material back afterwards.
- **Escape had an order and PICK FACE was at the front of it**, so an escape during a placement
  quietly left the placement armed. A modal thing — a pending height, a crop, a placement — goes
  first; a mode you are working in gives way.

### Verification

Standalone on :3900, viewport 1184 × 706, driven through the real pointer handlers:

| | |
|---|---|
| hover | highlight drawn (fill + fitted outline), readout `2 triangles · 18.00 × 12.00 m · lying flat` |
| release | the role menu at the pointer: LED WALL / WALL / DECK, each with what it means |
| DECK chosen | `{role:'stage', plane:'floor', closed:true, verts:[[-90,60],[90,60],[90,-60],[-90,-60]], at:[0,0,0], h:14, thick:2}` — 18 × 12 m, top at 1.40 m, in take units |
| a standing face | `{role:'led', closed:false, verts:[[-75,0],[75,0]], at:[0,0,-58], base:14, h:80, tile:{w:5,h:5}}` — 15 m wide, 8 m tall, base 1.4 m |
| an imported 6,904-triangle mesh | 11-triangle coplanar patch, 0.68 × 0.40 m |
| errors | none on `window.onerror` through any of it |

Standalone says so rather than pretending: *"DECK from the model · 4 verts · 18.00 × 12.00 m deck
at 1.40 m — standalone: the host is what builds it, so nothing will appear here."*

### Files and components

- `scene-study-3d.html` — new section *6b*: `faceAdj`, `facePatchFrom`, `paintFaceHighlight`,
  `faceUnder`, `faceHover`, `faceSolidOp`, `faceAssign`, `faceMenu`, `setFaceMode`, `faceSidesOn`;
  plus the `b-face` button, the press/release wiring, the `F` key and the escape order
- `HUB_5.8.html` — `case 'addSolid'`, through `agentApplyOp`
- `SCENE-STUDY-BRIDGE.md` — the `addSolid` row

### Pending

- **The fit is a rectangle.** An L-shaped or trapezoid face becomes the box that contains it. The
  hull is the next step and it is a bigger one: every role's builder would have to accept a
  non-convex outline, which the pad's own shapes already do, so the road exists.
- **One face at a time.** A curved LED wall in a model is a run of patches, and shift-click to add
  the next one into the same solid is not built — the u-ordering that `buildLedSolid` does for a
  faceted arc is the piece to reuse.
- **The tolerance is fixed** at 4° and 2 cm. A slightly bowed architectural wall reads as several
  faces; a modifier to widen it while picking would fix that and is not there.
- Picking is offered on the venue's own meshes as well as imported ones, which is useful — a
  parametric room's wall can become an LED — and does mean a venue face can be picked twice under
  two roles. The `srcId` is derived from the patch's centre, so the same face picked again
  REPLACES rather than duplicates; two different roles on one face is still possible.


## 27 August 2026 — The paper sees the room, ALT takes one face, and the POV has a sky

### 1 · Imported models are on the paper now

An imported `.glb` is tool-side, like the clips and the links: it never becomes a take fact, so
the Sketch Pad had no idea it existed. That makes the paper WRONG rather than incomplete —
somebody draws a deck straight through the truss tower standing in the room, because on the page
there is nothing there.

Every imported object's FOOTPRINT is published: where it stands, how big it is on the plan, how
tall, which way it faces. Not its geometry — the pad is a plan, and a plan of a model is its
shadow on the floor. The pad draws each as a dashed, crossed rectangle in meta ink with its name
over it, **plan only** (a footprint means nothing on an elevation page) and never selectable: it
is a shadow of something that lives in the room, and the only thing to do with it here is not
draw through it.

Fanned out exactly the way `ledLinks` is — forwarded to the sketch panels, not stored on the take
— because it is the same KIND of fact: something only the room can work out, that the paper needs
in order not to lie. Sent from `syncDimensions`, which is where every path that adds, drops, moves
or deletes anything already ends up: one hook rather than six, debounced 250 ms so a drag does not
flood the wire.

### 2 · ALT takes just one face

The coplanar fill is right for a wall exported as a hundred triangles and wrong for a model whose
whole shell is one continuous plane — there it swallows far more than anybody pointed at. ALT
holds it to one face, and one face is a QUAD: a quad is exported as two triangles split along its
DIAGONAL, which is the longest edge of both halves, so ALT takes the seed triangle and the one
coplanar triangle across that edge. Exactly two for a quad, exactly one for a lone triangle, and
never a fan — the first attempt at this took "the seed and everything touching it" and still came
back with eight.

| mesh | coplanar fill | ALT |
|---|---|---|
| Object_4, 4320 triangles | 20 | **2** |
| Object_8, 1240 triangles | 8 | **2** |
| Object_6, 3168 triangles | 4 | **2** |

The readout says which you are getting — `· hold ALT for just one face` / `· ALT: this face only`.

### 3 · The Camera POV has a sky

A POV in RENDER was a black frame. It has had its own RENDER button since the render stopped
travelling between panels, and it knows every map in the folder — but the one control that CHOOSES
a sky lives on the toolbar this mode hides, so it could only be lit if a Scene Study happened to
publish a look. Measured: `render: true`, `env: 'black'`, `scene.environment: null`.

So the POV chrome gains a **SKY** pill that opens the same LIGHT & LOOK panel. Its own render, its
own sky, and the same panel — nothing forked.

### Verification

- POV: `?mode=pov` → SKY · WORKING VIEW in its bar → panel opens → NIGHT picked → `night.hdr`
  ready at 2048 × 1024, `environmentIntensity` 0.174, background is the texture, and the frame
  carries the map's horizon glow behind the truss.
- Pad: three footprints posted → drawn as dashed crossed rectangles with names, including a
  rotated one, at the right places on a 1 m grid.
- Tool: `→ objects {"objects":[{"id":"obj-1","name":"concert_stage.glb","at":[0,0,0],"w":6.8,…`
  in the standalone dev log after an import and a drop.
- No console errors in any of it. All three files syntax-checked.

### Files and components

- `scene-study-3d.html` — `postObjects` and its hook in `syncDimensions`; `faceTight` and the quad
  rule in `facePatchFrom`; `b-povsky` in `setupPovChrome` and the menu-closer exception
- `HUB_5.8.html` — `case 'objects'`, fanned to sketch panels
- `sketchpad.html` — the `objects(m)` door, `roomObjects`, `drawRoomObjects`

### Pending

- **The import's own scale is worth a look, separately.** `concert_stage.glb` arrives 0.68 m
  across: `fitImport` reads the file's units and lands on 0.01, not on its 12 m target. The
  footprint on the paper is faithful to what is in the room, so this is not the pad's problem —
  but somebody will import that stage and wonder where it went.
- A rotated footprint's LABEL is placed in unrotated space, so it sits a little off the box.
- The footprint is the object's bounding box. A curved set piece is drawn as the rectangle that
  contains it, which is the same trade the face pick makes.


## 27 August 2026 — Close of session

Twenty-six entries today, and they fall into three runs.

**The crop and the canvas.** A crop armed after a JOIN was cropping one wall of a canvas, because
five readers asked a clip's ROUTE what surface it was on and the route still said one screen. The
canvas is the route now, normalised in one place. Then unlinking stopped replicating one picture
across the screens and started SPLITTING it — a clip per screen, on its own track, with its own
crop, re-fitted to that wall — which needed tracks asked for from the take, a parking rule for
what a join cannot show, and a timeline dense enough to hold the result.

**The sky.** The longest run, and most of it was not the feature. RENDER can be lit by a real
radiance map; the HDR folder is the list of skies; a map is READ on load and its own reading drives
the ambient pair, the key's bearing and colour, and the gain that keeps a preset's numbers
meaning what they said. Along the way: a map arrives upside down and the two formats disagree about
which way; a 4000 m ground plate was standing between the camera and the sky; the light-matching
gain was also dimming the picture; the environment only exists in RENDER and picking a sky did not
turn it on; `pumpSkies` was undefined in a partial write; the folder can be at two different URLs;
a preset was hardwired to a filename that had been renamed; and a `file://` page cannot fetch
anything at all, which is why there is now a way to hand a map over by file. Each of those was
reported as "the map does not show", and each was something else.

**The room.** PICK FACE: a flat face of an imported `.glb` becomes a solid with a role, asked for
from the host through the same door the pad's BUILD uses. Imported models now put their footprint
on the paper, so a plan cannot be drawn through a truss tower that is standing in the room. And
the Camera POV became a panel in its own right — its own render, its own sky.

### Where things stand

- **Serve it on 3900.** `python3 serve.py` in this folder. The port is not a preference: the AI3N
  agent on :3904 allows `localhost:3900`, `127.0.0.1:3900` and `null` (a `file://` page) and
  nothing else, so on any other port the Sketch Pad and the Reference Board come up with their
  agent offline. The server also sends `no-store`, because a cached iframe cost a whole round of
  "nothing has changed".
- **The build stamp is in the light panel**, bottom left. `27 Aug 23:06` is what this session ended on. If
  the panel says anything older, the page is cached.
- `HDR/` holds five maps and `index.json`; `favicon.ico` is Igor's own icon set; `serve.py` is new.
- Every change today is in `scene-study-3d.html`, with three small additions to `HUB_5.8.html`
  (`addSolid`, `objects`) and one to `sketchpad.html` (`objects` + `drawRoomObjects`), and two
  contract additions to `SCENE-STUDY-BRIDGE.md`.

### The three things worth doing next

1. **Re-run the suites.** The note of 26 August still stands and is now further out of date:
   `test-crop.mjs` asserts a single wall's canvas, and the linked path, the split, the parking and
   the reset have all changed under it.
2. **The import's scale.** `concert_stage.glb` arrives 0.68 m across — `fitImport` reads the file's
   units and lands on ×0.01 rather than its 12 m target. Everything downstream is faithful to what
   is in the room, which is why it looks like a missing model rather than a wrong number.
3. **DAYLIGHT-family levels and the fixed exposure.** DAYLIGHT was re-levelled today because it is
   the template every unrecognised map inherits; STUDIO and ARENA were not. The exposure is still a
   constant 1.25 for every sky, and an auto-exposure would change what LED DRIVE means between
   presets — which is the one comparison this tool exists to make.
