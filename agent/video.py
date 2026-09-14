"""MOVING CONTENT, locally. Z Image Turbo draws the first frame; Wan animates it.

THE SHAPE OF THE PIPELINE, and why it is this shape:

    prompt ──> Z Image Turbo (txt2img) ──> keyframe PNG
                                             │
                       (or a still the user already has)
                                             ▼
                        Wan 2.1 14B I2V (img2img, num_frames) ──> N PNG frames
                                             ▼
                                    mux.py ──> H.264 MP4

An image-to-video model needs a starting picture, and this workspace already has a very
good one: the same Turbo model that draws the stills, at the wall's own aspect. So video
is not a second pipeline, it is the image pipeline with one more stage. A user who has
already generated a still they like can hand THAT in as the keyframe instead and skip
the first stage entirely — which is both cheaper and the more likely way this gets used
once someone is actually working.

ONE HTTP API, TWO MODELS, NO GLOBAL STATE. Draw Things' HTTP surface is four routes:
`GET /`, `GET /sdapi/v1/options`, and POST on txt2img and img2img. `POST` to options
answers 404 — settings are READ-ONLY over HTTP — so every knob has to travel in the
generation body, and measurement says they all can: `model`, `num_frames`, `fps`,
`shift`, `motion_scale`, `start_frame_guidance`, `guiding_frame_noise` are all accepted
there, and none of them persists into the app afterwards (a video pass leaves the app's
own `num_frames` and loaded model exactly as they were).

That is the good outcome rather than the compromise. Each request is self-contained, so
there is no settings dance around a generation, nothing to put back in a `finally`, and
no way for a video pass to leave a 16 GB checkpoint loaded under the next still.

TWO THINGS THE BODY IS STRICT ABOUT, both learned from its 422s:
  · An unknown key is refused outright — "Unrecognized keys" — so nothing speculative
    can be sent on the off-chance it helps.
  · `init_images` must match `width`/`height` EXACTLY. So the frame size is read out of
    the keyframe PNG itself rather than recomputed, because a recomputation that
    disagrees with the actual image by one pixel fails the whole job.

THE MODEL IS FOUND ON DISK, not over HTTP. Draw Things has no `/sdapi/v1/sd-models`
endpoint (it answers 404), so the checkpoint list comes from its Models directory. That
turns out to be a feature rather than a workaround: a half-downloaded checkpoint sits
there as `.partial`, so this module can tell the panel "the video model is still
downloading" instead of the useless "generation failed" it would get from a POST.

TIME. A still is seconds. A five-second 480p clip is minutes, plus up to a minute the
first time, while a 16 GB checkpoint is read off disk. Every default here is set for
that reality and every one of them is an environment variable, because the right
trade between length, size and wait is a judgement for the person waiting.
"""
from __future__ import annotations

import base64
import glob
import json
import os
import time
from urllib import error as urlerror
from urllib import request as urlrequest

import drawthings as dt
import mux

ENGINE = "wan-i2v"

# WHERE DRAW THINGS KEEPS ITS CHECKPOINTS. Sandboxed app container, so this is a fixed
# path rather than anything discoverable; `DT_MODELS_DIR` moves it for a machine that
# has pointed the app somewhere else.
MODELS_DIR = os.environ.get("DT_MODELS_DIR", os.path.expanduser(
    "~/Library/Containers/com.liuliu.draw-things/Data/Documents/Models"))

# Preference order, best first. FusionX is a distilled Wan that gets there in ~8 steps;
# SkyReels 1.3B is the small one worth having on a machine with less memory.
PREFER = [s.strip() for s in os.environ.get(
    "DT_VIDEO_PREFER", "wan_2.1_14b_i2v_fusionx,wan_2.1_14b_i2v,wan_2.1,skyreels,_i2v").split(",")
    if s.strip()]
PINNED = os.environ.get("DT_VIDEO_MODEL", "")

