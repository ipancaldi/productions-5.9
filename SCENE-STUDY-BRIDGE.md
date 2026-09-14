# Scene Study bridge — protocol v1

The contract between **`production-hub-v5.html`** (the host) and
**`scene-study-3d.html`** (the tool). Both halves are implemented against this
document; if the two ever disagree, this file is the thing to fix first and the
version number is the thing to raise.

| | |
|---|---|
| **Host** | the workspace — section *4b · THE SCENE STUDY BRIDGE*, plus the `ed-stage`, `ed-preview`, `ed-timeline` and `ed-videopreview` components |
| **Tools** | `scene-study-3d.html` (`?mode=scene` · `?mode=pov`), **v5.9** `sequencing-timeline.html` (`?mode=timeline`), `video-preview.html` (`?mode=preview`), `content-bin.html` (`?mode=bin`) |
| **Transport** | `<iframe>` + `window.postMessage`, `targetOrigin: '*'` |
| **Version** | every message carries `v: 1`; a message with any other `v` is ignored, silently, on both sides |

> **v5.9 · THIS IS NO LONGER A BRIDGE TO ONE TOOL.** Four panels speak it, they are
> three files, and every one of them registers in the same `TOOL_SENDERS` set — which
> is why the additions below are four message types and no new plumbing: `scene`,
> `mediaAsset` and `transport` already fanned out to "every panel of this take" and
> never cared how many that was.
>
> **Sequencing left the viewport.** Until v5.8 the timeline was a strip pinned under
> the 3D. It was in the wrong place for three unrelated reasons: it competed for height
> with the thing it was describing, `?mode=pov` switched it off entirely — so the one
> view showing what the audience sees could not move the cue producing it — and it tied
> arithmetic about time to a WebGL context. It is `timeline.html` now.
>
> **What did not move is the picture.** The Scene Study still decodes the file, makes
> the `VideoTexture`, and puts it on the LED wall's material or the projector's landing
> quad. A texture belongs to the context that samples it. So the split is:
>
> | | owns |
> |---|---|
> | `sequencing-timeline.html` | the CUE — sequences, the tracks in them, the clips on those, and the one output and one crop each sequence carries. And the clock |
> | `video-preview.html` | nothing. It is a MONITOR: one picture, a transport, safe areas |
> | `content-bin.html` | the INVENTORY — every file this production has, with a frame of it |
> | `scene-study-3d.html` | the SURFACE — decode, texture, which mesh it lands on, crop-on-the-wall |
>
> **THE UNIT IS THE SEQUENCE, NOT THE TRACK.** A wall shows one picture. Six tracks
> cutting against each other are how that picture gets made — and it is the picture
> that is thrown at the wall, cropped into its frame, and named in a running order.
> So `route` and `crop` are decided on the SEQUENCE, which has a name and can be
> renamed, duplicated and deleted. Routing six tracks individually at one wall was
> six chances to disagree about one fact.
>
> **The room is never told about sequences.** Adding the concept there would be a
> second model of the same thing. Each clip row travels with its sequence's route
> and crop already RESOLVED, plus a `prio` for the video stack — the decision lives
> in the timeline, the consequence travels.
>
> **The strip is gone from the Scene Study, not folded.** An earlier pass kept it and
> hid it while a Timeline was open; that left two places to sequence one show, which is
> the thing the split was for. What the viewport keeps is the surface half plus one
> gesture that is genuinely about the room: **drop an `.mp4` onto a wall or a projector
> in the scene** — it finds a track, routes the clip to what you dropped it on, and
> publishes `clips` so the Timeline shows where it landed.
>
> The cost, stated: opened standalone the Scene Study can still be given a clip and will
> still show it, but nothing in it starts the playhead except `SPACE` and the POV bar's
> PLAY. The transport is the Timeline panel's. A `?mode=pov` panel no longer hides a
> timeline — there is none to hide, and a POV can now sit beside the real one, which was
> the original complaint.

