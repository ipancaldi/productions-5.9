"""AID3N answering from a model ON THIS MACHINE — the `local` engine.

    MODEL = "SmolVLM2-256M-Instruct" (local snapshot; see vision.py)

WHY THIS EXISTS
---------------
Until now AID3N had three engines and only two of them could think: `claude` needs a
credential this machine does not have, `external` needs somebody to attach an agent, and
`mock` is a deterministic reader that calls no model at all. So the panel read
**"AID3N · no model"**, which was true and useless: there IS a model on this machine.

This engine is the fourth: the local VLM is consulted on **every** call — a sketch or a
reference — and the panel names it. It sits above `mock` in the order and below `claude`,
    because a 256M local model and a frontier one are not substitutes.

WHAT IT DOES AND DOES NOT DO — read this before extending it
------------------------------------------------------------
It is the same split as everywhere else in this service, and it is the reason the
numbers can be trusted: **judgement in the model, arithmetic in Python.**

  · Every position, size, vertex and arc comes from the deterministic reader — the
    Sketch Pad's own fit for a sketch, `vision.py`'s tracer for a reference. Not one
    coordinate in a plan produced here was written by a language model.

  · The model is asked what things ARE, and only where that is genuinely open. A stamped
    shape is a DECLARATION and is never second-guessed; an unstamped one is a question,
    and that is where the model gets a vote.

  · The vote is CALIBRATED first, on ground truth the reader already knows, and the
    policy on what a calibrated vote may overrule lives in `vision.py`
    (`VISION_TRUST_ROLES`, off by default because it was measured off). See VISION.md.

  · Everything it decided, failed to decide, or was overruled on is in the narration and
    the risks. A local model that quietly disagreed with the geometry would be worse than
    no model at all.

REFINE is deliberately deterministic. A small local model asked to revise a plan produces
fluent noise, and a plan is a thing somebody is about to apply to their production. The
correction is recorded for whichever engine answers next, and the panel says so.
"""
from __future__ import annotations

import asyncio
import base64
import io

import stub
from session import Session

try:
    import vision
except Exception:                                            # pragma: no cover
    vision = None

BEAT = 0.14


def available() -> bool:
    return vision is not None and vision.available()


def why() -> str:
    if vision is None:
        return "vision.py is not present"
    return vision.why()


def short_model() -> str:
    """What the panel puts in its header. The family and the size, which is the part
    somebody reading a plan needs — the org and the task suffix are not."""
    name = ((vision._lmstudio_model() if getattr(vision, "BACKEND", "") == "lmstudio"
             else vision.MODEL_NAME) if vision else "")
    return name.replace("-Video-Instruct", "").replace("-Instruct", "") or "local model"


# ============================================================================
# THE SKETCH — the pad measured it; the model is asked about what it did not say
# ============================================================================
_ROLE_Q = {
    "stage": "In a stage plan, is this shape the stage platform the performers stand on, "
             "or the seating area for the audience? Answer one word: stage or seating.",
    "wall":  "In a stage plan, is this a wall or screen the performers stand in front of, "
             "or the floor they stand on? Answer one word: wall or floor.",
    "led":   "In a stage plan, is this long thin rectangle a video screen at the back of "
             "the stage, or a row of seats? Answer one word: screen or seats.",
}


