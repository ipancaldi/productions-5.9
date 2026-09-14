"""AID3N, driven from outside — the external agent channel.

The credential problem has an obvious way round it: something with model access is
already in the room. Claude Code can look at the drawing, reason about it, and post
the plan in over HTTP. So a plan can be PARKED here instead of being answered
locally: the sketch is written to `inbox/` as a real PNG somebody can open, the
stream stays live, and an outside agent stages the ops through
`/v1/plan/{id}/op` — the same ops, the same events, the same review.

That makes the API what it should have been all along: a plan is something you
DRIVE, and the local model is one driver among others. Three engines, one
protocol:

    claude    · agent.py, the model called from inside this service
    external  · this file, an agent outside it — Claude Code, for one
    mock      · stub.py, deterministic, no model at all

Nothing about the host or the panels changes between them, which is the test that
the boundary was drawn in the right place.
"""
from __future__ import annotations

import asyncio
import base64
import json
import time
from pathlib import Path
from typing import Any

from geometry import frame_for
from session import Session

INBOX = Path(__file__).resolve().parent / "inbox"
PARK_TIMEOUT_S = 900.0          # fifteen minutes; a human-paced agent is not fast

# An external agent announces itself and stays announced for this long. That is
# what flips the engine: if something is listening, it answers; if not, the stub
# does, and the panel says which.
ATTACH_TTL_S = 300.0
ATTACHED: dict[str, Any] = {"name": None, "until": 0.0}


def attach(name: str) -> dict[str, Any]:
    ATTACHED["name"] = name or "external agent"
    ATTACHED["until"] = time.monotonic() + ATTACH_TTL_S
    return {"name": ATTACHED["name"], "ttl": ATTACH_TTL_S}


def attached() -> bool:
    return bool(ATTACHED["name"]) and time.monotonic() < ATTACHED["until"]


def touch() -> None:
    """Any inbox read counts as still listening — but only while STILL attached.

    It used to refresh on the name alone, which meant a poll from a long-dead agent
    silently resurrected it and changed who answers as AID3N: a plan parked and
    waited for something that had stopped listening minutes ago. An expired
    attachment has to be renewed deliberately, on `/v1/attach`.
    """
    if attached():
        ATTACHED["until"] = time.monotonic() + ATTACH_TTL_S


def detach() -> str | None:
    """Hand back. Any parked plan is left to time out on its own — killing them here
    would be the one thing an external agent must not be able to do to a take."""
    was = ATTACHED["name"]
    ATTACHED["name"] = None
    ATTACHED["until"] = 0.0
    return was


# ============================================================================
# THE BRIEF — the same facts the local model gets, as files on disk
# ============================================================================
def _decimate(pts: list, keep: int = 12) -> list:
    if len(pts) <= keep:
        return pts
    step = (len(pts) - 1) / (keep - 1)
    return [pts[min(len(pts) - 1, round(i * step))] for i in range(keep)]