> **v5.8 · WHAT THE PAPER IS TOLD IS NOT A VIEWPORT PREFERENCE.** `objects` and
> `objectFaces` are published from `syncDimensions`, which is the one hook every path
> already ends up in — but they sat *below* its early return for DIMENSIONS, a toggle about
> whether measurement marks are drawn in this viewport. With it off, which is the default, a
> model imported or generated into the scene was never announced to the Sketch Pad at all:
> the paper drew straight through a set it could not see, and the faces it could have taken
> were nameable only by sweeping the pointer over the mesh in here. Both publishers are now
> hoisted above that return; `dimensionBox` is the only thing the toggle is about. Alongside
> it, **`resync`** lets the host ask for all three on demand, so a panel that opens late gets
> the room rather than waiting for somebody to nudge it. Additive: **`BRIDGE_V` stays 1**.
>
> **v5.8 · FACES ARE HELD, NAMED TOGETHER, AND CAN BE DROPPED.** A screen in a modelled set is
> normally three or five coplanar faces, so shift-click accumulates a HELD SET in both surfaces
> and one act names all of it — with `link` on **`promoteFace`** asking for them as one canvas in
> the same message. **`deleteFace`** takes faces off the mesh for the case that follows almost
> every pick: the modelled screen is now standing exactly where a real LED wall is, taking the
> same light and drawing the same surface twice. The pad also draws imports and their faces in
> ELEVATION now — a footprint is a fact about the floor, but how tall a set piece is was the one
> thing the front page could not see. Still additive: **`BRIDGE_V` stays 1**.
>
> **v5.8 · A MODEL'S FACES ARE A SET, NOT A SEARCH.** Picking a face of an imported `.glb`
> existed but could only be found by sweeping the pointer over the model, and the Sketch Pad
> was told an import's bounding box and nothing else — so a set arriving as one file was a
> dashed rectangle with a cross through it on the paper. The tool now segments every import
> into its coplanar patches once, keeps the significant ones, DRAWS that set in the viewport
> and publishes it with **`objectFaces`**. The pad draws the same set and can take one with
> **`promoteFace`**, or point at one with **`hoverFace`**; the fit is answered in the room,
> because that is the only surface holding geometry, and leaves by the same `addSolid` door
> a click in the viewport uses. All additive, so **`BRIDGE_V` stays 1**.
>
> **v5.8 · THE ROOM IS GRABBABLE.** The gizmo used to ask `selectedDevice()` directly,
> so a deck or an LED wall traced on the pad could be selected, outlined and deleted in
> the viewport but never moved or turned in it. It now holds either kind, and a shape
> reports its new place with **`moveSolid`** — additive, so **`BRIDGE_V` stays 1**. A
> solid gets three arrows and ONE ring: its `rot` is a single angle about the vertical,
> so offering three would be offering two that snap back.
>
> **v5.5 · SOLIDS.** `scene` gains `solids[]` — fitted outlines with a role, built
> in the tool's section *4d* as extruded decks, swept curved walls a projector can
> throw at, and LED walls faceted into flat cabinets. `ghostClear` gains an optional
> `planId`. `measure.derived` gains `builtGeometry`. All additive, so **`BRIDGE_V`
> stays 1**. The contract is `SOLIDS.md`.

---

## Why a bridge at all

v3 drew the Scene Study itself, in SVG, inside the prototype. That put the
spatial tool inside a 5,500-line file that also holds the checklist, the wiring
model, the cost engine and the layout engine — so improving the 3D meant
editing the prototype, and a mistake in the 3D was a mistake in the workspace.

v4 makes the viewport a separate file loaded into the panel. Three consequences,
in the order they matter:

1. **The tool can be iterated on its own.** Open `scene-study-3d.html` directly
   and it boots against `MOCK_TAKE` with every feature live. That is the
   standing test that it is genuinely external.
2. **The boundary is a written contract**, not a habit. Anything the tool can do
   to the take is in the table below and nowhere else.
3. **A WebGL failure is contained.** The tool crashing leaves the workspace up,
   and the panel says so.

## The rule both sides agree on

> **The take owns the facts. The tool owns the view.**
>
> Devices, positions, models, decisions and status live in the take.
> Geometry, venue, media, camera and gizmos live in the tool.

There is exactly one crossing, and it is the reason the split pays for itself:
the tool is the only part of the system holding real geometry, so it **derives**
measurements the model cannot and reports them. The host stores them under
`take.derived` and offers no editor for them anywhere — a derived figure is
never typeable.

## Units

The take counts spatial positions in **decimetres** (1 unit = 10 cm). That is
what its numbers always meant — a projector ring at radius 128 is 12.8 m, flown
at 96 is 9.6 m, in a venue 38.8 m wide. v3 divided by 100 and printed metres,
which is why every geometry-dependent figure in the Measurements panel had to be
hardcoded.

The tool works in **metres** and converts at the boundary using the
`unitsPerMetre` the host declares in `hello`. Positions on the wire are always
take units.

---

## Handshake

```
tool                          host
  │  ready ────────────────────►│
  │◄──────────────────── hello  │
  │◄──────────────────── scene  │
  │                             │
  │  … events …  ◄──────────────►  … scene on every take change …
```

The host pushes a full `scene` whenever anything in the take that the tool can
see changes. There is no diffing: a take is dozens of objects, and a whole
snapshot is cheaper than keeping a diff honest.

If `ready` never arrives within 6 s, the panel shows the *lost* state and names
the file. If `hello` never arrives within 4 s, the tool says the host never sent
a scene and points you at running it standalone.

---

## Host → tool

