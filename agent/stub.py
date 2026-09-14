"""The stub interpreter — phase 1.

No model call. It reads the vector record only: stamps, the declared projection,
the declared scale. Its job is not to be clever, it is to make every state the
plan panel has to render reachable and repeatable — high confidence, fitted,
guessed, empty, no-anchors, measurement-unavailable — so the whole accept loop can
be designed and reviewed before a token is spent.

Phase 4 swaps this file for `agent.py` behind the same `run(session)` signature.
Anything in here that looks like a judgement about production practice is
scaffolding, and says so.
"""
from __future__ import annotations

import asyncio
import base64
import math

import geometry
from geometry import frame_for
from model import Sketch
from session import Session

# v5.5 · the reference reader. Imported defensively for the same reason agent.py is:
# this service has to start and interpret a SKETCH on a machine with no torch on it.
try:
    import vision
except Exception:                                            # pragma: no cover
    vision = None

# Stamp vocabulary → the checklist item it belongs to. The panel offers exactly
# these, so this table and the palette are one decision in two places; the palette
# is sent to the panel in `hello` from here in phase 2.
STAMP_REQ = {
    "PROJ": "projectors",
    "CAM": "capture",
    "LED": "led",
    "TRACK": "tracking",
}
# Where a stamped device sits vertically when a PLAN sketch says nothing about
# height. STUB SCAFFOLDING — these are the v3 seed heights, not a model of
# anything, and the real agent replaces them with something it can justify.
STUB_HEIGHT_M = {"projectors": 9.6, "capture": 2.2, "led": 4.6, "tracking": 11.0}

# A crowd, when nothing says how big: 18 m across, 10 m deep, in take units.
STUB_CROWD = (180.0, 100.0)

# Which intent a drawing full of one kind of thing reads as.
REQ_INTENT = {"projectors": "rig", "capture": "frame", "led": "wall", "tracking": "block"}

BEAT = 0.18          # the narration is paced so the stream is visibly a stream


async def run(session: Session) -> None:
    req = session.req
    # v5.5 · a sketch made only of TRACED SOLIDS is a sketch. It was possible to
    # draw three fitted outlines, no strokes and no anchors, and be told nothing was
    # drawn — the reader was counting the two kinds of ink that existed when it was
    # written.
    if req.sketch and (req.sketch.stamps or req.sketch.strokes or req.sketch.solids):
        await _sketch(session, req.sketch)
    elif req.images:
        await _refs(session)
    else:
        session.note("Nothing to read — no strokes, no stamps, no references.")
        session.finish("Nothing was drawn.", 0.0,
                       ["the panel posted an empty payload"])


# ------------------------------------------------------------------ a sketch --
# What a rectangle is, in each projection. A plan rectangle is a FOOTPRINT with no
# height; the same rectangle in a front view is an UPRIGHT with no depth. Neither of
# those is a guess about what the thing IS — only about the dimension the drawing
# could not carry.
PLAN_BLOCK_H = 2.0            # metres: a footprint reads as a low platform
PLAN_STAGE_H = 1.0            # a deck somebody stands on
FRONT_BLOCK_D = 0.4           # metres: an upright reads as a panel
LED_FALLBACK_H = 5.0          # a wall drawn in plan has no height on the page


def _boxes(sketch: Sketch, frame) -> list[dict]:
    """Every drawn rectangle, with its corners already in take units."""
    out = []
    for st in sketch.strokes:
        if st.kind not in ("rect", "ellipse") or len(st.pts) < 2:
            continue
        (x0, y0), (x1, y1) = st.pts[0], st.pts[1]
        px = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        if (px[2] - px[0]) < 6 or (px[3] - px[1]) < 6:
            continue
        v = st.view or "plan"
        a, b = frame.take(px[0], px[1], view=v), frame.take(px[2], px[3], view=v)
        out.append({"px": px, "a": a, "b": b, "kind": st.kind, "claim": None,
                    "view": v, "plan": v != "elevation"})
    return out


