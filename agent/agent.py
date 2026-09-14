"""The real agent — phase 4.

Same signature as the stub (`run(session)` / `refine(session, message)`), so
`serve.py` swaps one for the other and nothing else changes.

WHY A HAND-WRITTEN LOOP AND NOT THE SDK's TOOL RUNNER
Two reasons, both about this task rather than about the runner. The narration is
load-bearing here — an interpret runs tens of seconds and the panel has to show
the reasoning as it happens, which needs `text_delta` and `thinking_delta`
events, not one message per iteration. And `measure_preview` is an *await into the
browser*: the tool asks the host, the host ghosts the staged ops into the Scene
Study, and the figure comes back over a different HTTP request. That is an async
tool, and owning the loop is the honest way to have one.

THE SHAPE THAT MATTERS: the write tools STAGE and the read tools are LIVE. The
model can add six projectors and then ask what they cover, and get a real answer
measured off real geometry — while nothing whatsoever has happened to the take.
"""
from __future__ import annotations

import base64
import json
import os
from typing import Any

import anthropic

from external import brief_dict

import geometry

# v5.5 · the reference tracer. Optional, like everything else that needs a big wheel.
try:
    import vision
except Exception:                                            # pragma: no cover
    vision = None
from session import OP_SOFT_CAP, Session

MODEL = "claude-opus-5"
MAX_TOKENS = 64000
TASK_BUDGET = 48000
MAX_ITERS = 14
BETAS = ["task-budgets-2026-03-13", "server-side-fallback-2026-07-01"]

_client: anthropic.AsyncAnthropic | None = None


def available() -> bool:
    """Whether a credential exists at all. The panel says STUB rather than
    failing halfway through a stream, so this is checked before anything runs."""
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True
    cfg = os.path.expanduser("~/.config/anthropic")
    return os.path.isdir(cfg) and bool(os.listdir(cfg))


def client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic()
    return _client