| type | payload | meaning |
|---|---|---|
| `hello` | `mode` `'scene'｜'pov'`, `unitsPerMetre`, `tokens`, `catalogues`, `reqs`, `bgs` | identity and vocabulary, once per connection |
| `scene` | `takeId`, `sel`, `selSolid`, `venue`, `view`, `devices[]`, `tracks[]`, `blocks[]`, `audience[]`, `solids[]` | the whole projection of the take. **v5.5** adds `solids[]` and `selSolid` — see `SOLIDS.md` |
| `selectSolid` | `solidId｜null` | **v5.5** — the Sketch Pad selected a shape, so highlight that one. `sel` is for kit and `selSolid` is for the room: two selections that share a pointer and nothing else |
| `select` | `objId` | another panel changed `take.focus.obj` |
| `arm` | `req`, `model` | a library panel wants placement armed in the viewport |
| `view` | `preset` | drive the view cube from outside |
| `venueAsset` | `name`, `bytes` (ArrayBuffer, or null to clear) | an imported `.glb` made in **another panel** of this take |
| `ledLinks` | `links[]` of `{ id, srcIds[] }` | **v5.9.2** — WHICH SCREENS ARE ONE CANVAS, replayed on every scene handshake and fanned when another room links or unlinks. Scene panels only. Sent **empty if empty**, and **before** the media: a `clips` row routed at `ledlink-2` cannot resolve until `ledlink-2` exists, and the empty send is also what tells a booting room it may start publishing its own (see `linksSettled`). A linked canvas is the one LED fact that lives ONLY in the tool — the id comes from a local counter, the members are route ids that instance minted — so a room re-created by a task button came back with no canvases at all, three linked walls became three walls, and every clip aimed at the canvas went dark. The host had been storing this since v5.8 and only ever forwarded it to the Sketch Pad. Members travel by SOURCE id because that is the only name a wall has that survives this panel being thrown away; a group whose walls have not arrived is dropped rather than half-built |
| `transport` (replay) | the last transport, with `playing: false` and `replay: true` | **v5.9.2** — WHERE THE PLAYHEAD WAS. A re-created room came up at 00:00 while the show was parked at 00:12, so the wall showed whatever happens to sit under the top of the timeline rather than the frame somebody was looking at. The position is restored; the RUNNING is not, because the clock lives in the Sequencing Timeline and replaying `playing: true` into a room with no clock sets it running free on its own frame loop. A Timeline that is open and playing beats every 1.5 s and picks the room back up |
| `importAssets` | `items[]` of `{ id, name, bytes, pose{ at[], w, d, h, rot }｜null }` | **v5.9.2** — every FILE IMPORT standing in this take's room, replayed on a handshake. Scene panels only, and sent **after** `venueAsset`: an import stands on the floor of the room, and restoring one into a room that has not arrived yet puts it on the default ground plane. The tool rebuilds any `id` it does not already hold, scales to the longest side in `pose`, then **measures its own box and shifts the holder** until centre and base match — exact whatever the file's own origin is, which is the one thing about a `.glb` nobody can predict |
| `importAsset` | `id`, `name`, `bytes` | **v5.9.2** — one import made in **another** scene panel of this take, fanned live. Two Scene Studies open on one take showing different furniture is two rooms, not one |
| `importDrop` | `id` | **v5.9.2** — that import was deleted somewhere else. Removed without a toast: the person watching this panel did not ask for anything |
| `mediaAsset` | `trackId`, `name`, `kind`, `bytes` (ArrayBuffer) | a file loaded in **another panel** of this take. **v5.9** `kind` is `'video'｜'audio'｜'image'` and it MUST survive the relay — the Scene Study skips audio and stills, the preview draws a still with no clock to park it on, and the bin sorts by it. Dropping the field made every still arrive everywhere as a video with no duration, which presents as a lane stuck on "measuring…" forever |
| `binRequest` | `assetId`, `trackId` | **v5.9** — relayed to the Content Bin: something was dragged out of it onto a lane. Only the id travels with a drag (a drag between two iframes moves strings, not megabytes), so the bin answers with an ordinary `mediaAsset` and the file reaches the take by the one path every file takes |
| `selectSequence` | `seqId` | **v5.9** — relayed to the Sequencing Timeline: the Video Preview was pointed at a different cue and the panel that edits cues should open the same one. A request, not an assertion — the answer is the next `clips` |
| `transport` | forwarded verbatim | the playhead, timeline length and loop region, from another panel |
| `clips` | `sequences[]`, `cur`, `clips[]` of `{ trackId, seqId, kind, name, dur, start, in, out, route, crop, prio }` | **v5.9** — THE CUE, WHOLE. `sequences[]` is `{ id, name, route, crop, tracks[] }` and `cur` is the one being edited (the Video Preview follows it rather than choosing its own). `kind` is `video｜audio`; audio never carries a route or a crop, because an LED wall has no speakers. `prio` is the video stack — higher draws over lower, so a surface with two live clips resolves the way the timeline says rather than the way a Map iterates. `route`/`crop` are the SEQUENCE'S, resolved onto every row of it. The rest: WHERE THE CUTS SIT, as the Timeline (or the Video Editing panel) states it. Adopted onto clips that **already exist** and never used to create one: the file arrives separately as `mediaAsset`, and a row naming a track whose bytes nobody has is a position with nothing to position. The host sends the assets first on a handshake for exactly this reason, and every receiver is written not to depend on it having done so. `in`/`out` are the part of the FILE that plays and `start` is where that part sits on the show's clock — an untrimmed clip has `in: 0, out: dur` and behaves as it always did |
| `routeTargets` | `targets[]` of `{ id, label, short?, req, note? }` | **v5.9** — WHAT A CLIP CAN BE SENT TO: library kit, an LED wall traced on the Sketch Pad, several walls linked into one canvas. Authored by the Scene Study because every one of them is derived from geometry no other panel holds, and replayed by the host exactly the way `objectFaces` is. `req` is `led` · `projectors` · `link` |
| `armCrop` | `trackId`, `seqId` | **v5.9** — the timeline's sequence-level CROP button, relayed. The crop belongs to the SEQUENCE; `trackId` is only which of its clips is on the surface for the handles to grab. The button is over there because that is where the clip is; the handles are drawn here because they are drawn on the wall, and the wall is geometry only this panel holds. Scene panels only |
| `look` | `look{ mode, env, trims, glow, emit, gain, surf }` | how another panel of this take is LIT. Applied to whichever view this panel is already in — see *The look travels, the render does not* |
| `promoteFace` | `faceIds[]` (or `faceId`), `role`, `link?`, `lay?` | **v5.8** — the Sketch Pad named faces it was sent in `objectFaces` and wants them built. Relayed rather than answered by the host: the fit is a fact about geometry and this is the only panel holding any, so the tool looks each face up in its own candidate set and asks for the solids with `addSolid` like any other pick. A SET travels together because a screen modelled as five flats is five faces and one surface; `link: true` then asks for them as ONE CANVAS, which only this side can do — the solids do not exist yet, and `requestLink` already knows how to wait across pushes for them. Ids the tool no longer has are counted and said, and the rest are still taken. **v5.8** `lay: 'flat'` asks for a HORIZONTAL LED — the face's outline as the emitting surface, lying where the face lies — instead of the upright reading that stands cabinets up out of it. Only meaningful on a flat face and only for `led`; see `SOLIDS.md § led`|
| `hoverFace` | `faceId｜null` | **v5.8** — the pointer is over that face on the paper, so light it in the room. Highlight only: it selects nothing and builds nothing. `null` clears it |
| `resync` | — | **v5.8** — say again what is in the room: `objects`, `objectFaces` and `ledLinks`, now. Sent when a Sketch Pad connects or changes take, because those three are published on change and a panel that opened afterwards heard nothing until somebody nudged the scene. No new computation and no new path — it calls the same three publishers every change already calls |
| `deleteFace` | `faceIds[]` (or `faceId`) | **v5.8** — those faces are dropped from the imported mesh. The mesh is tool-side and never reaches the take, so only this panel has anything to delete. The triangles are COLLAPSED onto one vertex rather than cut out of the index, which leaves the buffer the same length — so a multi-material mesh keeps its groups and the triangle numbering the pick cache depends on never moves. **The solid already made from a face is deliberately left alone**: it is a take fact, and deleting the modelled screen after taking it as a real LED wall is the sequence this exists for. Restorable per MODEL from the tool's own face menu |