async def _look_at_sketch(session: Session) -> None:
    """Ask the model about the drawing the pad rasterised for exactly this purpose.

    THE PNG IS ALREADY IN THE PAYLOAD. The pad has always sent the raster beside the
    vector record — *"the image is what the model looks at; the vectors are what make its
    answers snap to what was drawn"* — and until there was a model on the machine nothing
    ever opened it. This does.
    """
    sk = session.req.sketch
    if not sk:
        return
    if not sk.png_b64:
        # SAY SO. The pad always sends a raster; something that does not is a client this
        # engine cannot use its model on, and silence there looks like the model having
        # read the drawing and had no opinion.
        session.note(f"{short_model()} had nothing to look at — this payload carried no "
                     f"raster, so only the vectors were read.\n")
        return
    if vision is None or not vision.available():
        return
    try:
        data = base64.b64decode(sk.png_b64)
        img, _ = vision._load(data)                       # noqa: SLF001 — same package
        pil = vision.Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as exc:
        session.note(f"the drawing could not be opened for the model ({type(exc).__name__}).\n")
        return

    H, W = img.shape
    px_w = float((sk.canvas or {}).get("w") or W)
    px_h = float((sk.canvas or {}).get("h") or H)
    kx, ky = W / max(1.0, px_w), H / max(1.0, px_h)

    undeclared = [s for s in (sk.solids or []) if getattr(s, "roleFrom", "") != "stamp"]
    if not undeclared:
        session.note(f"{short_model()} looked at the drawing: every shape in it is "
                     f"stamped, so there is nothing for it to guess about.\n")
        return

    session.note(f"{short_model()} is looking at {stub._n(len(undeclared), 'unstamped shape')} "
                 f"— the stamped ones said what they were.\n")

    # ---- crop each shape out of the raster the pad sent ----
    crops: list[tuple[object, object]] = []
    for s in undeclared:
        xs = [v[0] for v in (s.verts or [])]
        ys = [v[1] for v in (s.verts or [])]
        if not xs:
            continue
        # verts are TAKE UNITS local to `at`; back to canvas pixels for the crop
        u = float(session.req.unitsPerMetre or 10)
        ppm = (sk.scale.pxPerMetre if (sk.scale and sk.scale.pxPerMetre) else 40.0)
        k = ppm / u
        cx = (s.at[0] * k + (sk.origin[0] if sk.origin else px_w / 2)) * kx
        own_view = getattr(s, "view", None) or sk.projection
        if own_view == "elevation" or getattr(s, "plane", None) == "front":
            ground = (sk.groundLine_elevation if sk.groundLine_elevation is not None
                      else (sk.groundLine if sk.groundLine is not None else px_h * 0.78))
            cy = (ground - (s.at[1] if len(s.at) > 1 else 0) * k) * ky
        else:
            cy = ((s.at[2] if len(s.at) > 2 else 0) * k
                  + (sk.origin_y if sk.origin_y is not None
                     else (sk.origin[1] if sk.origin else px_h / 2))) * ky
        w = (max(xs) - min(xs)) * k * kx
        h = (max(ys) - min(ys)) * k * ky
        pad = max(10.0, 0.14 * max(w, h))
        box = (max(0, int(cx - w / 2 - pad)), max(0, int(cy - h / 2 - pad)),
               min(pil.size[0], int(cx + w / 2 + pad)), min(pil.size[1], int(cy + h / 2 + pad)))
        crop = pil.crop(box) if (box[2] - box[0] > 8 and box[3] - box[1] > 8) else pil
        crops.append((s, crop))
    if not crops:
        return

    # ---- calibrate, then ask. Same policy as a reference; see VISION.md § 4 ----
    truth = [(max(1e-6, abs(max(v[0] for v in s.verts) - min(v[0] for v in s.verts)))
              / max(1e-6, abs(max(v[1] for v in s.verts) - min(v[1] for v in s.verts)))) > 3.4
             or (max(1e-6, abs(max(v[1] for v in s.verts) - min(v[1] for v in s.verts)))
                 / max(1e-6, abs(max(v[0] for v in s.verts) - min(v[0] for v in s.verts)))) > 3.4
             for s, _ in crops]
    cal = None
    if len(set(truth)) > 1:
        ok = 0
        for (s, crop), t in zip(crops, truth):
            a = vision.ask(crop, vision.CAL_Q).lower()
            said = True if "strip" in a else (False if "block" in a else None)
            if said is not None and said == t:
                ok += 1
        cal = ok / len(crops)
        session.note(f"  calibration: {ok} of {len(crops)} shapes placed correctly as strip "
                     f"or block, so it {'is' if cal >= 0.75 else 'is not reliably'} reading "
                     f"the drawing.\n")
    else:
        session.note("  no calibration possible — the unstamped shapes all have the same "
                     "proportions.\n")
    await asyncio.sleep(BEAT)

    agreed = disputed = 0
    for s, crop in crops:
        role = getattr(s, "role", "stage")
        question = _ROLE_Q.get(role, _ROLE_Q["stage"])
        own_view = getattr(s, "view", None) or sk.projection
        if own_view == "elevation":
            question = question.replace("In a stage plan", "In a front-facing stage elevation")
        raw = vision.ask(crop, question)
        said = vision._pick(raw, vision._ANSWER_WORDS)      # noqa: SLF001
        name = getattr(s, "name", None) or role
        if not said:
            session.note(f"  {name}: no usable answer.\n")
            continue
        if said == role:
            agreed += 1
            session.note(f"  {name}: the model agrees it is a {role}.\n")
            continue
        disputed += 1
        # THE GEOMETRY STILL DECIDES unless the policy says otherwise — and the policy
        # lives in vision.py so there is one place to argue with it.
        if vision.TRUST_MODEL_ROLES and cal is not None and cal >= 0.75:
            session.note(f"  {name}: the model calls it {said}, and it earned the call — "
                         f"changing it.\n")
            session.stage(kind="note", confidence="guessed",
                          why=f"{short_model()} read the unstamped {role} as a {said}",
                          text=f"{name} may be a {said}, not a {role}")
        else:
            session.note(f"  {name}: the model calls it {said}; the drawing said {role}, "
                         f"and the drawing wins.\n")
            art = 'an' if said[0] in 'aeiou' else 'a'
            session.risk(f"{short_model()} read the unstamped shape “{name}” as {art} {said} "
                         f"rather than a {role} — stamp it if the model was right")
        await asyncio.sleep(BEAT)
    if agreed and not disputed:
        session.note(f"  {short_model()} agreed with the drawing on all of it.\n")


async def run(session: Session) -> None:
    """A sketch, or references. Both go through the deterministic reader; the model is
    consulted on the way past."""
    req = session.req
    if not available():
        session.note(f"The local model is not usable ({why()}). Falling back to the "
                     f"deterministic reader.\n")
        return await stub.run(session)

    if req.sketch and (req.sketch.stamps or req.sketch.strokes or req.sketch.solids):
        # the model first: it is commenting on the drawing, not on the plan
        await _look_at_sketch(session)
        return await stub.run(session)
    # references: vision.py IS the model path, and stub._refs already drives it
    return await stub.run(session)


async def refine(session: Session, message: str) -> None:
    """Deterministic on purpose — see the module docstring."""
    session.note(f"Noted: “{message}”. ")
    await asyncio.sleep(BEAT)
    session.note(f"{short_model()} reads pictures; it does not revise plans — a model this "
                 f"size asked to rewrite a proposal produces fluent noise, and a plan is "
                 f"about to be applied to somebody's production. The correction is recorded "
                 f"for whichever engine answers next.\n")
    session.messages.append({"role": "user", "content": message})
    session.stage(kind="note", confidence="declared",
                  why="a correction from the plan panel",
                  text=f"correction: {message}")
    session.finish(session.summary or "Correction recorded.", session.confidence,
                   [f"{short_model()} does not revise plans"])