# ============================================================================
# THE RULES — every line here exists to prevent one specific failure.
# ============================================================================
RULES = """You are the Studio Agent for a live-production design tool. Somebody has drawn a
sketch or dropped reference images of a show, and your job is to turn it into a
PLAN: a short, ordered list of operations on their scene, each one justified and
each one carrying how sure you are.

You never change anything. Every write tool STAGES an operation for a human to
review, accept or reject. Say what you are doing as you go — your visible text is
shown live in the panel beside the drawing, so write it as short notes to a
colleague, not as a report.

POSITIONS AND FRAMES
1. Positions are TAKE UNITS: 1 unit = 10 cm. You are given `units_per_metre` and
   every anchor already converted for you. Never emit metres.
2. THE ROOM IS NAMED Z-UP; THE WIRE IS NOT. A position is `[across, UP, DEPTH]`,
   which is how the take stores it — but the room, the gizmo and the drawing all call
   the UP one **Z** (green) and the DEPTH one **Y** (blue). So the SECOND number is
   height and the THIRD is depth, positive downstage toward the audience. In a TOP
   view the top of the canvas is upstage; in a FRONT view the page is X across and
   height up.
3. The anchors you are given have been converted by the same code the tool uses.
   Trust them. Use the drawing to decide WHAT things are and what they imply, not
   to redo the arithmetic.

WHAT YOU MAY NAME
4. Only ever name kit that appears in the catalogue you were given, exactly as it
   is spelled there. If nothing in the catalogue fits, say so in your notes and
   stage the position without a model rather than inventing one.

HONESTY
5. Every operation carries a `confidence`: "declared" when the drawing or a
   reference said so (a labelled anchor, a declared scale, a dimension written on
   a plan), "fitted" when you derived it from the venue's own dimensions, and
   "guessed" when you chose a reasonable default. Guesses are left unticked for
   the human, so mark them honestly — an over-claimed position is worse than an
   admitted guess.
6. If a figure needs geometry — throw distance, coverage, overlap — call
   `measure_preview`. If it comes back unavailable, SAY it is unavailable. Never
   estimate a measured figure.

SIZE, SHAPE AND ORIENTATION — this is what makes a scene usable rather than
   decorative
7. Device bodies are built from the catalogue's real millimetres, so naming the
   right model IS the size. What the catalogue cannot know, you must say: an LED
   wall's width and height come from the drawing (`w`/`h` on add_device), never
   from a default.
8. A device with no aim is aimed for you — projectors at a surface they can cover,
   cameras and tracking at the stage. That is usually right. Aim explicitly when
   the drawing disagrees, and remember `y` is degrees of yaw with 180 looking
   upstage.
9. Close the decisions that change geometry: a projector's LENS is its throw ratio
   and its RESOLUTION is the shape of what it throws, and an LED processor's PIXEL
   MAP is the aspect of the wall. A position without a lens is a body without a beam.

SHAPES — v5.5, and the reason a curve stops becoming a rectangle
10. The sketch may arrive with SOLIDS already fitted: outlines the pad read off the
   ink and re-stated as vertices and true circular arcs, in take units, with the fit
   reported — how many raw points became how many vertices, the arc radii, the RMS it
   gave away, whether it was symmetrised. THE PAD HOLDS THAT FIT AND YOU DO NOT. Pass
   a fitted solid through with `add_solid` unchanged, or leave it to the host, and
   spend your judgement on what it IS and what belongs on it. Do not re-derive it,
   and do not restate a traced shape as a box.
11. Author a solid yourself only for geometry nobody traced, and say so in `why`. A
   bulge of 0 is a straight; ±1 is a semicircle; the sign says which way it bows.
   A traced shape arrives CLOSED, FACED and extruded — a filled solid half a metre
   thick unless it was named otherwise — and its role was named by a STAMP DROPPED ON
   IT. A stamp on a shape says what that shape is; a stamp on open canvas says where
   a device goes. Read them that way round.
   A solid marked `built: true` is ALREADY IN THE TAKE. Read it as the room you are
   placing kit into and do not restage it — an op that changes nothing is worse than
   no op, because a plan under review stops the 3D tool measuring into the take.
12. THE THREE ROLES ARE PHYSICS, NOT STYLING. `stage` is a footprint extruded up.
   `wall` is a surface that keeps its curve, and a projector's throw distance, image
   size and lit footprint are then measured against that curve. `led` DOES NOT BEND:
   it is faceted into flat cabinets, so what you are proposing is a cabinet count,
   and a curved LED wall is flat panels arranged on a polygon. Never propose a
   `wall` where somebody meant LED to get a smooth curve — that is a wall nobody
   can build.

SCOPE
13. Stay under %d operations. If the drawing implies more, stage the structure that
   matters and describe the rest in your notes.
14. Classify exactly one INTENT — what the person is doing right now — with
   `declare_intent`, and justify any panel override in one sentence.
15. Finish with `finish`. One summary sentence, a confidence, and the risks a
   reviewer should know about, in plain words.
""" % OP_SOFT_CAP

INTENTS = ["block", "rig", "frame", "wall", "patch", "cue", "price", "pack", "explain"]
PANELS = ["checklist", "stepeditor", "grid", "stage", "preview", "devices", "measure",
          "projlib", "camlib", "wiring", "sequence", "transport", "cost", "people",
          "prods", "deadline", "analytics", "takes", "compare", "sketch", "refs", "agent"]
CONF = ["declared", "fitted", "guessed"]


def _tool(name: str, desc: str, props: dict, required: list[str]) -> dict:
    return {
        "name": name, "description": desc, "strict": True,
        "input_schema": {"type": "object", "properties": props,
                         "required": required, "additionalProperties": False},
    }


WHY = {"type": "string", "description": "one short clause: what in the drawing or the "
       "references makes this the right operation"}
CONFIDENCE = {"type": "string", "enum": CONF, "description": "declared if the input said "
              "so, fitted if derived from the venue, guessed if you chose it"}
AT = {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3,
      "description": "[x, y, z] in TAKE UNITS (1 unit = 10 cm)"}