`tokens` is the host's **resolved** BrandOS AA palette (`--gray-800: "#1D2939"`,
…), written straight onto the tool's `:root`. The tool ships the same values as a
standalone fallback and transcribes nothing — there is one palette, transmitted,
not two kept in step.

`catalogues` is `PROJECTOR_LIB` / `CAMERA_LIB` and the LED and tracking model
names — the same rows the library panels list and the cost panel prices. Device
geometry is built from each row's `mm`, so a body in the scene is the size of the
body in the catalogue.

### `scene.devices[]`

```js
{
  id: 'projectors-3',      // the take's object id — the only identity that matters
  req: 'projectors',       // projectors | capture | led | tracking
  idx: 2, label: 'PROJ 3',
  model: 'BARCO G62-W14',  // the `create` decision, or null
  pos: [x, y, z],          // TAKE UNITS
  rot: { x, y, z } | null, // only once somebody has aimed it by hand
  values: { res: '3840×2160', lens: '1.00 : 1' },   // that req's decisions, short keys
  tone: 0|1|2|3,           // none | in progress | complete | failed — the checklist's own ramp
  pct: 0–100,
}
```

`tracks[]` is one per SEQUENCE TRACKS object:
`{ id, label, name, media, startMs, route }` — the clip's filename, where it
starts on the timeline, and which LED wall or projector it is thrown at.

---

## Tool → host