def _enclosing(boxes: list[dict], at) -> dict | None:
    """The smallest drawn box around a point. Somebody who draws a box and stamps it
    has told you how big that thing is; reading it is free."""
    best = None
    for bx in boxes:
        x0, y0, x1, y1 = bx["px"]
        if not (x0 <= at[0] <= x1 and y0 <= at[1] <= y1):
            continue
        area = (x1 - x0) * (y1 - y0)
        if best is None or area < best[1]:
            best = (bx, area)
    return best[0] if best else None


def _dims(bx: dict, _unused_plan: bool, h_m: float, d_m: float) -> dict:
    """A box's take-unit dimensions and the point it sits on. `at` is the CENTRE ON
    THE FLOOR for a footprint and the BOTTOM CENTRE for an upright, which is the same
    rule either way: the point the thing rests on."""
    ax, ay, az = bx["a"]
    bxx, byy, bzz = bx["b"]
    w = abs(bxx - ax)
    cx = (ax + bxx) / 2
    # the box's OWN view decides which two dimensions it knows — not the view that
    # happens to be on screen when INTERPRET was pressed
    plan = bx.get("plan", True)
    if plan:
        d = abs(bzz - az)
        return {"at": [round(cx, 1), 0.0, round((az + bzz) / 2, 1)],
                "w": round(w, 1), "d": round(d, 1), "h": round(h_m * 10, 1)}
    height = abs(byy - ay)
    return {"at": [round(cx, 1), round(min(ay, byy), 1), 0.0],
            "w": round(w, 1), "d": round(d_m * 10, 1), "h": round(height, 1)}


def _aim_target(stamp, frame, _unused_plan: bool) -> list[float] | None:
    """A drag out of an anchor is "point at THERE". Canvas degrees plus the drag
    length give a point, and a point is what the tool aims with — no rotation order
    to get backwards, and identical to how a device aimed by hand ends up."""
    if stamp.aim is None:
        return None
    length = max(20.0, float(stamp.aimLen or 60))
    a = math.radians(float(stamp.aim))
    ex = stamp.at[0] + math.cos(a) * length
    ey = stamp.at[1] + math.sin(a) * length
    v = stamp.view or "plan"
    t = frame.take(ex, ey, view=v)
    # a top-view drag names a point on the floor; a front-view drag names a height
    return [round(t[0], 1), 0.0 if v != "elevation" else round(t[1], 1), round(t[2], 1)]


async def _solids(session: Session, sketch: Sketch, m) -> None:
    """Fitted outlines → `solid` ops, straight through, with the fit reported."""
    for sol in sketch.solids:
        if len(sol.verts) < 2:
            continue
        fit = sol.fit or {}
        arcs = sum(1 for b in sol.bulges if b)
        radii = fit.get("radii") or []
        role = sol.role
        metrics = sol.metrics or {}
        if role == "led":
            what = (f"{metrics.get('cols', '?')}x{metrics.get('rows', '?')} cabinets in "
                    f"{metrics.get('facets', 1)} flat panel(s)")
        elif sol.closed:
            what = f"{metrics.get('area', 0):.1f} m2 footprint, {m(sol.h):.2f} m high"
        else:
            what = f"{metrics.get('length', 0):.1f} m long, {m(sol.h):.2f} m high"
        session.note(
            f"{sol.name or role.upper()} — traced, not guessed: {fit.get('raw', '?')} points "
            f"fitted to {len(sol.verts)} vertices"
            + (f" and {arcs} arc(s)" if arcs else " with no curvature")
            + (f" of radius {', '.join(f'{r:.2f} m' for r in radii[:3])}" if radii else "")
            + f", {what}.\n")
        if fit.get("rms"):
            session.thinking(f"{role} fit gave away {fit['rms'] * 100:.0f} cm rms; ")
        if sol.built:
            # already a fact in the take. Read it as context for the kit, and say so.
            session.thinking(f"{role} is already built; reading it as context. ")
            await asyncio.sleep(BEAT)
            continue
        why = (f"traced in the sketch pad and fitted to {len(sol.verts)} vertices"
               + (f" and {arcs} arc(s)" if arcs else "")
               + (", symmetrised" if fit.get("symmetric") else "")
               + (f", {fit['rms'] * 100:.0f} cm from the ink" if fit.get("rms") else ""))
        session.stage(kind="solid", role=role, name=sol.name, plane=sol.plane,
                      closed=sol.closed, at=sol.at, verts=sol.verts, bulges=sol.bulges,
                      h=sol.h, base=sol.base, thick=sol.thick, tile=sol.tile,
                      # WHICH TRACE it came from, so accepting a plan REPLACES the solid
                      # that trace already built rather than stacking a second one on it
                      srcId=sol.id,
                      fit=fit, why=why,
                      # the outline is a DECLARATION: somebody drew it and said what it
                      # was. Only its height is a guess, and only when nobody typed one.
                      confidence="declared")
        await asyncio.sleep(BEAT)