# Deterministic order — the tool list is part of the cache prefix, so it must not
# be built from a set or a dict iteration order that can move.
TOOLS: list[dict] = [
    _tool("read_scene", "What is in the take right now: devices with positions and "
          "models, the venue, tracks, the checklist items, and the measurements "
          "already derived.", {}, []),
    _tool("read_catalogue", "The real kit rows for one requirement — physical size, "
          "lumens, native resolution, lens, cost. Use this before naming a model.",
          {"req": {"type": "string", "enum": ["projectors", "capture", "led", "tracking"]}},
          ["req"]),
    _tool("read_reference", "TRACE one of the reference images you were given and get "
          "its real geometry back: every shape the drawing encloses, already fitted to "
          "vertices and true arcs and already converted to TAKE UNITS, with what the "
          "layout and a vision model each think it is.\n"
          "USE THIS INSTEAD OF READING COORDINATES OFF THE PICTURE YOURSELF. You can see "
          "the image and you cannot measure it — no model can — and a vertex you invent "
          "is indistinguishable downstream from one that was measured. Your judgement is "
          "wanted on what the shapes ARE and what belongs on them; the numbers are not "
          "yours to guess. Pass the returned bodies to `add_solid` unchanged.",
          {"n": {"type": "integer", "description": "which reference, 1-based, in the "
                 "order they were listed to you"}},
          ["n"]),
    _tool("measure_preview", "Ask the 3D tool to draw everything staged so far as "
          "ghosts and MEASURE it: throw distances, image size, pixel density, "
          "overlap, coverage. Returns {\"unavailable\": true} if the tool is not "
          "open or does not answer — in that case say so and do not estimate.",
          {}, []),
    _tool("set_venue", "Propose the room.",
          {"preset": {"type": "string", "description": "a venue preset name the tool "
                      "offers, e.g. concert"},
           "label": {"type": "string"}, "why": WHY, "confidence": CONFIDENCE},
          ["preset", "why", "confidence"]),
    _tool("add_device", "Propose a new device at a position. `handle` is your own name "
          "for it so later operations can refer to it before it exists.",
          {"req": {"type": "string", "enum": ["projectors", "capture", "led", "tracking"]},
           "model": {"type": "string", "description": "exactly as spelled in the "
                     "catalogue, or empty to leave the model undecided"},
           "at": AT, "handle": {"type": "string"},
           "w": {"type": "number", "description": "width in TAKE UNITS — an LED wall is "
                 "as wide as the plan says. 0 lets the catalogue or the pixel map decide."},
           "h": {"type": "number", "description": "height in TAKE UNITS, 0 for default"},
           "why": WHY, "confidence": CONFIDENCE},
          ["req", "model", "at", "handle", "w", "h", "why", "confidence"]),
    _tool("place", "Move something that already exists, or something you added, to a "
          "position.",
          {"obj": {"type": "string", "description": "an existing object id, or a handle "
                   "you gave add_device"},
           "at": AT, "why": WHY, "confidence": CONFIDENCE},
          ["obj", "at", "why", "confidence"]),
    _tool("aim", "Aim something. DEGREES: `y` is the yaw (0 looks downstage toward "
          "the audience, 180 looks upstage at the screen), `x` is the tilt (negative "
          "looks down). Left alone, the tool aims projectors at a surface they can "
          "actually cover and cameras at the stage — which is usually right. Aim "
          "explicitly when the drawing says otherwise.",
          {"obj": {"type": "string"},
           "rot": {"type": "object", "properties": {"x": {"type": "number"},
                                                    "y": {"type": "number"},
                                                    "z": {"type": "number"}},
                   "required": ["x", "y", "z"], "additionalProperties": False},
           "why": WHY, "confidence": CONFIDENCE},
          ["obj", "rot", "why", "confidence"]),
    _tool("set_decision", "Close a checklist decision on one object — a resolution, a "
          "lens, a machine, a pixel map. This is what makes the plan move the "
          "checklist rather than just the scene.",
          {"obj": {"type": "string"},
           "step": {"type": "string", "description": "the step id, e.g. projectors.lens"},
           "value": {"type": "string", "description": "one of that step's offered values"},
           "why": WHY, "confidence": CONFIDENCE},
          ["obj", "step", "value", "why", "confidence"]),
    _tool("remove", "Propose taking something out.",
          {"obj": {"type": "string"}, "why": WHY, "confidence": CONFIDENCE},
          ["obj", "why", "confidence"]),
    _tool("duplicate", "Propose a copy of something.",
          {"obj": {"type": "string"}, "why": WHY, "confidence": CONFIDENCE},
          ["obj", "why", "confidence"]),
    _tool("add_track", "Propose a playback track.",
          {"name": {"type": "string"}, "route": {"type": "string", "description":
           "the object id of the wall or projector it is thrown at, or empty"},
           "start_ms": {"type": "integer"}, "why": WHY, "confidence": CONFIDENCE},
          ["name", "route", "start_ms", "why", "confidence"]),
    _tool("route_signal", "Propose a signal run between two things.",
          {"frm": {"type": "string"}, "to": {"type": "string"},
           "medium": {"type": "string"}, "why": WHY, "confidence": CONFIDENCE},
          ["frm", "to", "medium", "why", "confidence"]),
    _tool("audience", "Propose a block of people — where the crowd stands or sits, "
          "how wide and how deep, in TAKE UNITS. This is the only thing in a scene "
          "that gives the rest of it human scale, so propose one whenever the drawing "
          "implies an audience.",
          {"at": AT, "w": {"type": "number", "description": "width in TAKE UNITS"},
           "d": {"type": "number", "description": "depth in TAKE UNITS"},
           "facing": {"type": "number", "description": "extra yaw in degrees; 0 faces the stage"},
           "why": WHY, "confidence": CONFIDENCE},
          ["at", "w", "d", "facing", "why", "confidence"]),
    _tool("add_solid", "Propose a piece of the ROOM with a shape — a deck, a "
          "free-form wall to project on, or an LED wall. This is not kit: it joins no "
          "checklist and costs nothing; what it carries is geometry.\n"
          "The outline is VERTICES AND BULGES. A bulge is one number per segment: 0 is "
          "a straight, +/-1 is a semicircle, and in general it is the signed sagitta "
          "over the half-chord (tan of a quarter of the included angle). That is how a "
          "true circular arc travels as two points and a number.\n"
          "Prefer PASSING THROUGH a solid the sketch pad already fitted — it holds the "
          "fit and you do not. Author one yourself only when the drawing implies "
          "geometry nobody traced, and say so in `why`.\n"
          "Roles behave differently on purpose: `stage` extrudes the outline UP to `h`; "
          "`wall` sweeps it into a surface a projector can throw at, and the throw is "
          "then measured against the curve; `led` FACETS it into flat cabinets, because "
          "LED does not bend — a curved LED wall is flat panels on a polygon.",
          {"role": {"type": "string", "enum": ["stage", "wall", "led"]},
           "name": {"type": "string"},
           "plane": {"type": "string", "enum": ["floor", "front"],
                     "description": "floor: the outline lies on the deck and `h` grows "
                     "upward. front: the outline is a face-on profile and `h` is its "
                     "depth."},
           "at": AT,
           "verts": {"type": "array", "description": "the outline in TAKE UNITS, LOCAL "
                     "to `at`. Two numbers per vertex: (across, depth) on the floor "
                     "plane, (across, up) on the front plane.",
                     "items": {"type": "array", "items": {"type": "number"},
                               "minItems": 2, "maxItems": 2}},
           "bulges": {"type": "array", "items": {"type": "number"},
                      "description": "one per segment, in order. 0 for a straight."},
           "closed": {"type": "boolean", "description": "true for a footprint, false "
                      "for a run of wall"},
           "h": {"type": "number", "description": "height in TAKE UNITS on the floor "
                 "plane, depth on the front plane"},
           "base": {"type": "number", "description": "how far off the deck it starts, "
                    "TAKE UNITS. 0 sits on the floor."},
           "tile": {"type": "number", "description": "led only: cabinet size in TAKE "
                    "UNITS. 5 is a 500 mm panel. 0 takes the default."},
           "why": WHY, "confidence": CONFIDENCE},
          ["role", "name", "plane", "at", "verts", "bulges", "closed", "h", "base",
           "tile", "why", "confidence"]),
    _tool("annotate", "Pin a note on the scene — something true about this proposal "
          "that is not a decision. Sightlines, access, a risk.",
          {"text": {"type": "string"}, "why": WHY}, ["text", "why"]),
    _tool("declare_intent", "What the person is doing right now, and the panels it "
          "wants. At most two added and two dropped, and say why.",
          {"intent": {"type": "string", "enum": INTENTS},
           "confidence": {"type": "number", "description": "0 to 1"},
           "why": {"type": "string"},
           "add": {"type": "array", "items": {"type": "string", "enum": PANELS}},
           "drop": {"type": "array", "items": {"type": "string", "enum": PANELS}},
           "reason": {"type": "string", "description": "one sentence, only if you added "
                      "or dropped a panel"}},
          ["intent", "confidence", "why", "add", "drop", "reason"]),
    _tool("finish", "End the turn.",
          {"summary": {"type": "string", "description": "one sentence a producer would "
                       "understand"},
           "confidence": {"type": "number"},
           "risks": {"type": "array", "items": {"type": "string"}}},
          ["summary", "confidence", "risks"]),
]