| type | payload | what the host does |
|---|---|---|
| `ready` | `capabilities[]` | replies `hello` + `scene` |
| `select` | `objId｜null` | `focusObj(id)` |
| `move` | `objId`, `x`, `y`, `z`, `rot?` | `moveObject(t, …)` |
| `add` | `req`, `model`, `at[]` | `addDevice(req, model, at)` |
| `remove` | `objId` | `removeObject(id)` |
| `duplicate` | `objId` | `duplicateObject(id)` |
| `addTrack` | — | `addDevice('sequence', null)` |
| `view` | `yaw`, `pitch`, `dist`, `tx/ty/tz`, `bg`, `mesh`, `grid` | writes `take.view` |
| `mediaAsset` | `trackId`, `name`, `bytes` | stored beside the take and fanned out |
| `transport` | `playing`, `t`, `span`, `autoSpan`, `loop`, `loopIn`, `loopOut` | **forwarded whole, unread** |
| `measure` | `derived{}` | replaces `take.derived` |
| `selectSolid` | `solidId｜null`, `srcId｜null` | **v5.5** — a shape was picked in the viewport. `srcId` names the TRACE it came from, which is the only name the Sketch Pad understands |
| `addSolid` | `solid{ role, name, srcId, plane, closed, verts[], bulges[], at[], h, base?, thick?, tile?, lay? }` | **v5.8** — a flat face of an imported `.glb` was picked and should become a solid. `srcId` is the FACE's own id from `objectFaces` whenever the pick is a whole candidate, which is what lets a taken face be ticked rather than re-offered and makes re-picking one REPLACE its solid instead of stacking a second on top; an ALT-tight pick is a deliberately smaller shape and keeps an id of its own. The tool does not make it: solids belong to the take, so this goes through the same `agentApplyOp` the Sketch Pad's BUILD uses — one sanitiser, one id, one `srcId` replacement rule — and comes back in the next `scene`. Which is why a picked face then persists, appears on the paper, and is treated as a stage or a wall or an LED rather than as an import |
| `moveSolid` | `solidId`, `at[]`, `rot?` | **v5.8** — a shape was moved or turned by its gizmo in the viewport. `at` is take units, `rot` is DEGREES about the vertical — the same two fields the Sketch Pad writes, so a shape nudged in 3D and a shape nudged on the pad are one fact arriving by two doors. The host writes them onto `take.solids[i]`; the pad's next BUILD is still authoritative about the SHAPE, this is only about where it stands |
| `ledLinks` | `links[]` of `{ id, srcIds[] }` | **v5.9.2** — several LED screens made one canvas. Stored in `roomOf(takeId).links`, forwarded to the Sketch Pad, fanned to the take's other rooms, and replayed on every scene handshake. The tool stays silent until its own replay has arrived — see `linksSettled` — because `postLinks()` runs from `routeMedia()`, which runs on boot: a booting room would otherwise publish "there are no canvases" straight over the store it is about to be restored from. Same rule as the sequence-loss fix, in a third place |
| `objectFaces` | `faces[]` | **v5.8** — *(and see the note below: these were published from behind the DIMENSIONS toggle, so with it off — the default — a model imported or generated into the scene was never announced at all)* the significant coplanar faces of every imported model in the room, as **the outline each one would become**, in take units and already projected onto the plan: `{ id, objId, name, flat, area, at[], w, hM, taken }` plus `poly[]` + `h` for one lying flat, or `line[]` + `nrm[]` + `base` + `h` for one standing up. Forwarded to the Sketch Pad, never stored — it is derived from geometry the take does not hold, so a copy on the take would be a copy of something the room recomputes anyway. `id` is keyed to the patch's LOCAL centroid, so it survives the model being dragged; `taken` is true once a solid carries that `srcId`. Sent from `syncDimensions` beside `objects`, on the same debounce |
| `removeSolid` | `solidId` | **v5.5** — DEL on a selected shape |
| `clearAll` | — | **v5.5** — empty the scene. Devices go through `removeObject` one at a time, so the checklist, the wiring model and the cost panel unwind exactly as they would by hand; there is no bulk path that could disagree with the single one |
| `venue` | `preset｜glbName`, `glbBytes?`, `label`, `bounds` | writes `take.venue`; bytes are stored and fanned out |
| `importAsset` | `id`, `name`, `bytes` (ArrayBuffer) | **v5.9.2** — a `.glb` was dropped into the room as an OBJECT rather than as the venue. Stored in `IMPORTS_BY_TAKE` and fanned to the take's other scene panels. Sent once, on import, from the file itself: this panel is the one thing in the system that gets thrown away and rebuilt, so it is the last place to hold the only copy of anything. Deliberately **not** a take fact — an import has no checklist, no spec and no cost, and inventing one for it would be the host having an opinion about the room |
| `importDrop` | `id` | **v5.9.2** — that import was deleted here. **Said, never inferred.** Pruning the store from the next `objects` list instead would empty it every time a panel reloaded, because a booting room reports no objects before its replay has arrived — the same class of bug as the sequence-loss one, and the same fix: *a panel must not be taken at its word about what it holds before it holds it* |
| `media` | `trackId`, `name`, `durationMs`, `startMs`, `route`, `label` | sets `track.mediaId`, and `track.range` from the clip's position. **v5.9** `durationMs` is the CUT's length, not the file's — a trimmed clip reporting its whole file would put a number on the take that nothing in the show agrees with |
| `clips` | `sequences[]`, `cur`, `clips[]` (same shape as above) | **v5.9** — stored per take in `SEQ_BY_TAKE`, fanned to every other panel, and replayed on a handshake. Deliberately **not** on the take: `start` moves continuously while a block is dragged and the take is deep-watched, so a drag would re-project and re-send the whole scene sixty times a second. What the take keeps is what it always kept — `track.mediaId` and `track.range`, written from `media` when the gesture **ends**. Sent by the Timeline and the Video Editing panel on every edit, and by the Scene Study whenever a clip is loaded, moved or routed **in the room** |
| `routeTargets` | `targets[]` | **v5.9** — Scene Study only. Stored in `TARGETS_BY_TAKE`, fanned, replayed. Published from `syncDimensions` beside `objects` and `objectFaces`, and again on `resync` |
| `armCrop` | `trackId`, `seqId` | **v5.9** — Sequencing Timeline only. Relayed to the scene panels of this take |
| `binRequest` | `assetId`, `trackId` | **v5.9** — Sequencing Timeline only: a bin item was dropped on a lane. Relayed to the bin, which answers `mediaAsset` |
| `selectSequence` | `seqId` | **v5.9** — Video Preview only: show me this cue, and open it over there too |
| `remove` | `objId` | a track deleted from a sequence, or a whole sequence's worth of them. The take owns what exists, so deleting a lane deletes its object |

**The first six go through mutators that already existed.** That is the point:
the checklist, the task grid, the wiring design and the cost panel react to a
device dragged in 3D for exactly the same reason they reacted to it dragged in
SVG — it is the same event. `moveObject` still writes the position decision, puts
SET POSITION in progress, and invalidates anything calibrated against the old
place. The bridge adds no mutation path of its own.

### The look travels, the render does not