# 480p is the resolution Wan 2.1 I2V is trained for at this size class, and a long edge
# of 832 with a stride of 16 lands the common wall aspects on legal dimensions.
LONG_EDGE = int(os.environ.get("DT_VIDEO_LONG_EDGE", "832"))
# 64, NOT WAN'S OWN 16-PIXEL STRIDE, and this is measured rather than chosen: Draw
# Things quantises the size it is asked for down to a multiple of 64 on its own. A
# 1920x1080 canvas requested at stride 16 came back 832x448, not the 832x464 the
# arithmetic here predicted. Since the KEYFRAME's real size is what the animation pass
# is then locked to, predicting 464 and receiving 448 made this module's own reported
# geometry wrong. 64 makes the prediction match what the app actually does.
GRID = int(os.environ.get("DT_VIDEO_GRID", "64"))
# 33 FRAMES — ABOUT TWO SECONDS — AND NOT WAN'S OWN 81, and this is a measured
# decision rather than a cautious one. A warm 81-frame pass at 832x448 took 876 s on
# this machine: 10.8 s per frame, so a five-second clip is nearly fifteen minutes. That
# is a fine thing to ASK for and a terrible thing to DEFAULT to, because the first
# thing anyone does with a generator is iterate, and a fifteen-minute round trip is not
# iteration. Two seconds costs about six minutes and still shows whether the motion is
# what you wanted; the slider goes to ten seconds when it is.
FRAMES = int(os.environ.get("DT_VIDEO_FRAMES", "33"))
FPS = int(os.environ.get("DT_VIDEO_FPS", "16"))
STEPS = int(os.environ.get("DT_VIDEO_STEPS", "8"))
CFG = float(os.environ.get("DT_VIDEO_CFG", "1.0"))
SHIFT = float(os.environ.get("DT_VIDEO_SHIFT", "5.0"))
MOTION = int(os.environ.get("DT_VIDEO_MOTION", "127"))
SAMPLER = os.environ.get("DT_VIDEO_SAMPLER", "Euler A Trailing")
# AN HOUR, and that is not padding. At the measured 10.8 s per frame the slider's
# longest setting — 161 frames — is about 29 minutes, so a 30-minute timeout would have
# failed the longest clip the panel can ask for, after 29 minutes of GPU. The ceiling
# has to sit above what the UI permits, or the UI is lying.
TIMEOUT = float(os.environ.get("DT_VIDEO_TIMEOUT", "3600"))
LOAD_TIMEOUT = float(os.environ.get("DT_VIDEO_LOAD_TIMEOUT", "300"))
MAX_FRAMES = int(os.environ.get("DT_VIDEO_MAX_FRAMES", "161"))
# MEASURED ON THIS MACHINE: 81 frames at 832x448, 8 steps, warm, took 876 s. It is
# reported to the panel so the length slider can say what it will cost in minutes
# rather than leaving somebody to discover it — and it is an environment variable
# because it is a property of the machine, not of the code.
SECS_PER_FRAME = float(os.environ.get("DT_VIDEO_SECS_PER_FRAME", "10.8"))

OUT_DIR = os.environ.get("VIDEO_OUT_DIR", dt.OUT_DIR)


def config() -> dict:
    return {"models_dir": MODELS_DIR, "model": PINNED or None, "long_edge": LONG_EDGE,
            "grid": GRID, "frames": FRAMES, "fps": FPS, "steps": STEPS, "cfg": CFG,
            "shift": SHIFT, "motion": MOTION, "sampler": SAMPLER,
            "timeout": TIMEOUT, "out_dir": OUT_DIR, "max_frames": MAX_FRAMES,
            "secs_per_frame": SECS_PER_FRAME}


# ------------------------------------------------------------- finding the model --
def checkpoints() -> list[str]:
    try:
        return sorted(os.path.basename(p) for p in glob.glob(os.path.join(MODELS_DIR, "*.ckpt")))
    except OSError:
        return []


def downloading() -> list[str]:
    """Checkpoints Draw Things is still fetching. Named separately because "not yet"
    and "not there" are different answers and only one of them means waiting."""
    try:
        return sorted(os.path.basename(p)[:-len(".partial")]
                      for p in glob.glob(os.path.join(MODELS_DIR, "*.ckpt.partial")))
    except OSError:
        return []


def _match(names: list[str], want: str) -> str | None:
    return next((n for n in names if want in n.lower()), None)