# ============================================================================
# EXECUTING A TOOL CALL — writes stage, reads are live
# ============================================================================
class Staged:
    """Tracks the handles the model invented, so `aim` can name something `add`
    made before either of them exists in the take."""

    def __init__(self) -> None:
        self.handles: dict[str, str] = {}     # handle -> the op id that made it
        self.done = False


async def call_tool(session: Session, st: Staged, name: str, a: dict[str, Any]) -> str:
    req = session.req
    n = len(session.ops)
    if n >= OP_SOFT_CAP and name not in ("finish", "declare_intent", "read_scene",
                                         "read_catalogue", "measure_preview", "annotate"):
        return (f"refused: {n} operations already staged, which is the cap. "
                "Describe the rest in your notes and call finish.")

    # ---- reads: live ----
    if name == "read_scene":
        sc = req.scene or {}
        return json.dumps({
            "venue": (req.venue.model_dump(exclude_none=True) if req.venue else None),
            "devices": sc.get("devices", []),
            "tracks": sc.get("tracks", []),
            "checklist": req.checklist.model_dump(),
            "derived": {k: (v or {}).get("text") if isinstance(v, dict) else v
                        for k, v in (req.derived or {}).items()},
        }, separators=(",", ":"))

    if name == "read_catalogue":
        return json.dumps(req.catalogues.get(a["req"]) or [], separators=(",", ":"))

    if name == "read_reference":
        if vision is None or not vision.traceable():
            return json.dumps({"unavailable": True,
                               "why": (vision.why() if vision else "vision.py is absent"),
                               "note": "say the reference could not be traced; do not "
                                       "invent coordinates from the picture"})
        i = int(a.get("n") or 1) - 1
        imgs = req.images or []
        if not (0 <= i < len(imgs)):
            return f"refused: there is no reference {i + 1}; you were given {len(imgs)}."
        img = imgs[i]
        try:
            read = vision.read(base64.b64decode(img.b64), hint_role=img.role)
        except Exception as exc:
            return json.dumps({"unavailable": True, "why": f"{type(exc).__name__}: {exc}"})
        if read is None or not read.regions:
            return json.dumps({"shapes": [], "notes": (read.notes if read else []),
                               "note": "nothing in that image traced as a shape"})
        frame = geometry.frame_for_image(read.size[0], read.size[1], read.projection,
                                        req.venue, req.unitsPerMetre, req.derived)
        out = []
        target_ids = {}
        for k, reg in enumerate(read.regions, 1):
            sol = vision.to_solid(reg, frame, read.size[0], read.size[1],
                                  read.projection, req.unitsPerMetre, (i + 1) * 100 + k)
            if sol:
                sol["layout_says"] = reg.role
                sol["model_says"] = reg.model_says
                out.append(sol)
                target_ids[k] = sol["srcId"]
        suggestions = []
        for suggestion in read.suggestions:
            suggestion = dict(suggestion)
            suggestion["targetId"] = target_ids.get(suggestion.pop("targetIndex", None))
            suggestions.append(suggestion)
        return json.dumps({
            "name": img.name, "declared_role": img.role,
            "projection": read.projection,
            # THE SCALE IS THE THING TO BE HONEST ABOUT. A photograph carries none, so
            # this says which of the two honest answers it got and the model is expected
            # to repeat it rather than imply a precision nobody has.
            "scale": {"basis": frame.basis, "note": frame.note},
            "vision_engine": read.engine, "calibration": read.calibration,
            "notes": read.notes, "shapes": out,
            # Reviewable OCR proposals: never normal stamps until explicitly accepted.
            "semanticSuggestions": suggestions,
        }, separators=(",", ":"))

    if name == "measure_preview":
        answer = await session.ask("measure_preview")
        if answer.get("unavailable"):
            return json.dumps({"unavailable": True,
                               "note": "the 3D tool did not answer — report this as "
                                       "unavailable, do not estimate"})
        derived = answer.get("derived") or {}
        return json.dumps({k: (v.get("text") if isinstance(v, dict) else v)
                           for k, v in derived.items()}, separators=(",", ":"))

    # ---- writes: staged ----
    def obj_of(key: str) -> str:
        """A handle resolves to the op that created it; anything else is an id the
        take already knows, and the host maps both when the plan is applied."""
        return st.handles.get(key, key)

    if name == "set_venue":
        session.stage(kind="venue", preset=a["preset"], label=a.get("label"),
                      why=a["why"], confidence=a["confidence"])
        return "staged. The room is NOT previewed in 3D — say so if it matters."

    if name == "add_device":
        model = (a.get("model") or "").strip() or None
        rows = req.catalogues.get(a["req"]) or []
        names = [r.get("name") for r in rows if isinstance(r, dict)]
        if model and names and model not in names:
            return (f"refused: {model!r} is not in the {a['req']} catalogue. "
                    f"Call read_catalogue first. Available: {', '.join(names[:8])}")
        op = session.stage(kind="add", req=a["req"], model=model, at=a["at"],
                           objId=a["handle"], why=a["why"], confidence=a["confidence"],
                           w=(a.get("w") or None), h=(a.get("h") or None))
        st.handles[a["handle"]] = a["handle"]
        return f"staged as {op.id} (handle {a['handle']}). {len(session.ops)} ops so far."

    if name == "place":
        session.stage(kind="place", objId=obj_of(a["obj"]), at=a["at"],
                      why=a["why"], confidence=a["confidence"])
        return "staged."

    if name == "aim":
        session.stage(kind="aim", objId=obj_of(a["obj"]), rot=a["rot"],
                      why=a["why"], confidence=a["confidence"])
        return "staged."

    if name == "set_decision":
        session.stage(kind="decide", objId=obj_of(a["obj"]), stepId=a["step"],
                      value=a["value"], why=a["why"], confidence=a["confidence"])
        return "staged."

    if name in ("remove", "duplicate"):
        session.stage(kind=name, objId=obj_of(a["obj"]), why=a["why"],
                      confidence=a["confidence"])
        return "staged."

    if name == "add_track":
        session.stage(kind="track", name=a["name"], route=(a.get("route") or None),
                      startMs=a.get("start_ms") or 0, why=a["why"],
                      confidence=a["confidence"])
        return "staged."

    if name == "route_signal":
        session.stage(kind="route", **{"from": a["frm"]}, to=a["to"], medium=a["medium"],
                      why=a["why"], confidence=a["confidence"])
        return ("staged, but note: signal runs are not applied by this version of the "
                "host — the plan will say so.")

    if name == "audience":
        session.stage(kind="audience", at=a["at"], w=a["w"], d=a["d"],
                      rot={"x": 0, "y": a.get("facing") or 0, "z": 0},
                      why=a["why"], confidence=a["confidence"])
        return "staged. The crowd is drawn as silhouettes and gives the scene its scale."

    if name == "add_solid":
        verts = [v for v in (a.get("verts") or []) if isinstance(v, list) and len(v) >= 2]
        if len(verts) < 2:
            return "refused: a solid needs at least two vertices."
        closed = bool(a.get("closed")) and len(verts) >= 3
        nseg = len(verts) if closed else len(verts) - 1
        bulges = list((a.get("bulges") or []))[:nseg]
        bulges += [0.0] * (nseg - len(bulges))
        tile = float(a.get("tile") or 0)
        session.stage(kind="solid", role=a["role"], name=(a.get("name") or None),
                      plane=a.get("plane") or "floor", closed=closed,
                      at=a["at"], verts=verts, bulges=bulges,
                      h=(a.get("h") or (10 if a["role"] == "stage" else 60)),
                      base=(a.get("base") or 0),
                      tile=({"w": tile, "h": tile} if a["role"] == "led" and tile else None),
                      why=a["why"], confidence=a["confidence"])
        arcs = sum(1 for b in bulges if b)
        return (f"staged: {len(verts)} vertices"
                + (f", {arcs} of the segments are arcs" if arcs else ", all straight")
                + ". Call measure_preview to find out what it actually covers.")

    if name == "annotate":
        session.stage(kind="note", text=a["text"], why=a["why"], confidence="declared")
        return "staged."

    if name == "declare_intent":
        session.declare_intent(a["intent"], float(a.get("confidence") or 0.5), a["why"],
                               add=a.get("add") or [], drop=a.get("drop") or [],
                               reason=a.get("reason") or "")
        return "noted. The host validates panel overrides and may trim them."

    if name == "finish":
        st.done = True
        session.finish(a["summary"], float(a.get("confidence") or 0.5), a.get("risks") or [])
        return "done."

    return f"unknown tool {name}"


