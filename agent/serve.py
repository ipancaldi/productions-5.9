"""The Studio Agent API — 127.0.0.1:3902.

The host's only counterpart. It holds no take, writes nothing, and talks to
nobody but the model: a function of (scene snapshot + images + conversation) → a
plan. The contract is `../AGENT-BRIDGE.md`.

Run:
    5.9/agent/.venv/bin/python -m uvicorn serve:app --host 127.0.0.1 --port 3902 \
        --app-dir 5.9/agent --reload

Which interpreter answers is decided in `interpreter()` below and reported by
`/health`: the real agent when a credential exists, and the deterministic stub
otherwise — or always, with `AGENT_STUB=1`. The stub is not a fallback nobody
wants; it is how the panels get designed without spending a token.
"""
from __future__ import annotations

import asyncio
import base64
import os
import time
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

import external

# v5.5 · the reference reader. Optional in exactly the way agent.py is: no torch on the
# machine means no picture can be read, and that is a NAMED state on /health rather than
# a service that will not start.
try:
    import vision
except Exception:                                            # pragma: no cover
    vision = None
try:
    import local
except Exception:                                            # pragma: no cover
    local = None
# v5.9.3 · AID3N drawing content for a wall. Optional in the same way vision.py is:
# no model server on the machine is a NAMED state on /health, not a service that
# will not start. See imagegen.py — and read its first paragraph before assuming
# this is a diffusion model, because it is not one.
try:
    import imagegen
except Exception:                                            # pragma: no cover
    imagegen = None
import stub
from model import (AGENT_V, AcceptedRequest, AnswerRequest, InterpretRequest,
                   RefineRequest)
from session import STORE, Session, keep

AGENT_NAME = "AID3N"
MODEL = "claude-opus-5"

try:
    import agent                        # type: ignore
except ModuleNotFoundError:
    agent = None


def engine():
    """WHO ANSWERS AS AID3N. Three engines, one protocol — nothing about the host or
    the panels changes between them, which is the test that the boundary was drawn
    in the right place.

        claude    a frontier model, called from inside this service
        external  an agent outside it — Claude Code, for one — driving the plan over
                  `/v1/plan/{id}/*`. This is what lets a machine with no credential
                  still interpret a drawing.
        local     v5.5 · a VLM on THIS MACHINE (SmolVLM2 by default), consulted on every
                  sketch and every reference. It reads pictures; it does not do the
                  arithmetic — see local.py and VISION.md. It sits above `mock` because
                  there genuinely is a model, and below `claude` because a 500M local
                  model and a frontier one are not substitutes.
        mock      stub.py: deterministic, no model, instant, free

    `auto` prefers an attached external agent, because attaching is a deliberate act
    by something that intends to answer. `AGENT_ENGINE` pins one.
    """
    forced = os.environ.get("AGENT_ENGINE", "auto")
    if os.environ.get("AGENT_STUB") == "1":
        forced = "mock"
    if forced == "mock":
        return stub, "mock", "pinned by AGENT_ENGINE=mock"
    if forced == "external":
        return external, "external", (f"pinned · {external.ATTACHED['name']} attached"
                                      if external.attached() else
                                      "pinned, but nothing is attached — plans will park and wait")
    if forced == "local":
        if local and local.available():
            return local, "local", local.why()
        return stub, "mock", f"pinned to local, but {local.why() if local else 'local.py is absent'}"
    if forced == "claude":
        if agent and agent.available():
            return agent, "claude", ""
        return stub, "mock", "pinned to claude, but there is no credential"
    if external.attached():
        return external, "external", f"{external.ATTACHED['name']} is attached"
    if agent and agent.available():
        return agent, "claude", ""
    # v5.5 · there IS a model on this machine. Preferring it over the deterministic
    # reader is the whole point of installing it, and the panel says which one it is
    # rather than the flat "no model" it used to read.
    if local and local.available():
        return local, "local", local.why()
    if agent is None:
        return stub, "mock", "agent.py is not present"
    return stub, "mock", ("no Anthropic credential, no local vision model and no external "
                          "agent attached — set ANTHROPIC_API_KEY, install the vision "
                          "requirements, or attach an agent on /v1/attach")


app = FastAPI(title="Productions v5 · AID3N", version=str(AGENT_V))

# The host is served from :3900. `null` is what a file:// page sends, and it is
# allowed so that opening the prototype by double-click DEGRADES — the panel names
# an offline agent — rather than failing in a way nobody can read.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3900", "http://127.0.0.1:3900", "null"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",          # nothing between us should buffer a stream
}


# ------------------------------------------------------------------- health --
@app.get("/")
def root():
    return Response("Productions v5 · AID3N. See /health.\n", media_type="text/plain")


