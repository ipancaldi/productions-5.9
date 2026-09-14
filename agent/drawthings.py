"""Z IMAGE TURBO, THROUGH DRAW THINGS, ON THIS MACHINE — the `drawthings` engine.

WHAT THIS TALKS TO, AND HOW I KNOW
----------------------------------
Draw Things (1.20260716.0 here) ships an **AUTOMATIC1111-compatible HTTP API**. That
is not an assumption — these three paths are in the app binary and nothing else in it
looks like a server:

    /sdapi/v1/txt2img
    /sdapi/v1/img2img
    /sdapi/v1/options

So the integration is JSON over HTTP to a port on this machine: no gRPC, no protobuf,
no SDK, no dependency this service does not already have. `urllib` is what the vision
adapter already uses to reach LM Studio, and it is all this needs.

WHAT IS *NOT* IN THAT LIST, because it decides the design: there is no
`/sdapi/v1/sd-models` and no `/sdapi/v1/progress`. This adapter therefore **cannot
enumerate or choose a model, and cannot report progress**. Whatever checkpoint the
app has loaded is what generates, and this module's job is to say so rather than to
pretend it picked it. `/sdapi/v1/options` is used only to prove the server is alive
and to read back whatever it will tell us about the loaded model.

NO DUPLICATE MODEL FILES, BY CONSTRUCTION. Nothing here reads, writes, copies or
downloads a checkpoint. The 5.94 GB of `z_image_turbo_1.0_q8p.ckpt` lives once, in
Draw Things' own container, and is reached only by asking the running app to use it.

WHAT COMES BACK. The A1111 contract returns the image as base64 in the JSON body, so
the bytes arrive in-process. This module writes the PNG to the configured output
folder AND returns the base64, because those serve two different needs: the file is
the archive, the base64 is what the panel turns into a draggable asset without a
second round trip or a static route.

SIZE IS NOT THE CANVAS SIZE, AND THAT IS DELIBERATE. Z-Image is a ~1024px-native
model. Asked for a 2 640 × 1 408 LED wall directly it would be slow and visibly
degraded, so the request is fitted to `LONG_EDGE` at the ASPECT that was asked for,
rounded to the multiple of 64 that diffusion models want, and BOTH sizes come back in
the metadata. Upscaling to the wall is a separate, explicit decision and this module
does not quietly make it.
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import time
from urllib import error as urlerror
from urllib import request as urlrequest

ENGINE = "drawthings"

# ---------------------------------------------------------------- configuration --
# Every one of these is an environment variable, because that is how this service
# already configures LM Studio (see vision.LM_STUDIO_URL) and because a port, a path
# and a step count are exactly the things that differ between two machines.
#
#   DRAWTHINGS_URL     where the app's API server is listening
#   IMAGE_OUT_DIR      where finished PNGs are written
#   DT_LONG_EDGE       longest side actually generated, before any upscale
#   DT_STEPS/DT_CFG    Turbo defaults — see the note below
#   DT_SAMPLER         sampler name, passed through as A1111 spells it
#   DT_NEGATIVE        default negative prompt
#   DT_TIMEOUT         seconds to wait for one image
BASE = os.environ.get("DRAWTHINGS_URL", "http://127.0.0.1:7860").rstrip("/")
# PORTS TO TRY WHEN THE CONFIGURED ONE IS DEAD. Draw Things lets you choose the port,
# and "which port did you pick" is a question the panel should not have to ask a person
# — so a failed probe of BASE falls through to the handful the app and its ecosystem
# actually use, and whichever answers /sdapi/v1/options IS Draw Things and is reported
# as the one that was found. Bounded and explicit on purpose: this is four known
# candidates, not a scan, and setting DRAWTHINGS_URL skips it entirely.
SNIFF = [int(x) for x in os.environ.get("DT_SNIFF_PORTS", "7860,7859,7861,3000").split(",") if x.strip()]
_found = ""            # a port discovered this run, remembered so it is probed first
_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.environ.get("IMAGE_OUT_DIR", os.path.join(_HERE, "Content", "ai-generated"))
LONG_EDGE = int(os.environ.get("DT_LONG_EDGE", "1536"))
# THE SIZE GRID, and it is not a detail. Diffusion UNets want whole multiples of a
# power of two, and which power decides how faithfully an aspect survives: 16:9 at a
# 1 536 long edge is 1 536 × 864, and 864 is a multiple of 32 but NOT of 64 — so on a
# 64 grid the nearest legal frame is 1 536 × 896, a 3.6% aspect error you would see
# as a slightly wrong crop on a wall. 64 is the conservative default because every
# SD-family model accepts it; try 32 once Z Image Turbo is loaded and, if it renders
# cleanly, keep it — most modern models do, and the aspect then comes out exact.
GRID = int(os.environ.get("DT_GRID", "64"))

# TURBO DEFAULTS, NOW MEASURED — 8 Sep, Z Image Turbo q8p on an M2 Ultra, at 1536×832.
#
#   steps  cfg   time
#   ---------------------
#     8    1.5   131.5 s     ← the original guesses
#     8    1.0    35.2 s
#     4    1.0    17.3 s     ← these
#
# CFG IS THE WHOLE STORY, and it is worth understanding rather than copying. Guidance
# above 1.0 turns classifier-free guidance ON, which means TWO forward passes per step
# — the conditional and the unconditional — so 1.5 did not cost 50% more than 1.0, it
# cost 3.7× more. A distilled Turbo model has the guidance baked in and is trained to
# be run at 1.0; asking for more buys nothing and pays double for it.
#
# Then 4 steps against 8 halves it again with no visible cost on stage-scale content —
# checked by eye on a curtain-and-scan-lines frame, which is the kind of thing this is
# for. Raise DT_STEPS for fine detail; there is no reason to raise DT_CFG at all.
STEPS = int(os.environ.get("DT_STEPS", "4"))
CFG = float(os.environ.get("DT_CFG", "1.0"))
SAMPLER = os.environ.get("DT_SAMPLER", "Euler A Trailing")
NEGATIVE = os.environ.get("DT_NEGATIVE", "text, watermark, signature, blurry, low quality")
TIMEOUT = float(os.environ.get("DT_TIMEOUT", "240"))
# The checkpoint the STILL path asks for by name. `DT_IMAGE_MODEL=` (empty) means "use
# whatever the app has loaded", which is the right answer for someone driving Draw
# Things by hand at the same time.
IMAGE_MODEL = os.environ.get("DT_IMAGE_MODEL", "z_image_turbo_1.0_q8p.ckpt").strip()
# MEASURED: a 1536x896 frame at 4 steps is 17-21 s warm on this machine. Reported so the
# panel can say how long before it is asked, rather than after. It is a property of the
# machine, hence an environment variable, and it is only a FLOOR: a still generated right
# after a clip also pays for Draw Things swapping a 16 GB video checkpoint back out, which
# measured 160 s and is not something a constant can predict.
SECS_PER_IMAGE = float(os.environ.get("DT_SECS_PER_IMAGE", "21"))


def config() -> dict:
    """What this engine is configured to do, for `/v1/image/health` to report. A
    pipeline whose settings are invisible is a pipeline nobody can debug."""
    return {"url": base(), "configured": BASE, "model": IMAGE_MODEL or None,
            "sniff": SNIFF, "out_dir": OUT_DIR, "long_edge": LONG_EDGE, "grid": GRID,
            "steps": STEPS, "cfg": CFG, "sampler": SAMPLER, "timeout": TIMEOUT,
            "secs_per_image": SECS_PER_IMAGE}


# ------------------------------------------------------------------- reachability --
def base() -> str:
    """The URL to talk to: whatever was configured, or whatever was found."""
    return _found or BASE


def _get(path: str, timeout: float = 2.5, at: str = ""):
    req = urlrequest.Request(f"{at or base()}{path}", method="GET")
    with urlrequest.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def app_ports() -> list[int]:
    """EVERY PORT THE DRAW THINGS PROCESS IS ACTUALLY LISTENING ON.

    Guessing ports was the wrong shape of answer. The app lets you choose the port, so
    a fixed candidate list is a list of guesses — and on this machine the app came up
    listening on 63313, which no sensible guess would have contained. `lsof` knows,
    because the kernel knows, so it is asked.

    This is not a scan: it is the set of sockets one named process holds. A port found
    this way is still PROVED to be the API by asking it for `/sdapi/v1/options` — the
    app also runs a local-network peer listener for Server Offload, and that one
    accepts a connection and closes it without a word.
    """
    try:
        pids = subprocess.run(["pgrep", "-f", "Draw Things.app/Contents/MacOS/DrawThings"],
                              capture_output=True, text=True, timeout=3).stdout.split()
        if not pids:
            return []
        out = subprocess.run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN", "-a", "-p", ",".join(pids)],
                             capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    ports = []
    for m in re.finditer(r":(\d+)\s+\(LISTEN\)", out):
        p = int(m.group(1))
        if p not in ports:
            ports.append(p)
    return ports


def _sniff() -> tuple[str, dict]:
    """The first port that answers like Draw Things, or ("", {}). The app's own
    listening ports first — it knows better than any list — then the conventional
    ones, for the case where the API is being served by something else entirely."""
    tried = {BASE}
    for port in app_ports() + SNIFF:
        url = f"http://127.0.0.1:{port}"
        if url in tried:
            continue
        tried.add(url)
        try:
            opts = _get("/sdapi/v1/options", 1.2, url)
        except Exception:
            continue
        if isinstance(opts, dict):
            return url, opts
    return "", {}


def available() -> tuple[bool, str, dict]:
    """(ok, why, options). A NAMED state for each way this can be not-ready, because
    "it didn't work" is the one answer a person cannot act on:

      · nothing listening      the API server is off in Draw Things, or on another port
      · listening, not Draw     something else owns that port
      · answering               the loaded checkpoint, if the app will say
    """
    global _found
    try:
        opts = _get("/sdapi/v1/options")
        if isinstance(opts, dict):
            return True, "", opts
        return False, f"{base()} answered with {type(opts).__name__}, not an options object", {}
    except urlerror.HTTPError as exc:
        # It answered, which means SOMETHING is there — just not this endpoint.
        why = (f"{base()} answered {exc.code} for /sdapi/v1/options — that port is "
               "serving something other than Draw Things")
    except (urlerror.URLError, OSError):
        why = f"nothing is answering on {base()}"
    except ValueError:
        why = f"{base()} answered, but not with JSON — that is not Draw Things"
    # the configured URL is dead or wrong: try the ports the app actually uses
    url, opts = _sniff()
    if url:
        _found = url
        return True, "", opts
    _found = ""
    mine = app_ports()
    if mine:
        seen = ", ".join(str(p) for p in mine)
        return False, (f"Draw Things is running and listening on {seen}, but none of those "
                       "speaks the HTTP API — that is what its local-network peer listener "
                       "looks like. Turn API Server on with Protocol = HTTP (not gRPC)."), {}
    return False, (why + ", and the Draw Things process is not listening on anything — "
                   "turn API Server on in the app, with Protocol = HTTP"), {}


def loaded_model(opts: dict) -> str:
    """The checkpoint Draw Things has loaded, as well as it will tell us. There is no
    model-list endpoint, so this is read from options and falls back to a plain
    admission rather than to a guess."""
    for key in ("sd_model_checkpoint", "sd_model", "model", "checkpoint"):
        v = opts.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return "whatever is loaded in Draw Things"


# --------------------------------------------------------------------- geometry --
def fit(w: int, h: int, long_edge: int = 0, grid: int = 0) -> tuple[int, int]:
    """The requested ASPECT at a size the model is actually good at, quantised to
    `GRID`. A 2 640 × 1 408 wall becomes 1 536 × 832. The nearest legal value is
    chosen on each axis, so the error is the smallest the grid allows — and the
    achieved size is reported next to the asked-for one rather than hidden."""
    long_edge, grid = long_edge or LONG_EDGE, max(8, grid or GRID)
    w, h = max(1, int(w)), max(1, int(h))
    k = long_edge / max(w, h)
    q = lambda v: max(grid * 4, int(round(v * k / grid)) * grid)
    return q(w), q(h)


# ---------------------------------------------------------------------- drawing --
_SLUG = re.compile(r"[^a-z0-9]+")


def _slug(s: str, n: int = 48) -> str:
    return _SLUG.sub("-", s.lower()).strip("-")[:n] or "frame"


def draw(prompt: str, w: int, h: int, seed: int | None = None,
         steps: int | None = None, cfg: float | None = None,
         negative: str | None = None,
         long_edge: int = 0, grid: int = 0) -> dict:
    """One image, locally. Returns a dict the endpoint hands straight back —
    including every failure, named, because a panel can only report what it is told."""
    t0 = time.time()
    ok, why, opts = available()
    if not ok:
        return {"ok": False, "engine": ENGINE, "why": why, "model": None, "ms": 0,
                "config": config()}

    gw, gh = fit(w, h, long_edge, grid)
    # HOW FAITHFUL THE ASPECT ACTUALLY IS. Capping the long edge and quantising the
    # short one is fine for ordinary canvases — a 2 640 × 1 408 wall lands within 1.5%
    # — and it is NOT fine for an extreme ribbon: 15 360 × 1 080 (14.2:1) comes back as
    # 1 536 × 256 (6:1), because the short side has nowhere to go. A wall that shape
    # wants tiling or outpainting, not one pass, and until something does that the
    # honest move is to hand the number back rather than quietly return a frame that
    # will be stretched.
    want_a, got_a = (w / max(1, h)), (gw / max(1, gh))
    skew = abs(got_a - want_a) / max(0.0001, want_a)
    body = {
        "prompt": prompt,
        "negative_prompt": negative if negative is not None else NEGATIVE,
        "steps": int(steps or STEPS),
        "cfg_scale": float(cfg if cfg is not None else CFG),
        "width": gw, "height": gh,
        "sampler_name": SAMPLER,
        "batch_size": 1, "n_iter": 1,
        "seed": int(seed) if seed is not None else -1,
    }
    if IMAGE_MODEL:
        body["model"] = IMAGE_MODEL
    try:
        req = urlrequest.Request(f"{base()}/sdapi/v1/txt2img",
                                 data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
        with urlrequest.urlopen(req, timeout=TIMEOUT) as r:
            reply = json.load(r)
    except urlerror.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        # 4xx here is overwhelmingly "no model is loaded" or "that size/sampler is not
        # available", and both are things the person can fix in the app.
        return {"ok": False, "engine": ENGINE, "ms": int((time.time() - t0) * 1000),
                "model": loaded_model(opts), "config": config(),
                "why": (f"Draw Things refused the job ({exc.code}). Check that a model is "
                        f"loaded and generation works in the app itself."
                        + (f" It said: {detail}" if detail else ""))}
    except (urlerror.URLError, OSError) as exc:
        # A timeout lands here too, and it is worth separating: a Turbo model that has
        # taken four minutes is not slow, something is wrong.
        reason = getattr(exc, "reason", exc)
        timed_out = "timed out" in str(reason).lower()
        return {"ok": False, "engine": ENGINE, "ms": int((time.time() - t0) * 1000),
                "model": loaded_model(opts), "config": config(),
                "why": (f"Draw Things did not finish inside {TIMEOUT:.0f}s. A Turbo model "
                        "should take seconds — check the app is not still loading the "
                        "checkpoint, and raise DT_TIMEOUT if it genuinely needs longer."
                        if timed_out else f"the connection to Draw Things failed: {reason}")}
    except ValueError as exc:
        return {"ok": False, "engine": ENGINE, "ms": int((time.time() - t0) * 1000),
                "model": loaded_model(opts), "config": config(),
                "why": f"Draw Things answered with something that is not JSON: {exc}"}

    images = reply.get("images") if isinstance(reply, dict) else None
    if not images or not isinstance(images, list) or not images[0]:
        return {"ok": False, "engine": ENGINE, "ms": int((time.time() - t0) * 1000),
                "model": loaded_model(opts), "config": config(),
                "why": ("Draw Things answered without an image. That is what it does when "
                        "generation itself failed — the app's own console will say why.")}
    b64 = images[0]
    if b64.startswith("data:"):                    # tolerated, not expected
        b64 = b64.split(",", 1)[-1]
    try:
        png = base64.b64decode(b64, validate=False)
    except Exception as exc:
        return {"ok": False, "engine": ENGINE, "ms": int((time.time() - t0) * 1000),
                "model": loaded_model(opts), "config": config(),
                "why": f"the image came back but would not decode: {exc}"}

    # SAVED, THEN RETURNED. A failure to write is reported and does NOT lose the
    # image: the bytes still go back, with `saved` false and the reason attached.
    name = f"{_slug(prompt)}-{time.strftime('%Y%m%d-%H%M%S')}.png"
    path, saved, save_why = os.path.join(OUT_DIR, name), False, ""
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(path, "wb") as f:
            f.write(png)
        saved = True
    except OSError as exc:
        save_why = f"could not write to {OUT_DIR}: {exc}"

    info = reply.get("info")
    if isinstance(info, str):
        try:
            info = json.loads(info)
        except ValueError:
            info = {"raw": info[:400]}
    return {
        "ok": True, "engine": ENGINE, "model": loaded_model(opts),
        "ms": int((time.time() - t0) * 1000),
        "png": base64.b64encode(png).decode("ascii"),
        "bytes": len(png),
        "w": gw, "h": gh,                       # what was generated
        "asked": {"w": int(w), "h": int(h)},    # what the canvas wanted
        "path": path if saved else None, "saved": saved, "save_why": save_why,
        "skew": round(skew, 4),
        "warn": (f"the canvas is {want_a:.2f}:1 and this frame is {got_a:.2f}:1 — "
                 f"{skew * 100:.0f}% off. A shape this extreme needs tiling or "
                 "outpainting rather than one pass; raise DT_LONG_EDGE or lower "
                 "DT_GRID to narrow the gap." if skew > 0.05 else ""),
        "steps": body["steps"], "cfg": body["cfg_scale"], "sampler": SAMPLER,
        "seed": (info or {}).get("seed", body["seed"]) if isinstance(info, dict) else body["seed"],
        "negative": body["negative_prompt"],
        "config": config(),
    }