`look` is the one message that is neither a fact about the take nor private to a panel. The
environment, the trims, the glow, the drives and the surfaces are published by whoever changed
them and applied by everyone else, because two panels of one show under a different sun is not a
choice anybody made. The host keeps the last one per take (`LOOK_BY_TAKE`) and replays it to any
panel that connects later, so a panel opened at any time describes the same room as its
neighbours.

**`render` is not in it.** Whether a panel is showing a lit preview is a decision about THAT
panel — the same class of thing as its orbit, or which camera a POV is pinned to — so it is not
published, not applied and not stored. A Scene Study is a diagram somebody is building in; a
Camera POV is a shot somebody is judging; and since choosing a sky brings the lit view with it,
a shared flag meant one panel picking a sky put every other panel into a render, each with its
own maps to download and its own composer to run.

So an arriving `look` is applied with the receiving panel's own view state. A panel in the
working view stays in the working view — where an environment does not exist, so nothing is
downloaded and nothing is composited for a picture nobody asked to see — and adopts the room the
moment it does enter RENDER. `mode` rides along for the log's sake: it is how you tell a POV's
look from a Scene Study's when reading a trace, and nothing branches on it.

### The transport is forwarded, not interpreted

`transport` is the one message the host passes through without looking at it.
The playhead, the timeline's length and the loop region are the tool's own
vocabulary — the take has no opinion about them — but two panels showing the
same take must not disagree about what time it is. So the host is a switchboard
here rather than a participant, and a field added to the transport on one side
does not need adding on the other.

### Imported geometry and clips

An object URL belongs to the document that made it, so a `.glb` dropped on one
panel cannot simply be named to the others — **the bytes travel**. The importing
panel posts the `ArrayBuffer` with its `venue` message; the host keeps it in
`GLB_ASSETS` (a plain `Map`, deliberately **not** on the take, which is deep-watched
and would re-send several megabytes on every keystroke) and pushes `venueAsset`
to every other panel of that take, and to any panel that connects later. The take
itself carries only `venue.glb`, the name.

**Video works the same way**, in `MEDIA_ASSETS`, keyed by take and then by track.
That is what lets a Camera POV panel show the picture on the wall: the clip is
not "in the Scene Study", it is on the take, and every panel gets the bytes.
Where the clip sits in time and what it is thrown at travel with the `scene`
message instead — `tracks[].startMs` and `tracks[].route` — because those are
decisions, and decisions belong to the take.

> **v5.8 · AND THE ROUTE HAS TO BE READ ON THE WAY IN.** The two halves arrive as two
> messages and, on a panel opening cold, in the unhelpful order: the host sends `scene`
> and then the bytes. The tool adopted `tracks[].route` onto clips it already had, which on
> a cold open is none of them — so the clip landed a moment later with no route and fell
> back to guessing from that panel's own selection. In a Camera POV panel the selection is
> a CAMERA, or nothing, so the clip was installed, active and playing with its texture bound
> to no surface at all: video simply did not appear. `installClip` now takes the route from
> the track when the caller does not name one, which makes the take authoritative on both
> paths. An **explicit `null`** route means the take says NOWHERE and is honoured as such;
> `undefined` means it has no opinion and the local guess still stands.

### `measure.derived`

Each key is `{ text, …numbers }`. `text` is what the Measurements panel prints;
the numbers are there for anything that wants to compute on them later.

| key | derived from |
|---|---|
| `throwDistances` | each beam's centre ray to the surface it actually hits |
| `imageSize` | throw distance × the lens's throw ratio |
| `pixelDensity` | the chosen resolution over that image width; grazing beams excluded and counted |
| `overlap` | polygon intersection of landing quads sharing a plane (Sutherland–Hodgman) |
| `ledPitch` | panel width over the chosen pixel map |
| `trackingVolume` | the box the base positions enclose |
| `cameraCoverage` | a 12×12 sample of the stage footprint against each camera's real FOV |
| `venueSurface` | the venue preset's own stage dimensions, or the import's bounds |
| `builtGeometry` | **v5.5** — every solid the drawing built: deck areas by shoelace over the tessellation (so an arc contributes the area an arc has), wall surface area, and LED **cabinet counts**, which is the figure that actually gets ordered |
| `photometry` | **v5.9.2** — `{ groups[], excluded[] }`. Each group is one SURFACE — beams matched by the identical test the `overlap` loop uses, same normal to within ~20° and same plane to within 400 mm — carrying its own 2D frame in metres and each beam's landing quad flattened into it, with `area`, `dist`, `imageW/H`, `incidence` and the chosen `res`. **No lumens, and no lux.** Flux is a catalogue fact and the choice of illuminance-or-luminance, of scale, of screen gain and of what counts as enough are judgements somebody makes while looking at the answer: the room supplies geometry, the *Photometric analysis* panel supplies the lighting. `excluded[]` is the beams left off the map with the reason — `runaway` (a corner ray never found a surface) or grazing, with the angle — because those are two different faults and reporting them as one printed an angle that had nothing to do with why the beam was dropped |

A key the tool cannot derive is simply absent, and the panel prints
*"— waiting on the Scene Study"*. It never prints a plausible default.

---

## Two rules that keep the loop from oscillating

**The tool ignores echoes of its own drag.** A `move` the tool sends comes back
inside the next `scene`. The tool keeps a `dragging` set and, for those ids only,
keeps its own position instead of the host's — released 260 ms after the drag
ends, so the host's version wins again as soon as it can.