def brief_dict(session: Session) -> dict[str, Any]:
    """Everything an interpreter needs except the pictures.

    The arithmetic is done HERE, deliberately: anchors arrive already converted to
    take units by the same code the tool uses, so an interpreter spends its effort
    on judgement rather than on unit conversion — the one thing a model is worst at
    and Python is perfect at.
    """
    req = session.req
    out: dict[str, Any] = {
        "planId": session.id,
        "takeId": req.takeId,
        "units_per_metre": req.unitsPerMetre,
        # THE ROOM IS NAMED Z-UP and the wire is not. Both are spelled out because
        # mixing them is the one mistake that puts a projector in the floor.
        "frames": {
            "wire_order": "at = [across, UP, DEPTH] — that is how the take stores it",
            "X": "across the room; positive is stage right to left. FIRST number.",
            "Z": "UP. Flown kit is positive. SECOND number. Green on screen.",
            "Y": "into the room; positive is downstage toward the audience, upstage is "
                 "negative. THIRD number. Blue on screen.",
        },
        "venue": req.venue.model_dump(exclude_none=True) if req.venue else None,
        "checklist": req.checklist.model_dump(),
        "scene": {"devices": (req.scene or {}).get("devices", []),
                  "tracks": (req.scene or {}).get("tracks", []),
                  "audience": (req.scene or {}).get("audience", [])},
        "derived": {k: (v or {}).get("text") if isinstance(v, dict) else v
                    for k, v in (req.derived or {}).items()},
        "catalogues": req.catalogues,
    }
    if req.sketch:
        sk = req.sketch
        frame = frame_for(sk, req.venue, req.unitsPerMetre, req.derived)
        out["sketch"] = {
            "projection": sk.projection,
            "coordinate_contract": (
                "AUTHORITATIVE PLAN — top-down: page x = room X across; page y down = room Y depth/downstage; "
                "Z/height is not visible and must not be inferred from page y."
                if sk.projection == "plan" else
                "AUTHORITATIVE ELEVATION — front-facing: page x = room X across; page y up from groundLine = room Z height; "
                "Y/depth is not visible and must not be inferred from page y."
            ),
            "canvas": sk.canvas,
            "scale": {"basis": frame.basis, "px_per_metre": round(frame.px_per_metre, 2),
                      "note": frame.note},
            "anchors": [{"label": s.label, "note": s.note, "view": s.view,
                         "at_px": s.at,
                         "at_take": frame.take(s.at[0], s.at[1], view=s.view)} for s in sk.stamps],
            "labels": [{"text": l.text, "view": l.view, "at_px": l.at,
                        "at_take": frame.take(l.at[0], l.at[1], view=l.view)} for l in sk.labels],
            "strokes": [{"kind": s.kind, "view": s.view,
                          "pts_px": _decimate(s.pts)} for s in sk.strokes[:60]],
            "strokes_dropped": max(0, len(sk.strokes) - 60),
            "note_from_user": sk.note,
            # v5.5 · THE FITTED OUTLINES, verbatim and already in take units. This is
            # the one part of the sketch that arrives converted, because the pad is
            # what fitted it — see model.Solid. `fit` says what the correction cost,
            # so an interpreter can report the precision it was actually handed rather
            # than the precision the numbers look like.
            "solids": [s.model_dump(exclude_none=True) for s in sk.solids],
            # the two corners of every drawn box, already converted — a rectangle is
            # how people draw a stage, a wall or a seating block
            "boxes_take": [
                {"kind": s.kind, "view": s.view,
                 "a": frame.take(min(s.pts[0][0], s.pts[1][0]), min(s.pts[0][1], s.pts[1][1]), view=s.view),
                 "b": frame.take(max(s.pts[0][0], s.pts[1][0]), max(s.pts[0][1], s.pts[1][1]), view=s.view)}
                for s in sk.strokes if s.kind in ("rect", "ellipse") and len(s.pts) >= 2
            ],
        }
    if req.images:
        out["references"] = [{"n": i, "name": im.name, "role": im.role, "note": im.note}
                             for i, im in enumerate(req.images, 1)]
    return out


def write_inbox(session: Session) -> dict[str, Any]:
    """The drawing as a file. An agent outside this process cannot be handed a
    base64 string in a stream it is not reading — it needs something to open."""
    INBOX.mkdir(parents=True, exist_ok=True)
    files: list[str] = []
    req = session.req
    if req.sketch and req.sketch.png_b64:
        f = INBOX / f"{session.id}-sketch.png"
        f.write_bytes(base64.b64decode(req.sketch.png_b64))
        files.append(str(f))
    for i, im in enumerate(req.images, 1):
        ext = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(im.mime, "png")
        f = INBOX / f"{session.id}-ref{i}.{ext}"
        f.write_bytes(base64.b64decode(im.b64))
        files.append(str(f))
    brief = brief_dict(session)
    bf = INBOX / f"{session.id}.json"
    bf.write_text(json.dumps(brief, indent=1, default=str))
    return {"planId": session.id, "brief": str(bf), "images": files,
            "kind": "sketch" if req.sketch else "refs"}


# ============================================================================
# THE TWO ENTRY POINTS — the same signature as the stub and the local agent
# ============================================================================
PARKED: dict[str, dict[str, Any]] = {}          # planId -> what the inbox holds


async def run(session: Session) -> None:
    entry = write_inbox(session)
    entry["at"] = time.time()
    PARKED[session.id] = entry
    who = ATTACHED["name"] or "an external agent"
    session.note(f"Parked for {who}. The drawing is on disk and the plan is open — "
                 "ops will appear here as they are staged.\n")
    session.emit("waiting", entry)
    held = await session.park(PARK_TIMEOUT_S)
    PARKED.pop(session.id, None)
    if held:
        return                                   # `finish` was posted; it closed the plan
    if session.ops:
        session.finish(f"{len(session.ops)} staged before the agent stopped answering.",
                       0.3, [f"{who} never called finish — the plan is partial"])
    else:
        session.fail("external_timeout",
                     f"{who} did not answer in {int(PARK_TIMEOUT_S)}s")


async def refine(session: Session, message: str) -> None:
    entry = PARKED.get(session.id) or write_inbox(session)
    entry["correction"] = message
    entry["at"] = time.time()
    PARKED[session.id] = entry
    session.note(f"Correction parked: “{message}”\n")
    session.emit("waiting", entry)
    held = await session.park(PARK_TIMEOUT_S)
    PARKED.pop(session.id, None)
    if not held:
        session.finish(session.summary or "No revision.", session.confidence,
                       ["the external agent did not answer the correction"])