async def _sketch(session: Session, sketch: Sketch) -> None:
    req = session.req
    frame = frame_for(sketch, req.venue, req.unitsPerMetre, req.derived)
    plan = sketch.projection == "plan"
    U = req.unitsPerMetre
    m = lambda u: u / U                                  # take units → metres, for talking

    session.note(f"Reading a {'plan' if plan else 'front'} sketch — "
                 f"{_n(len(sketch.strokes), 'stroke')}, "
                 f"{_n(len(sketch.stamps), 'anchor')}"
                 + (f", {_n(len(sketch.solids), 'fitted outline')}" if sketch.solids else "")
                 + f". {frame.note}.\n")
    session.thinking(f"scale {frame.basis} at {frame.px_per_metre:.1f} px/m; "
                     f"{'plan: X across, Y/depth downstage' if plan else 'front: X across, Z/up from ground'}. ")
    await asyncio.sleep(BEAT)

    # ---- 0 · THE FITTED OUTLINES ------------------------------------------
    # v5.5. A solid arrives ALREADY FITTED and already in take units: the pad decided
    # which runs of ink were arcs and what radius each was rounded to, and it is the
    # only thing that holds that decision. So this reader passes it through rather
    # than re-deriving it — the geometry is not the interpreter's to have an opinion
    # about. What it DOES do is say out loud what the fit cost, because a plan that
    # quietly accepts somebody else's correction is a plan nobody can argue with.
    await _solids(session, sketch, m)

    boxes = _boxes(sketch, frame)
    # A STAMP NAMES A DRAWING; IT IS NOT A SECOND OBJECT. Dropping LED on a rectangle
    # (v5.5: or on a traced SOLID, where the pad has already applied it and the role
    # arrives decided — so those stamps never reach this list at all)
    # says "that rectangle is the wall" — so the rectangle becomes the wall and the
    # stamp adds nothing further. Two objects where somebody drew one was the whole
    # bug: the sized rectangle AND a default-sized device on top of it.
    claimed: set[int] = set()
    for stamp in sketch.stamps:
        bx = _enclosing(boxes, stamp.at)
        if bx is not None and bx["claim"] is None:
            bx["claim"] = stamp
            claimed.add(id(stamp))

    counts_pre: dict[str, int] = {}
    blocks_made = 0
    # ---- 1 · THE DRAWING, AT THE SIZE IT WAS DRAWN -------------------------
    # Every rectangle becomes something the same size as itself. What it becomes
    # depends on what was stamped inside it, and a rectangle with nothing stamped in
    # it is still geometry: a deck, a riser, a screen, a truck.
    for i, bx in enumerate(boxes, 1):
        claim = bx["claim"]
        label = (claim.label.upper() if claim else "")
        bplan = bx.get("plan", True)          # the view this rectangle was drawn in
        if label == "AUDIENCE":
            dims = _dims(bx, bplan, 0, 0)
            session.note(f"Audience block {m(dims['w']):.1f} × {m(dims['d'] if bplan else dims['h']):.1f} m — "
                         "that is the crowd.\n")
            session.stage(kind="audience", at=dims["at"], w=dims["w"],
                          d=dims["d"] if bplan else dims["h"],
                          why="an AUDIENCE anchor inside a drawn block — the block is the crowd",
                          confidence=frame.confidence)
            await asyncio.sleep(BEAT)
            continue
        if label in ("LED", "SCREEN"):
            dims = _dims(bx, bplan, LED_FALLBACK_H, 0.4)
            h = round(LED_FALLBACK_H * U, 1) if bplan else dims["h"]
            model, _ = _pick_model(session, "led", claim.note if claim else "")
            # WHICH WAY THE WALL FACES, from the drawing rather than from a default.
            # A front-view rectangle is a wall seen face-on, so it runs along X. A
            # top-view rectangle runs along whichever of its two sides is longer: a
            # thin wide one is an upstage wall (X), a thin deep one is a side wall (Y).
            wall_w = dims["w"]
            yaw = 0.0
            if bplan and dims["d"] > dims["w"]:
                wall_w, yaw = dims["d"], 90.0
            session.note(f"{label} wall {m(wall_w):.1f} × {m(h):.1f} m at "
                         f"{m(dims['at'][0]):.1f}, {m(dims['at'][2]):.1f}, "
                         f"{'parallel to X' if yaw == 0 else 'running upstage'}.\n")
            session.stage(kind="add", req="led", model=model, objId=f"wall{i}",
                          at=[dims["at"][0], round(dims["at"][1] + h / 2, 1), dims["at"][2]],
                          w=wall_w, h=h,
                          why=f"a {label} anchor inside a drawn rectangle — the wall is that "
                              f"rectangle, {m(wall_w):.1f} m wide"
                              + ("" if not bplan else f", height not on a top view so {LED_FALLBACK_H:.0f} m"),
                          confidence=frame.confidence if not bplan else "fitted")
            session.stage(kind="aim", objId=f"wall{i}", rot={"x": 0, "y": yaw, "z": 0},
                          confidence=frame.confidence,
                          why=("the rectangle runs along X, so the wall is parallel to it"
                               if yaw == 0 else
                               "the rectangle runs upstage-downstage, so the wall is a side wall"))
            await asyncio.sleep(BEAT)
            continue
        if label in STAMP_REQ and label not in ("LED",):
            # kit drawn as a rectangle: the rectangle says WHERE and HOW BIG the thing
            # it stands for is, and a body that size comes from the catalogue. So the
            # position is the rectangle's centre, not the stamp's dot.
            rk = STAMP_REQ[label]
            dims = _dims(bx, bplan, 0, 0)
            counts_pre[rk] = counts_pre.get(rk, 0) + 1
            handle = f"{rk}b{counts_pre[rk]}"
            model, declared_model = _pick_model(session, rk, claim.note)
            at = [dims["at"][0],
                  round(STUB_HEIGHT_M.get(rk, 0.0) * U, 1) if bplan else dims["at"][1],
                  dims["at"][2]]
            session.note(f"{label} drawn as a rectangle — placing it at its centre, "
                         f"{m(at[0]):.1f}, {m(at[2]):.1f} m.\n")
            session.stage(kind="add", req=rk, model=model, at=at, objId=handle,
                          why=f"a {label} anchor inside a drawn rectangle — the rectangle "
                              f"is the thing, so it is placed at its centre rather than "
                              f"twice",
                          confidence=frame.confidence)
            target = _aim_target(claim, frame, bplan)
            if target:
                session.stage(kind="aim", objId=handle, at=target, confidence="declared",
                              why="the direction dragged out of that anchor")
            await asyncio.sleep(BEAT)
            continue
        name = label or f"BLOCK {i}"
        h_m = PLAN_STAGE_H if label == "STAGE" else PLAN_BLOCK_H
        dims = _dims(bx, bplan, h_m, FRONT_BLOCK_D)
        session.note(f"{name} — {m(dims['w']):.1f} × {m(dims['d']):.1f} × {m(dims['h']):.1f} m, "
                     "drawn to size.\n")
        blocks_made += 1
        session.stage(kind="block", name=name, at=dims["at"], w=dims["w"], d=dims["d"],
                      h=dims["h"],
                      why=(f"a {'top' if bplan else 'front'}-view rectangle {m(dims['w']):.1f} × "
                           f"{m(dims['d'] if bplan else dims['h']):.1f} m on the sketch"
                           + (f", stamped {label}" if label else ", nothing stamped in it")),
                      confidence=frame.confidence)
        await asyncio.sleep(BEAT)

    # ---- 2 · THE KIT ------------------------------------------------------
    devices = [s for s in sketch.stamps
               if s.label.upper() in STAMP_REQ and id(s) not in claimed]
    counts: dict[str, int] = dict(counts_pre)
    defaulted_models = False
    for stamp in devices:
        rk = STAMP_REQ[stamp.label.upper()]
        counts[rk] = counts.get(rk, 0) + 1
        model, declared_model = _pick_model(session, rk, stamp.note)
        defaulted_models = defaulted_models or not declared_model
        handle = f"{rk}{counts[rk]}"
        # in a FRONT view the anchor's own height IS the height; in plan the page
        # cannot say, so a rail height is assumed and said to be assumed
        sv = stamp.view or "plan"
        if sv != "elevation":
            at = frame.take(stamp.at[0], stamp.at[1], STUB_HEIGHT_M.get(rk, 0.0), view=sv)
            hnote = f"flown at {STUB_HEIGHT_M.get(rk, 0):.1f} m — a top view cannot say"
        else:
            at = frame.take(stamp.at[0], stamp.at[1], view=sv)
            hnote = f"at {m(at[1]):.1f} m, read off the front view"
        session.note(f"{stamp.label} {counts[rk]} → {m(at[0]):.1f}, {m(at[1]):.1f}, {m(at[2]):.1f} m · {hnote}.\n")
        session.stage(kind="add", req=rk, model=model, at=at, objId=handle,
                      why=f"the {_ordinal(counts[rk])} {stamp.label} anchor, {hnote}"
                          + (f" — note: {stamp.note}" if stamp.note else ""),
                      confidence=frame.confidence)
        target = _aim_target(stamp, frame, sv != "elevation")
        if target:
            session.stage(kind="aim", objId=handle, at=target,
                          why=f"the direction dragged out of the anchor, at "
                              f"{m(target[0]):.1f}, {m(target[1]):.1f}, {m(target[2]):.1f} m",
                          confidence="declared")
        await asyncio.sleep(BEAT)

    if defaulted_models and devices:
        session.risk("kit is the first catalogue row — this reader places and sizes, "
                     "it does not choose models")
    if not boxes and not devices:
        # v5.5 · TRACED SOLIDS ARE NOT NOTHING. A drawing of a curved thrust and a
        # curved LED wall has no rectangles and no anchors, and this branch used to
        # answer it with "nothing placed" while two solids sat in the plan above.
        if sketch.solids:
            roles = [x.role for x in sketch.solids]
            lead = "wall" if "led" in roles or "wall" in roles else "block"
            session.note("The drawing is geometry rather than kit — the shapes are the "
                         "proposal, and nothing has been placed on them yet.\n")
            session.declare_intent(lead, 0.55,
                                   f"{_n(len(sketch.solids), 'traced outline')} and no kit yet")
            session.finish(
                _n(len(sketch.solids), "fitted solid") + " built from the trace — "
                + ", ".join(f"{(x.name or x.role).lower()} at "
                            f"{len(x.verts)} vertices"
                            + (f" with {sum(1 for b in x.bulges if b)} arc(s)"
                               if any(x.bulges) else "")
                            for x in sketch.solids[:3]) + ".",
                0.7)
            return
        session.note("Nothing placeable: no rectangles and no anchors.")
        session.stage(kind="note", why="the drawing has nothing this reader can size or place",
                      confidence="guessed", text="Sketch read, nothing placed.")
        session.declare_intent("block", 0.3, "a drawing with nothing in it is still about the space")
        session.finish("Read the sketch; nothing placeable in it.", 0.25)
        return

    # ---- 3 · WHAT IT ADDS UP TO -------------------------------------------
    if "projectors" in counts:
        session.note("Asking the Scene Study what these cover… ")
        answer = await session.ask("measure_preview", {"want": ["throwDistances", "overlap"]})
        if answer.get("unavailable"):
            session.note("no answer — coverage is unavailable, not estimated.\n")
        else:
            throw = ((answer.get("derived") or {}).get("throwDistances") or {}).get("text")
            session.note(f"back: {throw or 'measured'}.\n")

    lead = max(counts, key=lambda k: counts[k]) if counts else None
    intent = REQ_INTENT.get(lead, "block")
    add = ["measure"] if counts.get("projectors") else []
    session.declare_intent(intent, 0.75 if frame.basis == "declared" else 0.6,
                           f"{sum(counts.values())} anchors" + (f", mostly {lead}" if lead else "")
                           + f" and {_n(len(boxes), 'drawn rectangle')}",
                           add=add,
                           reason="throw distances are the live question" if add else "")

    # Counted off the OPS, not off the drawing. A rectangle with a stamp in it became
    # that device rather than a block, so counting rectangles said "2 rectangles and 2
    # devices" for two objects — which reads as the double placement this reader was
    # just fixed not to do. The plan is the record; count that.
    kinds: dict[str, int] = {}
    for o in session.ops:
        kinds[o.kind] = kinds.get(o.kind, 0) + 1
    parts = []
    if kinds.get("add"):
        parts.append(_n(kinds["add"], "object"))
    if kinds.get("block"):
        parts.append(_n(kinds["block"], "block"))
    if kinds.get("solid"):
        parts.append(_n(kinds["solid"], "fitted solid"))
    if kinds.get("audience"):
        parts.append("a crowd")
    if kinds.get("aim"):
        parts.append(_n(kinds["aim"], "aim"))
    session.finish(
        (" · ".join(parts) or "nothing placeable")
        + f", read off a {'top' if plan else 'front'} view at "
        + ("the drawn scale" if frame.basis == "declared" else "1 m per square") + ".",
        0.8 if frame.basis == "declared" else 0.65)