**The tool applies the take's viewpoint once per take.** `view` in a `scene`
message is honoured only when `takeId` changes. Otherwise every push would yank
the camera back while somebody is orbiting. This is also what makes a fork open
where its parent was left: it is a different `takeId`, so the inherited viewpoint
applies exactly once.

---

## Modes

`?mode=scene` — the Scene Study. Everything.

`?mode=pov` — the Camera POV panel. The same scene, the same geometry, rendered
through the selected camera's real focal length. Grid, view cube, timeline and
gizmo are off; the toolbar is hidden (not replaced — the buttons stay in the
document so the code that keeps them in step with the selection does not have to
know which mode it is in) and a row of camera pills and an INFO toggle take its
place.

**POV panels are independent of each other.** A POV panel follows the take's
selection *until* somebody picks a camera on its own pill row; from then on it is
pinned to that camera. Choosing a camera there deliberately does **not** post
`select`, because that would drag every other POV panel onto the same camera and
there would be no reason to open two. What POV panels *do* share is everything
that belongs to the take rather than to a camera — the venue, an imported `.glb`,
and the background — which is why `view.bg` and `view.mesh` are applied on every
`scene` push while the orbit is applied once per take.

**v5.9** `?mode=timeline` — `sequencing-timeline.html`. The cue and the clock.
Reads `scene.tracks[]`, `routeTargets`, `mediaAsset` and `clips`; writes
`transport`, `clips`, `media`, `mediaAsset`, `addTrack`, `remove` and `armCrop`.
Holds its own element per clip — for the duration, the filmstrip on a video block
and the waveform on an audio one. Never for a surface.

**Every sequence in the take is on screen at once**, stacked, each one bracketed by
a coloured spine on the pinned name gutter with its own header carrying the cue's
name, output and fold state — a running order is a sequence of cues, and "does ACT
TWO start before ACT ONE finishes" is unanswerable in a panel showing one at a
time. Everything but the cue being edited is dimmed rather than hidden. Lanes are
laid out in **pixels per second**, not as a percentage of the show, so a four-second
cue inside a twenty-minute running order can still be trimmed by hand; the ruler,
the headers and the gutter are all in one scroller with `position: sticky` doing the
pinning, so there is no second scroller to keep in step.

**A still is a clip whose length was decided, not measured.** `kind: 'image'`
arrives with a default hold of five seconds and its tail is free — a movie's tail
stops at the end of the file because there are no frames past it, and a still has
no such limit, so "hold this slate until the band comes on" is a drag rather than a
workaround. Dropping content from the bin onto a sequence with no lane of the right
kind **makes one**: the thing being dragged says what it is, and a cue with nowhere
to put it plainly needs the lane.

**Each clip row also carries its ramps** — `fadeIn`/`fadeOut` in seconds off each
end and `easeIn`/`easeOut` for the shape of each (0.5 is a straight line) — and
`hidden`, which takes a video layer out of the picture without deleting it. A
crossfade is not a third thing: it is a V2 fading out over a V1 that is still
running, which is what it is on a real rig. **The Video Preview composites those
ramps; the Scene Study does not yet** — it puts the top layer's texture on the
surface at full opacity, because blending two video textures on a wall is a change
to the material and not to the wire. Fade in and fade out are therefore true in the
monitor and approximate in the room, and that is the one place the two disagree.

Each sequence may also carry a `cue` — `{ at, label }`, where the cue is CALLED,
which is not the same as where its first frame is. Dragging the cue drags the
sequence with it.

**The host always answers, empty if empty, and answers first.** A panel that has
just opened cannot know whether a replay is coming, and it must not guess: the
timeline builds a default `SEQUENCE 1` when there is nothing to restore, and
building it a moment too early swallows every real cue in the take. It used to
guess on a 700 ms timer — fine on a take with two small clips, hopeless on one with
four masters, because the assets are `ArrayBuffer`s posted ahead of it and
structured-cloning tens of megabytes outlasts the timer. So `clips` is now sent
unconditionally on the handshake, **before** the assets (a second copy follows them,
to land positions on clips that by then exist). "There is no grouping" is an answer;
silence is not.

**And a panel must not publish a grouping before it has one.** `scene` arrives in
the same breath as `hello`, ahead of the replay, and the timeline published its
grouping from that handler — with `S.seqs` still empty, as though *nothing* were the
answer. The host stored it, and the cues were gone: not from that panel, which
restored a moment later, but from the host's copy, which is what the **next** panel
to open is given. That is why opening a second Sequencing Timeline lost the
sequences, and why the first one then lost them on its next reload. Nothing is
published until the replay has landed.

**Two open timelines are not two opinions.** The host never echoes to the origin, so
any `clips` arriving at a panel was authored elsewhere and its grouping is news, not
a competing draft. A live panel therefore **reconciles** — cues updated, new ones
added, deleted ones dropped — rather than ignoring it, which is what left two open
timelines disagreeing about the names of the cues from the first rename onwards.
Skipped only while something is under the hand.

**A reopened panel restores itself from the host.** An iframe that is closed throws
its document away, and sequences are authored here — so the grouping, the names, the
outputs and the cues lived only in this document and died with it: reopening found
no sequences, built a default one, and swept every track in the take into it. Six
cues collapsed into one, silently. The host has held all of it the whole time
(`SEQ_BY_TAKE`, replayed on the handshake) and this panel simply was not listening.
It is now, with one rule: **if this document has no sequences yet, the grouping in
the message IS the state and is taken whole; after that this panel is the author and
takes the shape of a cue from nobody.** Creating the first sequence also waits for
that replay — `scene` arrives before `clips`, so a default sequence built on the
`scene` would have pre-empted the restore by a few milliseconds.