# ============================================================================
# THE BRIEF — what the model is given, once
# ============================================================================
def build_brief(session: Session) -> tuple[list[dict], str]:
    """(image blocks, brief text). The facts come from `brief_dict` — the very same
    assembly the external channel writes to disk — so a plan means the same thing
    whichever engine read it."""
    req = session.req
    blocks: list[dict] = []
    brief = brief_dict(session)
    brief.pop("catalogues", None)          # the catalogue is in the cached system prompt

    if req.sketch and req.sketch.png_b64:
        blocks.append({"type": "image", "source": {"type": "base64",
                                                  "media_type": "image/png",
                                                  "data": req.sketch.png_b64}})
    for i, img in enumerate(req.images, 1):
        blocks.append({"type": "text",
                       "text": f"REFERENCE {i} — {img.name} · declared as {img.role}"
                               + (f" · note: {img.note}" if img.note else "")})
        media = img.mime if img.mime in ("image/png", "image/jpeg", "image/webp",
                                         "image/gif") else "image/png"
        blocks.append({"type": "image", "source": {"type": "base64",
                                                  "media_type": media, "data": img.b64}})

    projection_rule = ""
    if req.sketch:
        projection_rule = (
            "\n\nPROJECTION IS DECLARED METADATA, NOT A VISUAL GUESS. "
            + ("This sketch is PLAN/top-down: canvas X maps to room X across and canvas Y maps to room Y depth/downstage; never read canvas Y as height."
               if req.sketch.projection == "plan" else
               "This sketch is ELEVATION/front-facing: canvas X maps to room X across and canvas Y measured upward from groundLine maps to room Z height; never read canvas Y as room depth.")
            + " Per-item `view` is equally authoritative for mixed-view records. Do not change projection or plane because the raster resembles another view."
        )
    text = ("Here is the take and what was just given to you." + projection_rule + "\n\n```json\n"
            + json.dumps(brief, indent=1, default=str)
            + "\n```\n\nRead it, work out what is being proposed, and stage the plan.")
    return blocks, text