def _pick_model(session: Session, req_key: str, note: str) -> tuple[str | None, bool]:
    """A stamp whose note names a catalogue row gets that row — that is a
    declared choice. Otherwise the first row, and the plan says it defaulted."""
    rows = session.req.catalogues.get(req_key) or []
    names = [r.get("name") for r in rows if isinstance(r, dict) and r.get("name")]
    if note:
        up = note.upper()
        for n in names:
            if n.upper() in up or up in n.upper():
                return n, True
    return (names[0] if names else None), False


def _n(count: int, noun: str) -> str:
    return f"{count} {noun}" + ("" if count == 1 else "s")


def _ordinal(n: int) -> str:
    return {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth"}.get(n, f"{n}th")


# -------------------------------------------------------------- references --
async def _refs(session: Session) -> None:
    """v5.5 · READ THE PICTURE. `vision.py` traces the drawing and arbitrates what each
    shape is; this turns the result into ops. See VISION.md.

    Nothing here interprets pixels itself, and nothing here converts a unit: the tracer
    measures, `geometry.Frame` converts, and this function is the part that speaks the
    take's vocabulary. Same division as everywhere else in this service.
    """
    req = session.req
    U = req.unitsPerMetre
    m = lambda u: u / U
    names = ", ".join(i.name for i in req.images)
    session.note(f"{_n(len(req.images), 'reference')} received — {names}. ")
    await asyncio.sleep(BEAT)

    if vision is None or not vision.traceable():
        why = vision.why() if vision is not None else "vision.py is not present"
        session.note(f"But nothing can be traced from them: {why}.\n")
        for img in req.images:
            session.stage(kind="note", confidence="declared",
                          why=f"{img.name} declared as {img.role}",
                          text=f"{img.name} · {img.role}" + (f" · {img.note}" if img.note else ""))
        session.risk(f"reference images were not read — {why}")
        session.declare_intent("block", 0.2, "references were dropped, nothing traced")
        session.finish(f"Logged {_n(len(req.images), 'reference')}. Nothing traced.", 0.1,
                       [why])
        return

    session.note(f"Reading them with {vision.MODEL.split('/')[-1]} over a deterministic "
                 f"tracer — the model says what each shape IS, the tracer measures it.\n")
    made = 0
    solids = 0
    for n_img, img in enumerate(req.images, 1):
        try:
            data = base64.b64decode(img.b64)
        except Exception:
            session.note(f"{img.name} could not be decoded.\n")
            continue
        if img.role == "mood":
            # A MOOD SHOT CARRIES INTENT, NOT DIMENSIONS. Tracing one produces confident
            # geometry from a photograph of a nightclub, which is the worst possible
            # output: measured-looking and meaningless.
            session.note(f"{img.name} is tagged a mood reference, so it is read for "
                         f"intent and not for geometry.\n")
            session.stage(kind="note", confidence="declared",
                          why=f"{img.name} is a mood reference — no geometry taken from it",
                          text=f"mood · {img.name}" + (f" · {img.note}" if img.note else ""))
            continue

        read = vision.read(data, hint_role=img.role)
        if read is None or not read.regions:
            for nt in (read.notes if read else ["nothing traced"]):
                session.note(f"{img.name}: {nt}.\n")
            continue
        measurements = vision.measurement_labels(data, read.ocr_rows)
        if measurements:
            shown = ", ".join(f"{x['text']} ({round(x['confidence'] * 100)}%)" for x in measurements[:6])
            session.note(f"  measurement OCR found {shown}. These labels are shown for confirmation; "
                         f"they are not silently treated as the drawing width.\n")
            session.stage(kind="note", confidence="guessed",
                          why="measurement OCR needs confirmation before it can set scene scale",
                          text="CONFIRM SCALE · " + shown)
            session.risk("written measurements were read locally, but a label may describe an object "
                         "rather than the whole room — confirm which dimension sets the drawing scale")
        frame = geometry.frame_for_image(read.size[0], read.size[1], read.projection,
                                        req.venue, U, req.derived)
        session.thinking(f"{img.name}: {len(read.regions)} shapes traced, "
                         f"{read.projection}, scale {frame.basis}. ")
        for nt in read.notes:
            session.note(f"  {nt}.\n")
        session.risk(frame.note)
        await asyncio.sleep(BEAT)

        for idx, reg in enumerate(read.regions, 1):
            sol = vision.to_solid(reg, frame, read.size[0], read.size[1],
                                  read.projection, U, n_img * 100 + idx)
            if not sol:
                continue
            long_m = sol["fit"]["long_m"]
            # A CROWD IS NOT A SHAPE, it is a region full of people — the take has its
            # own store for that and the tool draws silhouettes rather than a prism.
            if reg.role == "audience":
                session.note(f"  a seating block {long_m:.1f} m across, downstage — "
                             f"read as the audience.\n")
                session.stage(kind="audience", at=sol["at"],
                              w=round(reg.w / frame.px_per_metre * U, 1),
                              d=round(reg.h / frame.px_per_metre * U, 1),
                              why=f"a wide shape at the foot of {img.name}, which is where "
                                  f"the audience is on a plan",
                              confidence=frame.confidence)
                made += 1
                continue
            arcs = sol["fit"]["arcs"]
            dispute = (f" — the model read it as {reg.model_says} instead"
                       if reg.role_from == "layout·disputed" and reg.model_says else "")
            area = (sol.get("metrics") or {}).get("area")
            session.note(f"  {reg.role.upper()} · {long_m:.1f} m across"
                         + (f" · {area:.1f} m²" if area else "")
                         + f" · {sol['fit']['raw']} traced points fitted to {len(sol['verts'])} "
                         f"vertices" + (f" and {_n(arcs, 'arc')}" if arcs else " and no curvature")
                         + f"{dispute}.\n")
            if dispute:
                session.risk(f"{img.name}: the vision model called that {reg.role} shape a "
                             f"{'an' if reg.model_says[0] in 'aeiou' else 'a'} "
                             f"{reg.model_says} — the layout decided; change the role on the "
                             f"shape if it was right")
            session.stage(kind="solid", **{k: v for k, v in sol.items() if k != "fit"},
                          fit=sol["fit"],
                          why=(f"traced from {img.name}: {sol['fit']['raw']} points fitted to "
                               f"{len(sol['verts'])} vertices"
                               + (f" and {_n(arcs, 'true arc')}" if arcs else "")
                               + f", role from the {reg.role_from.replace('·disputed','')}"),
                          # THE GEOMETRY IS MEASURED; THE SCALE IS NOT. A photograph
                          # carries no scale, so `fitted` at best — never `declared`.
                          confidence=frame.confidence)
            solids += 1
            made += 1
            await asyncio.sleep(BEAT)

        # Semantic text is evidence about a nearby object, not a declaration. Keep it
        # as its own proposed op so the ordinary plan review can accept/reject/edit it;
        # `reviewActions` also tells richer clients that reassignment is supported.
        for suggestion in read.suggestions:
            local_idx = suggestion.get("targetIndex")
            target_id = (f"ref{n_img * 100 + int(local_idx)}" if local_idx else None)
            pct = round(float(suggestion.get("confidence", 0)) * 100)
            session.note(f"  OCR suggestion · {suggestion['label']} → "
                         f"{suggestion['role']} ({pct}%), awaiting confirmation.\n")
            session.stage(kind="note", confidence="guessed",
                          why=(f"local OCR read {suggestion['text']} at {pct}% and associated "
                               "it with the nearest traced object; confirm before stamping"),
                          text=f"SUGGESTED {suggestion['label']} → {suggestion['role']}",
                          objId=target_id, semanticSuggestion=True,
                          suggestionStatus="proposed", suggestionSource="ocr",
                          suggestionConfidence=suggestion.get("confidence", 0),
                          proposedLabel=suggestion["label"],
                          proposedRole=suggestion["role"],
                          reviewActions=["accept", "edit", "reassign", "reject"])

    if not made:
        session.declare_intent("block", 0.3, "references traced, nothing placeable in them")
        session.finish("Read the references; no shapes came out of them.", 0.2)
        return
    lead = "wall" if any(o.kind == "solid" and getattr(o, "role", "") in ("led", "wall")
                         for o in session.ops) else "block"
    session.declare_intent(lead, 0.5,
                           f"{_n(solids, 'shape')} traced off {_n(len(req.images), 'reference')}")
    session.finish(f"{_n(solids, 'shape')} traced from "
                   f"{_n(len(req.images), 'reference image')} and built to the fitted scale.",
                   0.5 if solids else 0.2)


# ------------------------------------------------------------------ refine --
async def refine(session: Session, message: str) -> None:
    session.note(f"Noted: “{message}”. ")
    await asyncio.sleep(BEAT)
    session.note("The stub cannot revise a plan — it has no model of what you "
                 "meant. It records the correction so the real agent gets it as "
                 "conversation.")
    session.messages.append({"role": "user", "content": message})
    session.stage(kind="note", confidence="declared",
                  why="a correction from the plan panel",
                  text=f"correction: {message}")
    session.finish(session.summary or "Correction recorded.",
                   session.confidence, ["the stub does not revise plans"])