def model() -> tuple[str | None, str]:
    """(checkpoint filename, why not). The one that will animate."""
    have = checkpoints()
    if PINNED:
        if PINNED in have:
            return PINNED, ""
        if PINNED in downloading():
            return None, f"{PINNED} is still downloading in Draw Things"
        return None, f"DT_VIDEO_MODEL={PINNED} is not in {MODELS_DIR}"
    for want in PREFER:
        hit = _match(have, want)
        if hit:
            return hit, ""
    for want in PREFER:                          # not there yet, but on its way
        hit = _match(downloading(), want)
        if hit:
            return None, (f"{hit} is still downloading in Draw Things — video will work "
                          "once it finishes; stills work now")
    return None, ("no image-to-video checkpoint is installed. In Draw Things, download "
                  "Wan 2.1 14B I2V (or SkyReels v2 1.3B I2V on a smaller machine).")


def available() -> tuple[bool, str, dict]:
    """Everything the video path needs: the app, the checkpoint, and an encoder."""
    ok, why, opts = dt.available()
    if not ok:
        return False, why, {}
    m, mwhy = model()
    if not m:
        return False, mwhy, opts
    enc = mux.encoder()
    if not enc["ok"]:
        return False, enc["why"], opts
    return True, "", opts


def state() -> dict:
    """What `/v1/image/health` reports for video."""
    ok, why, opts = available()
    m, _ = model()
    return {"ok": ok, "why": why, "model": m, "encoder": mux.encoder(),
            "downloading": downloading(), "config": config()}


# ------------------------------------------------------------- the frame count --
def snap(n: int) -> int:
    """The nearest 4k+1, clamped. Wan 2.1 compresses time by 4 in its latent space, so
    4k+1 is the length it actually works in — 81 frames, its own training length, is
    4x20+1. A request for 16 is not a smaller ask than 17, it is an awkward one, and
    snapping here is better than finding out what the model does with the remainder.

    The panel derives its frame count the same way, so the number on the slider is the
    number that gets generated."""
    n = max(5, min(int(n or 81), MAX_FRAMES))
    k = round((n - 1) / 4)
    return max(5, min(int(4 * k + 1), MAX_FRAMES))


# --------------------------------------------------------------- the frame size --
def png_size(png: bytes) -> tuple[int, int]:
    """(w, h) from a PNG's IHDR. Eight bytes of signature, then a length and the type,
    then the two dimensions — fixed offsets, no image library needed, and no chance of
    disagreeing with the file the way a recomputed `fit` can."""
    if len(png) < 24 or png[:8] != b"\x89PNG\r\n\x1a\n" or png[12:16] != b"IHDR":
        return 0, 0
    return int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big")