def system_for(session: Session) -> list[dict]:
    """Stable first, volatile last. The rules and the catalogues do not change
    between requests, so they are the cached prefix; everything that moves is in
    the user message, after the breakpoint."""
    cats = json.dumps(session.req.catalogues, sort_keys=True, separators=(",", ":"))
    return [
        {"type": "text", "text": RULES},
        {"type": "text", "text": "THE CATALOGUE — the only kit that exists:\n" + cats,
         "cache_control": {"type": "ephemeral"}},
    ]


# ============================================================================
# THE LOOP
# ============================================================================
async def _turn(session: Session, messages: list[dict], system: list[dict]) -> Any:
    """One request, streamed. Text and reasoning are forwarded delta by delta —
    the panel shows them live, which is what makes a 40-second turn legible."""
    async with client().beta.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=messages,
        tools=TOOLS,
        thinking={"type": "adaptive", "display": "summarized"},
        output_config={"effort": "xhigh",
                       "task_budget": {"type": "tokens", "total": TASK_BUDGET}},
        betas=BETAS,
        fallbacks="default",
    ) as stream:
        async for event in stream:
            if event.type != "content_block_delta":
                continue
            d = event.delta
            if getattr(d, "type", None) == "text_delta":
                session.note(d.text)
            elif getattr(d, "type", None) == "thinking_delta":
                session.thinking(d.thinking)
        return await stream.get_final_message()


