"""FRAMES INTO A MOVIE. The step Draw Things does not do for you.

A video model reached over the A1111-compatible HTTP API comes back the same way an
image does: base64 PNGs in an `images` array. There is no movie file in that exchange,
so the frames have to be encoded before anything can play them.

WHY NOT FFMPEG. It is not installed on this machine, and adding it would mean a
download and a dependency for one job on a box that already ships a hardware H.264
encoder. So the default path is AVFoundation through a small Swift helper next door in
`native/`, compiled on first use and cached. If ffmpeg IS on PATH it is used instead —
not as a preference, but because a machine that has it usually has it for a reason.

WHY H.264 IN MP4, and not the smaller WebM. This lands in a browser: an <img>-and-
<video> panel, a Content Bin thumbnail, and a THREE.VideoTexture on an LED wall in the
Scene Study. H.264/MP4 is the one encoding all three read in both Safari and Chrome
without negotiation. WebM would have been the smaller change to make and the bigger one
to live with.

FAILURES ARE NAMED, not raised. Encoding is the last step of a job that has already
spent a minute or two on a diffusion model, so losing the frames to an exception would
be the most expensive possible way to fail. Every return says what happened, and the
caller still holds the frames.
"""
from __future__ import annotations

import base64
import os
import shutil
import subprocess
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
NATIVE_DIR = os.path.join(_HERE, "native")
SWIFT_SRC = os.path.join(NATIVE_DIR, "frames2mp4.swift")
SWIFT_BIN = os.environ.get("FRAMES2MP4", os.path.join(NATIVE_DIR, "frames2mp4"))
FFMPEG = os.environ.get("FFMPEG", "") or shutil.which("ffmpeg") or ""
BUILD_TIMEOUT = float(os.environ.get("MUX_BUILD_TIMEOUT", "120"))
MUX_TIMEOUT = float(os.environ.get("MUX_TIMEOUT", "180"))


def _swift_ready() -> tuple[bool, str]:
    """The helper, compiling it if the binary is missing or older than its source.
    Compilation takes ~15 s and happens once; a later run finds the binary."""
    if os.path.isfile(SWIFT_BIN) and os.access(SWIFT_BIN, os.X_OK):
        try:
            if os.path.getmtime(SWIFT_BIN) >= os.path.getmtime(SWIFT_SRC):
                return True, ""
        except OSError:
            return True, ""
    if not os.path.isfile(SWIFT_SRC):
        return False, f"the encoder source is missing at {SWIFT_SRC}"
    swiftc = shutil.which("swiftc")
    if not swiftc:
        return False, ("neither ffmpeg nor swiftc is available, so there is nothing on "
                       "this machine to encode frames with. Install Xcode command line "
                       "tools (xcode-select --install) or ffmpeg.")
    try:
        p = subprocess.run([swiftc, "-O", "-o", SWIFT_BIN, SWIFT_SRC],
                           capture_output=True, text=True, timeout=BUILD_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"could not build the encoder: {exc}"
    if p.returncode != 0 or not os.path.isfile(SWIFT_BIN):
        return False, f"the encoder would not compile: {(p.stderr or '').strip()[:300]}"
    return True, ""


def encoder() -> dict:
    """Which encoder will run, and whether it can — what `/health` reports."""
    if FFMPEG:
        return {"kind": "ffmpeg", "at": FFMPEG, "ok": True, "why": ""}
    ok, why = _swift_ready()
    return {"kind": "avfoundation", "at": SWIFT_BIN if ok else None, "ok": ok, "why": why}


def mux(frames: list[bytes], fps: float, out_path: str) -> dict:
    """PNG frames -> H.264 MP4 at `out_path`. `frames` in play order."""
    t0 = time.time()
    if not frames:
        return {"ok": False, "why": "there are no frames to encode", "ms": 0}
    if len(frames) < 2:
        return {"ok": False, "why": "one frame is not a movie — generate more frames "
                                    "or ask for a still instead", "ms": 0}
    fps = max(1.0, float(fps or 8))
    enc = encoder()
    if not enc["ok"]:
        return {"ok": False, "why": enc["why"], "encoder": enc["kind"], "ms": 0}

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="frames2mp4-")
    try:
        paths = []
        for i, png in enumerate(frames):
            p = os.path.join(tmp, f"{i:05d}.png")
            with open(p, "wb") as f:
                f.write(png)
            paths.append(p)

        if enc["kind"] == "ffmpeg":
            cmd = [FFMPEG, "-y", "-framerate", f"{fps:g}",
                   "-i", os.path.join(tmp, "%05d.png"),
                   "-c:v", "libx264", "-pix_fmt", "yuv420p",
                   # even dimensions: H.264 in yuv420p requires them
                   "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                   "-movflags", "+faststart", out_path]
        else:
            cmd = [SWIFT_BIN, out_path, f"{fps:g}", *paths]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=MUX_TIMEOUT)
        except subprocess.TimeoutExpired:
            return {"ok": False, "encoder": enc["kind"], "ms": int((time.time() - t0) * 1000),
                    "why": f"the encoder did not finish inside {MUX_TIMEOUT:.0f}s"}
        except OSError as exc:
            return {"ok": False, "encoder": enc["kind"], "ms": int((time.time() - t0) * 1000),
                    "why": f"the encoder would not run: {exc}"}
        if p.returncode != 0 or not os.path.isfile(out_path):
            msg = ((p.stderr or p.stdout or "").strip().splitlines() or ["no reason given"])[-1]
            return {"ok": False, "encoder": enc["kind"], "ms": int((time.time() - t0) * 1000),
                    "why": f"encoding failed: {msg[:300]}"}

        with open(out_path, "rb") as f:
            data = f.read()
        return {"ok": True, "encoder": enc["kind"], "path": out_path,
                "mp4": base64.b64encode(data).decode("ascii"),
                "bytes": len(data), "frames": len(frames), "fps": fps,
                "secs": round(len(frames) / fps, 3),
                "ms": int((time.time() - t0) * 1000)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