def animate(keyframe_png: bytes, motion: str, frames: int | None = None,
            fps: int | None = None, seed: int | None = None,
            steps: int | None = None, cfg: float | None = None,
            negative: str | None = None, asked: dict | None = None) -> dict:
    """A keyframe plus a motion brief becomes an MP4. Failures are named, never raised.

    The frame size is the KEYFRAME's size, not a requested one — see the note above on
    what `init_images` is strict about."""
    t0 = time.time()
    ok, why, _ = available()
    if not ok:
        return {"ok": False, "engine": ENGINE, "why": why, "ms": 0, "config": config()}
    ckpt, _ = model()
    gw, gh = png_size(keyframe_png)
    if gw <= 0 or gh <= 0:
        return {"ok": False, "engine": ENGINE, "model": ckpt, "config": config(), "ms": 0,
                "why": "the first frame is not a PNG this can read the size out of"}
    want_frames = snap(frames or FRAMES)
    want_fps = max(1, int(fps or FPS))

    body = {
        "init_images": [base64.b64encode(keyframe_png).decode("ascii")],
        "prompt": motion or "",
        "negative_prompt": negative if negative is not None else dt.NEGATIVE,
        "model": ckpt,
        "num_frames": want_frames,
        "fps": want_fps,
        "steps": int(steps or STEPS),
        "cfg_scale": float(cfg if cfg is not None else CFG),
        "shift": SHIFT,
        "motion_scale": MOTION,
        "width": gw, "height": gh,
        "sampler_name": SAMPLER,
        # 1.0: the keyframe is the FIRST FRAME, not a noisy base to redraw. A lower
        # strength here does not make the motion gentler, it makes frame one wrong.
        "denoising_strength": 1.0,
        "batch_size": 1, "n_iter": 1,
        "seed": int(seed) if seed is not None else -1,
    }
    try:
        req = urlrequest.Request(f"{dt.base()}/sdapi/v1/img2img",
                                 data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
        with urlrequest.urlopen(req, timeout=TIMEOUT) as r:
            reply = json.load(r)
    except urlerror.HTTPError as exc:
        detail = ""
        try:
            detail = (json.loads(exc.read().decode("utf-8", "replace")) or {}).get("detail", "")
        except Exception:
            pass
        return {"ok": False, "engine": ENGINE, "model": ckpt, "config": config(),
                "ms": int((time.time() - t0) * 1000),
                "why": (f"Draw Things refused the animation ({exc.code})"
                        + (f": {str(detail)[:220]}" if detail else
                           f". Check that {ckpt} loads and generates in the app itself."))}
    except (urlerror.URLError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        if "timed out" in str(reason).lower():
            return {"ok": False, "engine": ENGINE, "model": ckpt, "config": config(),
                    "ms": int((time.time() - t0) * 1000),
                    "why": (f"the animation did not finish inside {TIMEOUT / 60:.0f} min. "
                            f"{want_frames} frames at {gw}x{gh} is a lot to ask — try "
                            "fewer frames or a smaller wall, or raise DT_VIDEO_TIMEOUT.")}
        return {"ok": False, "engine": ENGINE, "model": ckpt, "config": config(),
                "ms": int((time.time() - t0) * 1000),
                "why": f"the connection to Draw Things failed: {reason}"}
    except ValueError as exc:
        return {"ok": False, "engine": ENGINE, "model": ckpt, "config": config(),
                "ms": int((time.time() - t0) * 1000),
                "why": f"Draw Things answered with something that is not JSON: {exc}"}

    images = reply.get("images") if isinstance(reply, dict) else None
    if not images or not isinstance(images, list):
        return {"ok": False, "engine": ENGINE, "model": ckpt, "config": config(),
                "ms": int((time.time() - t0) * 1000),
                "why": ("Draw Things answered without any frames, which is what it does "
                        "when generation itself failed — its own console will say why.")}
    out = []
    for b64 in images:
        if not b64:
            continue
        if b64.startswith("data:"):
            b64 = b64.split(",", 1)[-1]
        try:
            out.append(base64.b64decode(b64, validate=False))
        except Exception:
            pass
    # ONE FRAME BACK IS THE SIGNATURE OF A STILL MODEL. Worth saying plainly, because
    # the alternative is a one-frame "video" nobody can explain.
    if len(out) < 2:
        return {"ok": False, "engine": ENGINE, "model": ckpt, "config": config(),
                "ms": int((time.time() - t0) * 1000), "frames": len(out),
                "why": (f"{ckpt} returned {len(out)} frame rather than a sequence. That is "
                        "what happens when the loaded checkpoint is an image model — check "
                        "it is the image-to-video one.")}

    name = f"{dt._slug(motion or 'clip')}-{time.strftime('%Y%m%d-%H%M%S')}.mp4"
    path = os.path.join(OUT_DIR, name)
    enc = mux.mux(out, want_fps, path)
    if not enc["ok"]:
        return {"ok": False, "engine": ENGINE, "model": ckpt, "config": config(),
                "frames": len(out), "ms": int((time.time() - t0) * 1000), "why": enc["why"]}

    return {
        "ok": True, "engine": ENGINE, "model": ckpt,
        "ms": int((time.time() - t0) * 1000),
        "mp4": enc["mp4"], "bytes": enc["bytes"], "encoder": enc["encoder"],
        "frames": len(out), "fps": want_fps, "secs": enc["secs"],
        # The keyframe travels back as the poster: the panel and the Content Bin both
        # want a picture, and this one is free — already decoded, and frame one by
        # construction, so nothing has to seek or decode a movie to get it.
        "png": base64.b64encode(keyframe_png).decode("ascii"),
        "w": gw, "h": gh, "asked": asked or {"w": gw, "h": gh},
        "path": path, "saved": True,
        "steps": int(steps or STEPS), "cfg": float(cfg if cfg is not None else CFG),
        "sampler": SAMPLER, "config": config(),
    }