async def _drive(session: Session, messages: list[dict]) -> None:
    if not available():
        session.fail("no_credentials",
                     "no Anthropic credential in the environment — set ANTHROPIC_API_KEY "
                     "or run `ant auth login`, then restart the agent. AGENT_STUB=1 keeps "
                     "the deterministic interpreter.")
        return

    system = system_for(session)
    st = Staged()
    for _ in range(MAX_ITERS):
        msg = await _turn(session, messages, system)

        usage = getattr(msg, "usage", None)
        if usage:
            session.usage = {
                "in": usage.input_tokens, "out": usage.output_tokens,
                "cache_read": getattr(usage, "cache_read_input_tokens", 0),
                "cache_write": getattr(usage, "cache_creation_input_tokens", 0),
            }

        if msg.stop_reason == "refusal":
            det = getattr(msg, "stop_details", None)
            session.fail("refusal", "the model declined this request"
                         + (f" ({det.category})" if det and getattr(det, "category", None) else ""))
            return

        # thinking blocks travel back unchanged, or the next turn loses the thread
        messages.append({"role": "assistant", "content": msg.content})

        calls = [b for b in msg.content if getattr(b, "type", None) == "tool_use"]
        if not calls:
            if not st.done:
                # it stopped without finishing: keep what was staged and say so
                session.finish(_fallback_summary(session), 0.4,
                               ["the agent stopped without a summary of its own"])
            return

        results = []
        for c in calls:
            try:
                out = await call_tool(session, st, c.name, dict(c.input or {}))
            except Exception as e:                     # a bad tool call is not a dead turn
                out = f"error: {type(e).__name__}: {e}"
            results.append({"type": "tool_result", "tool_use_id": c.id, "content": out})
        # every result in ONE user message, or parallel tool use quietly stops
        messages.append({"role": "user", "content": results})

        if st.done:
            return

    session.finish(_fallback_summary(session), 0.35,
                   [f"the agent was stopped after {MAX_ITERS} turns"])


def _fallback_summary(session: Session) -> str:
    n = len(session.ops)
    return f"{n} operation{'' if n == 1 else 's'} staged." if n else "Nothing staged."


# ============================================================================
# THE TWO ENTRY POINTS — the same signature as the stub
# ============================================================================
async def run(session: Session) -> None:
    blocks, text = build_brief(session)
    session.messages = [{"role": "user", "content": blocks + [{"type": "text", "text": text}]}]
    await _drive(session, session.messages)


async def refine(session: Session, message: str) -> None:
    """A refine turn is the same conversation. What a human kept or threw away
    since the last turn goes in with the correction — that is what makes the
    second answer better rather than just different."""
    if not session.messages:
        session.fail("no_conversation", "this plan has no conversation to refine")
        return
    fb = session.feedback[-1] if session.feedback else None
    note = ""
    if fb:
        note = ("\n\nSince your last turn the human accepted "
                f"{len(fb.get('accepted') or [])} of your operations and rejected "
                f"{len(fb.get('rejected') or [])}.")
    session.messages.append({"role": "user", "content": message + note})
    await _drive(session, session.messages)