Sequences are authored here and nowhere else. `DUPLICATE` is a real copy, so it
asks the take for as many new tracks as the original has and finishes the copy as
they arrive (the bytes are already held, so each new lane is given its file the
same way loading one is); `DELETE` removes the sequence **and** posts `remove` for
its tracks, because a lane belonging to a deleted cue is a lane the checklist would
go on asking for media on forever.

**v5.9** `?mode=bin` — `content-bin.html`. The inventory: every file already on a
track in this take (it receives them as bytes like every other panel), plus a
project folder pointed at with `webkitdirectory`, plus anything dropped on it. One
thumbnail each, made once; filters by name, kind and whether it is in the show. It
writes `mediaAsset` — but only ever in answer to a `binRequest`, so a file entering
the take from the bin takes the same path as one opened from a lane.

**v5.9** `?mode=preview` — `video-preview.html`. A monitor. It resolves the picture
of the sequence named by `cur` — highest `prio` video row with a live clip — paints
it letterboxed into a 2D canvas, plays that sequence's audio rows unmuted, and
draws action-safe (90%) and title-safe (80%) guides *inside the letterbox*, so the
percentages are of the frame rather than of however wide the panel happens to be.

Its sequence picker either FOLLOWS or PINS.

**FOLLOW is the running order**, not "whatever the timeline is editing". That earlier
reading was wrong twice: it darkened the monitor the moment the playhead ran out of
the cue somebody happened to have open — so a show of six sequences played one and
black for the rest — and it made the picture depend on a *selection* rather than on
the *clock*, which is not what a program monitor is. Following now shows whatever is
live at the playhead, whichever cue it belongs to: press play at zero and the show
plays through, the monitor changing over as the playhead crosses from one into the
next. Two cues overlapping in time resolve by **the one that started most recently**
— the same cut rule the video stack uses one level down — and a playhead parked in a
gap falls back to the cue being edited rather than going black.

Because the cue on air is a function of the clock, every row of every sequence is
now synced, not just the live cue's: a row that has just gone off air has to be told
to stop, and iterating only the live cue's rows left the previous cue's audio running
underneath the new one.

**PIN** overrides all of it: that cue, whatever the clock is doing. Pinning posts
`selectSequence` so the timeline opens the same cue, and parks the playhead inside it
if the clock is somewhere else entirely, because a monitor showing black is not
previewing anything.

It writes two messages: `transport` and `selectSequence`. Play, pause, stop and scrub are what
its controls are for, and driving the take's clock is what those do — scrubbing
here moves the picture on the wall in the Scene Study and in every Camera POV.
There is deliberately no editing in it: an earlier version had a razor, trims, a
clip list, a tile per surface and a file export, and every one of those was a
second place for the cue to be changed.

### One clock, and it is not a frame loop

`transport` is the take's clock and every panel follows it. The panel driving it
therefore **must not** run it on `requestAnimationFrame`: rAF fires only while the
document is being painted, so a Timeline in a background tab, behind a window, or
in a pane the compositor has parked stops the show for every other panel while
looking, in itself, exactly like a clock somebody paused. Measured: zero rAF
callbacks with `playing` true and the playhead pinned at `00:00.0` everywhere.

Both v5.9 panels drive their clock from a `setInterval` and compute the elapsed
time from `performance.now()` deltas rather than counting ticks — so a throttled
panel updates less often and still knows exactly what time it is. A gap longer
than two seconds is treated as a suspended document and **resumed** rather than
accumulated: inventing that time would jump the show past cues nobody saw, and the
next `transport` from whoever is driving settles the difference.

The Scene Study keeps its rAF loop, correctly: it is the panel being looked at,
and it follows this clock rather than owning it.

### A duration is not known at `loadedmetadata`

Anything recorded or streamed — including every WebM the Video Editing panel's own
ASSEMBLE writes — reports `duration === Infinity` at `loadedmetadata` and only
settles later, on `durationchange`. Reading it once put `Infinity` on the clip,
which made `out` and then the show's SPAN infinite, which made every block on every
lane a zero-width sliver and threw `RangeError: Invalid string length` out of the
ruler. All three files now take the length whenever it becomes finite, from either
event, and a span that is not a finite positive number is refused at the point of
use as well as at both points of origin.

---

## Origins, and running from `file://`

Opened by double-click the prototype is a `file://` page, so the iframe's origin
is `null` and neither side can verify the sender. Both use `'*'` as
`targetOrigin` and the host instead filters on
`event.source === iframe.contentWindow`, which is exact.

This is acceptable for a local design prototype and would not be for anything
deployed. If this ever leaves a laptop, pin `targetOrigin` and check
`event.origin`.

Served over HTTP the two files are same-origin and everything above still holds
unchanged. For a local server:

```bash
python3 -m http.server 3900
```

---

## Changing the protocol

Adding a message type or a field is backwards-compatible — the other side ignores
what it does not know — and does **not** need a version bump. Changing the meaning
of an existing field, or its units, does: raise `BRIDGE_V` on both sides, and both
sides will then refuse to talk to an old counterpart rather than half-work.