@app.get("/health")
def health():
    """Polled once when the plan panel mounts. The panel names the offline state
    off a failure here, the way the Scene Study panel names its lost state."""
    mod, which, why = engine()
    # WHICH MODEL IS ANSWERING, not which one this file was written against. The panel
    # puts this in its header, so a local engine has to name the local checkpoint or the
    # header claims a model that is not being called.
    model = MODEL
    if which == "local" and local:
        model = local.short_model()
    elif which == "mock":
        model = None
    return {
        "ok": True, "v": AGENT_V, "name": AGENT_NAME, "model": model,
        "engine": which, "why": why,
        "stub": which == "mock", "interpreter": which,      # the panels' older reading
        "credentials": bool(agent and agent.available()),
        "attached": external.ATTACHED["name"] if external.attached() else None,
        "plans": len(STORE), "parked": list(external.PARKED),
        # v5.5 · CAN A REFERENCE BE READ, and by what. Three states, like the engine:
        #   smolvlm2  the model answers and the tracer measures
        #   tracer    numpy and Pillow are here but torch is not — shapes are still
        #             traced and their roles come from the layout
        #   off       nothing can be read; the panel says so instead of pretending
        "vision": (vision.state() if vision is not None
                   else {"ok": False, "engine": "off", "model": None,
                         "why": "vision.py is not present"}),
    }


# ---------------------------------------------------------------- the stream --
def _sse(session: Session, run):
    """Run an interpreter and drain its session as server-sent events.

    The interpreter is a task, not a generator, because `ask` has to emit an event
    and then wait for `/v1/answer` on a different request — a generator could not
    be in both places at once.
    """
    async def pump():
        eng = engine()[1]
        session.emit("open", {"planId": session.id, "name": AGENT_NAME,
                              "model": MODEL if eng == "claude" else None,
                              "engine": eng, "interpreter": eng, "effort": "xhigh"})
        try:
            await run(session)
        except asyncio.CancelledError:
            raise
        except Exception as e:                      # never a partial apply
            session.fail(type(e).__name__, str(e) or "the interpreter failed")
        finally:
            session.close()

    async def gen():
        task = asyncio.create_task(pump())
        try:
            async for chunk in session.stream():
                yield chunk
        finally:
            # the panel navigated away or hit cancel — stop the work
            if not task.done():
                task.cancel()

    return StreamingResponse(gen(), media_type="text/event-stream", headers=SSE_HEADERS)


@app.post("/v1/interpret")
async def interpret(req: InterpretRequest):
    if req.v != AGENT_V:
        raise HTTPException(400, f"protocol v{req.v}; this service speaks v{AGENT_V}")
    session = keep(Session(req))
    return _sse(session, engine()[0].run)


@app.post("/v1/refine")
async def refine(req: RefineRequest):
    session = STORE.get(req.planId)
    if not session:
        raise HTTPException(404, f"no plan {req.planId} — it may have aged out of the store")
    if not session.closed:
        raise HTTPException(409, f"plan {req.planId} is still streaming")
    session.reopen()
    fn = engine()[0].refine
    return _sse(session, lambda s: fn(s, req.message))


# ------------------------------------------------------- the host answering --
@app.post("/v1/answer")
async def answer(req: AnswerRequest):
    """The host's reply to an `ask`. `measure_preview` is the reason this exists:
    the host ghosts the staged ops into the Scene Study, the tool measures real
    geometry, and the figure comes back here."""
    session = STORE.get(req.planId)
    if not session:
        raise HTTPException(404, f"no plan {req.planId}")
    if not session.answer(req.askId, req.result):
        # not an error worth failing the turn over: the ask has already timed out
        # and the interpreter was told the figure is unavailable.
        return JSONResponse({"ok": False, "reason": "no pending ask, or it timed out"},
                            status_code=202)
    return {"ok": True}


# ------------------------------------------------------------ content for a wall --
@app.post("/v1/image")
async def image(body: dict[str, Any] = Body(...)):
    """Content for an LED wall, from a prompt. A still, or a clip.

    ONE ENDPOINT, TWO SHAPES, chosen by `kind`:

        kind: "image"   Z Image Turbo draws a frame           — seconds
        kind: "video"   Turbo draws frame one, Wan animates it — minutes

    They are the same request otherwise, which is the point: the panel has one prompt
    field, one size, and one Generate button, and the toggle decides how far down the
    pipeline the job travels. `engine` and `kind` come back on every answer so nothing
    downstream has to guess what it was handed.

    Video-only fields, all optional: `motion` (how it should move — falls back to the
    picture's own prompt), `frames`, `fps`, and `keyframe` (base64 PNG). That last one
    is the cheap path: a still the user already generated and liked becomes frame one,
    and the first stage is skipped entirely.

    Synchronous on purpose, still. A still is seconds and a clip is minutes — both are
    too long to hide behind a spinner and too short to be worth a plan store — so the
    panel shows an elapsed clock and can abort, and this stays one request, one answer.
    """
    if imagegen is None:
        raise HTTPException(503, "imagegen is not installed in this service")
    prompt = str(body.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(400, "no prompt")
    try:
        w = max(64, min(15360, int(body.get("w") or 1920)))
        h = max(64, min(8640, int(body.get("h") or 1080)))
    except (TypeError, ValueError):
        raise HTTPException(400, "w and h must be whole numbers of pixels")
    seed = body.get("variant")
    seed = int(seed) if isinstance(seed, (int, float)) else None
    num = lambda k: (float(body[k]) if isinstance(body.get(k), (int, float)) else None)

    kind = str(body.get("kind") or "image").strip().lower()
    if kind not in ("image", "video"):
        raise HTTPException(400, f'kind must be "image" or "video", not "{kind}"')
    motion = str(body.get("motion") or "").strip()
    frames = int(num("frames")) if num("frames") else None
    fps = int(num("fps")) if num("fps") else None
    # A KEYFRAME IS DECODED HERE, not deeper in, so a bad one is a 400 from the
    # endpoint rather than a puzzling failure four minutes into a job.
    keyframe = None
    if body.get("keyframe"):
        raw = str(body["keyframe"])
        if raw.startswith("data:"):
            raw = raw.split(",", 1)[-1]
        try:
            keyframe = base64.b64decode(raw, validate=False)
        except Exception:
            raise HTTPException(400, "keyframe is not base64")
        if keyframe[:8] != b"\x89PNG\r\n\x1a\n":
            raise HTTPException(400, "keyframe must be a PNG")

    # off the event loop: urllib blocks, and a minutes-long block here would stall
    # /health and every plan stream in the service with it
    out = await asyncio.to_thread(
        imagegen.generate, prompt, w, h, seed,
        bool(body.get("refine")), body.get("engine"),
        int(num("steps")) if num("steps") else None, num("cfg"),
        kind, motion, frames, fps, keyframe)
    return JSONResponse(out, status_code=200 if out.get("ok") else 502)


@app.get("/v1/image/health")
async def image_health():
    """What the content panel polls: which engine would run, what every engine's
    state is, and the live configuration. All three, because "it says it is not
    ready" is only actionable if it also says which part is not ready."""
    if imagegen is None:
        return {"ok": False, "why": "imagegen is not installed in this service"}
    st = await asyncio.to_thread(imagegen.engines)     # each probe is a blocking GET
    which, why = imagegen.pick()
    e = st.get(which, {})
    vid = st.get("wan-i2v") or {"ok": False, "why": "the video stage is not installed"}
    return {"ok": which != "none", "engine": which, "chose": why,
            "model": e.get("model"), "why": "" if which != "none" else why,
            "engines": st, "want": imagegen.WANT,
            "refine": promptmod_available(),
            # The panel needs to know whether to OFFER the video toggle, and if it is
            # off, exactly why — "still downloading" and "not installed" ask different
            # things of the person reading it.
            "video": {"ok": bool(vid.get("ok")), "why": vid.get("why", ""),
                      "model": vid.get("model"), "encoder": vid.get("encoder"),
                      "downloading": vid.get("downloading") or [],
                      "config": vid.get("config") or {}},
            "note": ("Z Image Turbo, generated locally by Draw Things"
                     if which == "drawthings" else
                     "SVG written by a language model and rasterised by the panel — "
                     "no diffusion model is answering")}


def promptmod_available() -> dict:
    """Whether step 2 of the pipeline — Qwen expanding the prompt — can run."""
    if imagegen is None or getattr(imagegen, "promptmod", None) is None:
        return {"ok": False, "why": "the prompt module is not installed"}
    m = imagegen.promptmod._model()
    return {"ok": bool(m), "model": m,
            "why": "" if m else "no Qwen model is loaded in LM Studio"}


@app.post("/v1/accepted")
async def accepted(req: AcceptedRequest, response: Response):
    """Nothing is applied here — the host has already done that. This is the
    feedback that makes the second sketch better than the first."""
    session = STORE.get(req.planId)
    if not session:
        raise HTTPException(404, f"no plan {req.planId}")
    session.feedback.append(req.model_dump())
    return Response(status_code=204)


@app.get("/v1/plan/{plan_id}")
async def plan(plan_id: str):
    session = STORE.get(plan_id)
    if not session:
        raise HTTPException(404, f"no plan {plan_id}")
    return session.snapshot()


# ============================================================================
# THE EXTERNAL CHANNEL — AID3N, driven from outside this process.
#
# Everything below is the same plan built by a different hand. The events the host
# receives are identical, which is the point: an agent with model access elsewhere
# on the machine can read the drawing and stage the ops, and the host cannot tell.
# See external.py.
# ============================================================================
@app.post("/v1/attach")
async def attach(body: dict[str, Any] = Body(default={})):
    """Announce an external agent. While one is attached, `auto` routes plans to it."""
    got = external.attach(str(body.get("name") or "external agent"))
    return {"ok": True, "name": got["name"], "ttl": got["ttl"], "engine": engine()[1]}


@app.post("/v1/detach")
async def detach(body: dict[str, Any] = Body(default={})):
    """Hand AID3N back to whichever engine `auto` would otherwise pick."""
    was = external.detach()
    return {"ok": True, "was": was, "engine": engine()[1]}


@app.get("/v1/inbox")
async def inbox():
    """What is parked and waiting. Reading this counts as still listening, so a
    poller stays attached without having to say so again."""
    external.touch()
    now = time.time()
    return {"ok": True,
            "attached": external.ATTACHED["name"] if external.attached() else None,
            "parked": [dict(e, waiting_s=round(now - e.get("at", now), 1))
                       for e in external.PARKED.values()]}


def _open_plan(plan_id: str) -> Session:
    session = STORE.get(plan_id)
    if not session:
        raise HTTPException(404, f"no plan {plan_id}")
    if session.closed:
        raise HTTPException(409, f"plan {plan_id} is closed — its stream has ended")
    external.touch()
    return session


@app.get("/v1/plan/{plan_id}/brief")
async def brief(plan_id: str):
    """The same facts the local model gets, for an agent that would rather read JSON
    over HTTP than off the disk."""
    session = STORE.get(plan_id)
    if not session:
        raise HTTPException(404, f"no plan {plan_id}")
    return external.brief_dict(session)


@app.post("/v1/plan/{plan_id}/note")
async def plan_note(plan_id: str, body: dict[str, Any]):
    """Narration. It streams into the plan panel as AID3N's own voice, so write it
    as notes to a colleague, not as a report."""
    _open_plan(plan_id).note(str(body.get("delta") or ""))
    return {"ok": True}


@app.post("/v1/plan/{plan_id}/op")
async def plan_op(plan_id: str, body: dict[str, Any]):
    """Stage one operation. It reaches the panel and ghosts into the 3D immediately —
    the same event the local model produces, through the same validation."""
    session = _open_plan(plan_id)
    body.pop("id", None)
    try:
        op = session.stage(**body)
    except Exception as e:                     # a malformed op is the caller's problem
        raise HTTPException(400, f"{type(e).__name__}: {e}")
    return {"ok": True, "op": op.model_dump(by_alias=True, exclude_none=True),
            "staged": len(session.ops)}


@app.post("/v1/plan/{plan_id}/ops")
async def plan_ops(plan_id: str, body: dict[str, Any]):
    """The same thing in bulk, because a scene is usually a list."""
    session = _open_plan(plan_id)
    out = []
    for raw in (body.get("ops") or []):
        raw.pop("id", None)
        try:
            out.append(session.stage(**raw).id)
        except Exception as e:
            raise HTTPException(400, f"op {len(out) + 1}: {type(e).__name__}: {e}")
    return {"ok": True, "ids": out, "staged": len(session.ops)}


@app.post("/v1/plan/{plan_id}/intent")
async def plan_intent(plan_id: str, body: dict[str, Any]):
    session = _open_plan(plan_id)
    session.declare_intent(str(body.get("intent") or "block"),
                           float(body.get("confidence") or 0.5),
                           str(body.get("why") or ""),
                           add=list(body.get("add") or []),
                           drop=list(body.get("drop") or []),
                           reason=str(body.get("reason") or ""))
    return {"ok": True}


@app.post("/v1/plan/{plan_id}/measure")
async def plan_measure(plan_id: str):
    """The ghost round-trip, on demand: everything staged so far is drawn as ghosts
    in the Scene Study and measured off real geometry. `{"unavailable": true}` when
    nothing answers — in which case say so and do not estimate."""
    session = _open_plan(plan_id)
    return await session.ask("measure_preview")


@app.post("/v1/plan/{plan_id}/finish")
async def plan_finish(plan_id: str, body: dict[str, Any]):
    """Ends the turn and releases the parked stream."""
    session = _open_plan(plan_id)
    session.finish(str(body.get("summary") or ""), float(body.get("confidence") or 0.5),
                   list(body.get("risks") or []))
    return {"ok": True, "ops": len(session.ops)}
