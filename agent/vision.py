"""A reference sketch → real geometry. SmolVLM2 reads it; a tracer measures it.

    MODEL = ".../SmolVLM2-256M-Instruct/snapshots/067788b..."

THE DIVISION OF LABOUR, AND WHY IT IS NOT NEGOTIABLE
----------------------------------------------------
A 500-million-parameter vision model is genuinely good at one thing and hopeless at
another, and the difference is the whole design of this file.

It is good at JUDGEMENT over a picture: *is this a plan or an elevation · is this
shape a deck, an LED wall, a projection surface or a seating block*. Those are short,
closed-vocabulary questions about what something IS, and a small VLM answers them
usefully.

It is hopeless at MEASUREMENT. Ask any language model for `verts: [[-60,-40], …]` and
it will produce a plausible list of numbers that is not the shape in the picture — and
at 500M it will not be close. Nothing downstream can tell an invented coordinate from a
measured one, so a model that guesses geometry poisons every figure the Scene Study
derives from it.

So the geometry is TRACED, deterministically, from the pixels:

    threshold → close the gaps → find the regions the lines enclose → follow each
    boundary → fit it to vertices and true circular arcs

and the model is asked only what each traced region IS. That is the same rule the rest
of this service already follows — *judgement in the model, arithmetic in Python* — and
the same rule the Sketch Pad follows when it hands over a fit rather than pixels.

The fit is a deliberate mirror of the pad's, contract in `SOLIDS.md`: RDP simplify, a
Kåsa circle fit with a sagitta gate, regularise, and bulges on the wire. It is
duplicated rather than shared because the pad fits what a person traced with a pointer
and this fits what a camera photographed off a wall — neither can call the other, and a
pure function of five numbers is the cheapest thing in this system to keep honest.

WHAT IT REFUSES TO DO
---------------------
It never invents a scale. A photograph of a drawing carries no declared scale, so every
position it produces is `fitted` at best and `guessed` when the venue has posted no
dimensions either — and the plan says so in its risks. The alternative is a scene that
looks measured and is not.
"""
from __future__ import annotations

import io
import json
import math
import os
import re
import subprocess
import tempfile
import base64
from urllib import error as urlerror
from urllib import request as urlrequest
from dataclasses import dataclass, field
from typing import Any

# The checkpoint asked for. `VISION_MODEL` swaps it with no other change — see § 4: the
# arbitration is explicit precisely so a larger VLM can start winning it on merit.
LOCAL_MODEL = os.path.join(os.path.dirname(__file__), "models", "snapshots",
                           "067788b187b95ebe7b2e040b3e4299e342e5b8fd")
MODEL = os.environ.get("VISION_MODEL", LOCAL_MODEL)
MODEL_NAME = "SmolVLM2-256M-Instruct" if MODEL == LOCAL_MODEL else MODEL.rsplit("/", 1)[-1]

# The production agent uses LM Studio by default.  The original Transformers
# checkpoint remains available as an explicit fallback for development, but it
# is no longer loaded inside this process when a local LM Studio server is up.
BACKEND = os.environ.get("VISION_BACKEND", "lmstudio").lower()
# 4096, not LM Studio's own default of 1234. This machine serves on 4096, and a wrong
# port here is indistinguishable from "no model loaded": `_lmstudio_model` cannot reach
# `/v1/models`, returns None, and every panel honestly reports VISION as tracer-only while
# a perfectly good VLM sits there answering on another port. Override per machine.
LM_STUDIO_URL = os.environ.get("LM_STUDIO_URL", "http://127.0.0.1:4096/v1")
LM_STUDIO_MODEL = os.environ.get("LM_STUDIO_MODEL", "")

# WHICH LOADED MODEL WINS, when nothing is pinned. Substrings, in order, matched against
# the ids LM Studio reports — the API says nothing about a model's MODALITY, so this list
# is the only place that knows which of them can look at a picture.
#
# Qwen is first because it won on merit, which is what § 4 said this arbitration was for.
# On a 32x32 test card of a black rectangle, asked the question this adapter actually asks
# at the budget it actually sends: Qwen answers "rectangle"; smolvlm2-2.2b answers "Circle."
# and leaks its chat template into the reply. A wrong answer is worse here than no answer,
# because the tracer's measurements are trusted and the role labels ride on the VLM.
LM_STUDIO_PREFER = ("qwen2.5-vl", "qwen2-vl", "qwen3.8", "qwen-vl",
                    "smolvlm", "llava", "moondream", "pixtral", "internvl", "minicpm-v")

# ---------------------------------------------------------------------------- deps --
# Imported defensively and reported honestly. This service has to start, answer
# `/health` and interpret a *sketch* on a machine with no torch on it — the same way it
# has to start with no Anthropic credential. A missing dependency is a named state, not
# a stack trace at boot.
try:
    import numpy as np
except Exception:                                            # pragma: no cover
    np = None
try:
    from PIL import Image
except Exception:                                            # pragma: no cover
    Image = None

_TORCH_ERR = ""
try:
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor
except Exception as exc:                                     # pragma: no cover
    torch = None
    AutoProcessor = AutoModelForImageTextToText = None
    _TORCH_ERR = f"{type(exc).__name__}: {exc}"

OFF = os.environ.get("VISION_OFF") == "1"
TRACE_ONLY = os.environ.get("VISION_TRACE_ONLY") == "1"


def _lmstudio_model() -> str | None:
    """Return the selected loaded LM Studio model, without making startup fragile."""
    if BACKEND != "lmstudio":
        return None
    try:
        with urlrequest.urlopen(f"{LM_STUDIO_URL}/models", timeout=1.5) as response:
            rows = json.load(response).get("data", [])
    except (OSError, ValueError, urlerror.URLError):
        return None
    ids = [row.get("id", "") for row in rows if row.get("id")]
    if LM_STUDIO_MODEL:
        return LM_STUDIO_MODEL if LM_STUDIO_MODEL in ids else None
    # in preference order, not in whatever order LM Studio happened to list them
    for want in LM_STUDIO_PREFER:
        hit = next((m for m in ids if want in m.lower()), None)
        if hit:
            return hit
    return None


def traceable() -> bool:
    """Can we measure a picture? numpy and Pillow are all that takes."""
    return not OFF and np is not None and Image is not None


def available() -> bool:
    """Can we also ASK about it? That needs the model."""
    if not traceable() or TRACE_ONLY:
        return False
    if BACKEND == "lmstudio":
        return _lmstudio_model() is not None
    return torch is not None


def why() -> str:
    if OFF:
        return "pinned off by VISION_OFF=1"
    if np is None or Image is None:
        return "numpy and Pillow are not installed — no reference can be traced"
    if TRACE_ONLY:
        return "pinned by VISION_TRACE_ONLY=1 — shapes are traced, roles are inferred from the layout"
    if BACKEND == "lmstudio":
        if _lmstudio_model() is None:
            return "LM Studio is not running with a vision model loaded — shapes are still traced"
        return f"{_lmstudio_model()} reads the drawing through LM Studio; the tracer measures it"
    if torch is None:
        return (f"torch/transformers are not installed ({_TORCH_ERR or 'import failed'}) — "
                "shapes are still traced, roles are inferred from the layout")
    return f"{MODEL_NAME} reads the drawing; the tracer measures it"


def _engine_name(model: str | None) -> str:
    """The family actually answering, not the family this module was written around.
    Reporting `smolvlm2` while Qwen reads the drawing is the kind of small lie that
    costs an afternoon when the answers look wrong and the label looks right."""
    low = (model or "").lower()
    for fam in ("qwen", "smolvlm", "llava", "moondream", "pixtral", "internvl", "minicpm"):
        if fam in low:
            return fam
    return "vlm"


def state() -> dict[str, Any]:
    name = _lmstudio_model() if BACKEND == "lmstudio" else MODEL_NAME
    return {"ok": traceable(), "model": name if available() else None,
            "engine": _engine_name(name) if available() else ("tracer" if traceable() else "off"),
            "why": why()}


def _ocr_rows(data: bytes) -> list[dict[str, Any]]:
    """Run the shared local OCR once and return Vision's normalized boxes."""
    script = os.path.join(os.path.dirname(__file__), "measurement_ocr.swift")
    if not os.path.exists(script):
        return []
    path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(data); path = f.name
        raw = subprocess.run(["swift", script, path], capture_output=True, text=True,
                             timeout=20, check=True).stdout
        return json.loads(raw or "[]")
    except Exception:
        return []
    finally:
        if path:
            try: os.unlink(path)
            except OSError: pass


def measurement_labels(data: bytes, rows: list[dict[str, Any]] | None = None
                       ) -> list[dict[str, Any]]:
    """Accurate local OCR for dimension labels, using macOS Vision rather than asking
    the 256M VLM to transcribe small text. Results are evidence for confirmation, not
    an automatic scale: a label may describe a doorway rather than the whole drawing."""
    rows = rows if rows is not None else _ocr_rows(data)
    unit = re.compile(r"(?<!\w)(\d+(?:[.,]\d+)?)\s*(mm|cm|m|metres?|meters?|ft|feet|')\b", re.I)
    out = []
    for row in rows:
        for match in unit.finditer(row.get("text", "")):
            value = float(match.group(1).replace(",", ".")); u = match.group(2).lower()
            metres = value / 1000 if u == "mm" else value / 100 if u == "cm" else value * 0.3048 if u in ("ft", "feet", "'") else value
            out.append({"text": match.group(0), "metres": round(metres, 3),
                        "confidence": round(float(row.get("confidence", 0)), 3),
                        "box": row.get("box")})
    return out


_SEMANTIC_LABEL = re.compile(
    r"(?<!\w)(CAM(?:ERA)?\s*[-#]?\s*\d+|L[EG]D|PROJ(?:ECTOR|ECTION)?|TRACK|"
    r"STAGE|WALL|SCREEN|AUDIENCE|AUD|SEATING)(?!\w)", re.I)
_SEMANTIC_ROLE = {
    "CAM": "camera", "CAMERA": "camera", "LED": "led", "PROJ": "projector",
    "LGD": "led",  # common handwritten L→G OCR substitution
    "PROJECTOR": "projector", "PROJECTION": "projector", "TRACK": "track",
    "STAGE": "stage", "WALL": "wall", "SCREEN": "screen",
    "AUDIENCE": "audience", "AUD": "audience", "SEATING": "audience",
}


def semantic_label_suggestions(data: bytes, regions: list[Any], size: tuple[int, int],
                               rows: list[dict[str, Any]] | None = None
                               ) -> list[dict[str, Any]]:
    """Associate handwritten semantic labels with the nearest traced object.

    Apple Vision reports boxes in bottom-left-normalized coordinates; traced regions
    use top-left pixels.  Associations remain proposals and explicitly advertise the
    four allowed review actions. No role is mutated here.
    """
    W, H = size
    out: list[dict[str, Any]] = []
    for row in rows if rows is not None else _ocr_rows(data):
        box = row.get("box") or []
        if len(box) != 4:
            continue
        x = (float(box[0]) + float(box[2]) / 2) * W
        y = (1 - float(box[1]) - float(box[3]) / 2) * H
        for match in _SEMANTIC_LABEL.finditer(str(row.get("text", ""))):
            raw = re.sub(r"\s+", " ", match.group(1).strip()).upper()
            base = re.match(r"[A-Z]+", raw).group(0)
            role = _SEMANTIC_ROLE[base]
            target = min(enumerate(regions, 1),
                         key=lambda pair: math.hypot(pair[1].cx - x, pair[1].cy - y),
                         default=None)
            target_id = f"ref{target[0]}" if target else None
            conf = max(0.0, min(1.0, float(row.get("confidence", 0))))
            out.append({
                "id": f"ocr-{len(out) + 1}", "status": "proposed", "text": raw,
                "label": raw, "role": role, "targetId": target_id,
                "targetIndex": target[0] if target else None,
                "at": [round(x, 1), round(y, 1)], "confidence": round(conf, 3),
                "source": "ocr", "highConfidence": conf >= 0.8,
                "actions": ["accept", "edit", "reassign", "reject"],
            })
    return out


# ============================================================================
# 1 · THE TRACER — pixels to polylines, with no model involved
# ============================================================================
MAX_EDGE = 1024          # a hand drawing carries no detail past this, and it is 4× faster
MIN_AREA_FRAC = 0.004    # below this a region is a smudge, a letter or a stray tick
MAX_REGIONS = 8          # a plan with more shapes than this is not what this reads


def _load(data: bytes):
    """Grayscale, downscaled, 0..1. Alpha is composited onto white: a PNG exported
    from a drawing app is usually black lines on nothing at all."""
    im = Image.open(io.BytesIO(data))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im)
    im = im.convert("L")
    w, h = im.size
    k = MAX_EDGE / max(w, h)
    if k < 1:
        im = im.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float32) / 255.0
    return a, im


def _box_mean(a: np.ndarray, r: int) -> np.ndarray:
    """Local mean by integral image, edge-padded. A hand-drawn plan is photographed
    under whatever light was in the room, so one global threshold loses half of it."""
    h, w = a.shape
    p = np.pad(a, r, mode="edge")
    s = p.cumsum(0).cumsum(1)
    s = np.pad(s, ((1, 0), (1, 0)))
    k = 2 * r + 1
    A = s[k:, k:] - s[:h, k:] - s[k:, :w] + s[:h, :w]
    return A / (k * k)


def _ink(a: np.ndarray) -> np.ndarray:
    """The strokes, and only the strokes.

    Two tests, ANDed, because either alone fails on a real reference. The LOCAL one
    adapts to a photograph's uneven light. The GLOBAL one, scaled to the drawing's own
    contrast, is what keeps antialiased edges out — a 4-pixel line resampled by any
    image pipeline has a 3-pixel skirt of half-tones either side, and a flat offset
    threshold swallows the skirt, doubles every stroke's width and then the dilation
    that closes corner gaps merges the whole drawing into one blob with no regions in
    it at all. That failure is invisible in the mask and total downstream, which is why
    the numbers here are relative to `hi - lo` rather than absolute.

    Polarity is decided, not assumed: a photo of a whiteboard and a screenshot of this
    very panel are both references somebody will drop, and they are opposites.
    """
    # 0.5 rather than 2: the ink on a line drawing is a couple of PER CENT of the
    # pixels, so a 2nd-percentile "darkest" lands in the antialiased skirt rather than
    # on a stroke, `span` collapses, and the threshold rejects the drawing entirely.
    lo, hi = (float(np.percentile(a, 0.5)), float(np.percentile(a, 99.5)))
    span = hi - lo
    if span < 0.08:
        return np.zeros_like(a, dtype=bool)          # blank, or all one tone
    r = max(6, min(a.shape) // 24)
    m = _box_mean(a, r)
    dark = (a < m - 0.30 * span) & (a < lo + 0.55 * span)
    light = (a > m + 0.30 * span) & (a > hi - 0.55 * span)
    return dark if dark.mean() >= light.mean() else light


def _dilate(mask: np.ndarray, r: int = 1) -> np.ndarray:
    """Close the gaps a hand leaves at a corner. Without this every open-looking loop
    leaks into the background and the drawing has no regions in it at all."""
    out = mask.copy()
    for _ in range(r):
        p = np.pad(out, 1, constant_values=False)
        out = (p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
               | p[:-2, :-2] | p[:-2, 2:] | p[2:, :-2] | p[2:, 2:] | out)
    return out


def _label(mask: np.ndarray):
    """4-connected components, iteratively — a recursive flood fill on a megapixel
    mask hits Python's stack limit on the first real photograph."""
    h, w = mask.shape
    lab = np.zeros((h, w), dtype=np.int32)
    cur = 0
    comps: list[dict[str, Any]] = []
    stack: list[int] = []
    flat = mask.reshape(-1)
    labf = lab.reshape(-1)
    for start in range(h * w):
        if not flat[start] or labf[start]:
            continue
        cur += 1
        labf[start] = cur
        stack.append(start)
        n = 0
        touches = False
        while stack:
            i = stack.pop()
            n += 1
            y, x = divmod(i, w)
            if y == 0 or x == 0 or y == h - 1 or x == w - 1:
                touches = True
            for j, ok in ((i - w, y > 0), (i + w, y < h - 1),
                          (i - 1, x > 0), (i + 1, x < w - 1)):
                if ok and flat[j] and not labf[j]:
                    labf[j] = cur
                    stack.append(j)
        comps.append({"id": cur, "n": n, "border": touches})
    return lab, comps


# Moore-neighbour order, clockwise from due east
_N8 = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def _boundary(mask: np.ndarray) -> list[list[float]]:
    """Follow the outside of one blob, once round. Moore-neighbour tracing: start at
    the first filled pixel and keep the wall on your left."""
    ys, xs = np.nonzero(mask)
    if not len(ys):
        return []
    start = (int(xs[0]), int(ys[0]))
    h, w = mask.shape
    inside = lambda p: 0 <= p[0] < w and 0 <= p[1] < h and mask[p[1], p[0]]
    out = [list(start)]
    cur = start
    d = 6                                   # came from the west
    for _ in range(4 * mask.size):
        found = False
        for k in range(8):
            nd = (d + 6 + k) % 8            # start looking behind-left and sweep round
            nxt = (cur[0] + _N8[nd][0], cur[1] + _N8[nd][1])
            if inside(nxt):
                cur, d, found = nxt, nd, True
                out.append([float(cur[0]), float(cur[1])])
                break
        if not found or (len(out) > 3 and cur == start):
            break
    return out


@dataclass
class Region:
    pts: list[list[float]]
    area_px: float
    cx: float
    cy: float
    w: float
    h: float
    enclosed: bool
    crop: Any = None
    role: str = "stage"
    role_from: str = "layout"       # layout | agreed | model | layout·disputed
    model_says: str | None = None   # what the model said, kept even when overruled
    label: str | None = None
    fit: dict[str, Any] = field(default_factory=dict)


def trace(data: bytes) -> tuple[list[Region], tuple[int, int], Any]:
    """Every shape the lines enclose, biggest first."""
    a, pil = _load(data)
    h, w = a.shape
    ink = _ink(a)
    closed = _dilate(ink, max(1, min(h, w) // 300))
    # the regions the drawing encloses = background components that do not reach the edge
    lab, comps = _label(~closed)
    keep = [c for c in comps if not c["border"] and c["n"] >= MIN_AREA_FRAC * h * w]
    # …plus anything drawn SOLID, which is one blob of ink rather than an outline
    lab2, comps2 = _label(closed)
    solid = [c for c in comps2 if c["n"] >= MIN_AREA_FRAC * h * w * 3 and not c["border"]]

    out: list[Region] = []
    for src_lab, cs, enclosed in ((lab, keep, True), (lab2, solid, False)):
        for c in cs:
            m = src_lab == c["id"]
            pts = _boundary(m)
            if len(pts) < 12:
                continue
            ys, xs = np.nonzero(m)
            out.append(Region(pts=pts, area_px=float(c["n"]),
                              cx=float(xs.mean()), cy=float(ys.mean()),
                              w=float(xs.max() - xs.min() + 1),
                              h=float(ys.max() - ys.min() + 1),
                              enclosed=enclosed))
    # EVERY SHAPE IS FOUND TWICE and only one of them is the shape. A closed outline
    # gives an ENCLOSED region (its interior — what the drawing means) and an INK region
    # (the loop of stroke itself, traced up one side and back down the other). Both are
    # real components; the interior is the object. So the ink twin is dropped wherever
    # it covers the same ground, and kept only where there is no interior at all —
    # something drawn solid rather than outlined.
    out.sort(key=lambda r: (-int(r.enclosed), -r.area_px))
    kept: list[Region] = []
    for r in out:
        if any(_overlap(r, k) > 0.45 for k in kept):
            continue
        kept.append(r)
    kept.sort(key=lambda r: -r.area_px)
    out = kept[:MAX_REGIONS]
    for r in out:
        r.crop = _crop(pil, r)
    return out, (w, h), pil


def _overlap(a: Region, b: Region) -> float:
    """Bounding-box intersection over the smaller box — asymmetric on purpose: a
    stroke loop is slightly BIGGER than the interior it encloses, so IoU understates
    the match and both twins survive."""
    ax0, ax1 = a.cx - a.w / 2, a.cx + a.w / 2
    ay0, ay1 = a.cy - a.h / 2, a.cy + a.h / 2
    bx0, bx1 = b.cx - b.w / 2, b.cx + b.w / 2
    by0, by1 = b.cy - b.h / 2, b.cy + b.h / 2
    iw = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    ih = max(0.0, min(ay1, by1) - max(ay0, by0))
    small = max(1.0, min(a.w * a.h, b.w * b.h))
    return (iw * ih) / small


def _crop(pil, r: Region):
    """The region on its own, with a little room round it — a VLM asked about a whole
    plan answers about the whole plan."""
    pad = max(8, int(0.12 * max(r.w, r.h)))
    box = (int(max(0, r.cx - r.w / 2 - pad)), int(max(0, r.cy - r.h / 2 - pad)),
           int(min(pil.size[0], r.cx + r.w / 2 + pad)),
           int(min(pil.size[1], r.cy + r.h / 2 + pad)))
    if box[2] - box[0] < 8 or box[3] - box[1] < 8:
        return pil.convert("RGB")
    return pil.crop(box).convert("RGB")


# ============================================================================
# 2 · THE FIT — the Python mirror of the pad's. Contract: SOLIDS.md
# ============================================================================
FIT_TOL_FRAC = 0.006     # of the image's long edge: a photograph is noisier than a pointer
ARC_MIN_SWEEP = 0.30     # ~17°, below which a straight is the truer story
ARC_MAX_SWEEP = 2.97     # ~170°, beyond which an arc is split rather than trusted


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _resample(pts, step):
    if len(pts) < 2:
        return list(pts)
    out = [list(pts[0])]
    carry = 0.0
    for i in range(1, len(pts)):
        a, b = out[-1], pts[i]
        d = _dist(a, b)
        while carry + d >= step and d > 1e-9:
            t = (step - carry) / d
            a = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
            out.append(a)
            d = _dist(a, b)
            carry = 0.0
        carry += d
    if _dist(out[-1], pts[-1]) > step * 0.35:
        out.append(list(pts[-1]))
    return out


def _rdp_idx(P, tol, closed):
    """A CLOSED LOOP HAS TO BE CUT FIRST: run plain RDP on a chain whose two ends are
    the same point and the base segment has zero length, so every perpendicular distance
    is zero and the whole shape reduces to one vertex."""
    keep = {0, len(P) - 1}
    stack = []
    if closed and len(P) > 3:
        far, fd = 1, -1.0
        for i in range(1, len(P) - 1):
            d = _dist(P[i], P[0])
            if d > fd:
                fd, far = d, i
        keep.add(far)
        stack = [(0, far), (far, len(P) - 1)]
    else:
        stack = [(0, len(P) - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        A, B = P[a], P[b]
        ax, ay = B[0] - A[0], B[1] - A[1]
        L = math.hypot(ax, ay) or 1.0
        worst, wi = -1.0, -1
        for i in range(a + 1, b):
            px, py = P[i][0] - A[0], P[i][1] - A[1]
            d = abs(px * ay - py * ax) / L
            if d > worst:
                worst, wi = d, i
        if worst > tol:
            keep.add(wi)
            stack += [(a, wi), (wi, b)]
    return sorted(keep)


def _circle(run):
    """Kåsa algebraic fit, solved by Cramer."""
    n = len(run)
    if n < 3:
        return None
    Sx = Sy = Sxx = Syy = Sxy = Sxz = Syz = Sz = 0.0
    for x, y in run:
        z = x * x + y * y
        Sx += x; Sy += y; Sxx += x * x; Syy += y * y; Sxy += x * y
        Sxz += x * z; Syz += y * z; Sz += z
    M = [[Sxx, Sxy, Sx], [Sxy, Syy, Sy], [Sx, Sy, float(n)]]
    V = [-Sxz, -Syz, -Sz]

    def det(m):
        return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
                - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))

    D0 = det(M)
    if abs(D0) < 1e-9:
        return None
    def col(k):
        return [[V[i] if j == k else M[i][j] for j in range(3)] for i in range(3)]
    D, E, F = det(col(0)) / D0, det(col(1)) / D0, det(col(2)) / D0
    cx, cy = -D / 2, -E / 2
    r2 = cx * cx + cy * cy - F
    if r2 <= 0:
        return None
    return (cx, cy), math.sqrt(r2)


def _sweep(run, c, r):
    total, sign = 0.0, 0
    for i in range(1, len(run)):
        a0 = math.atan2(run[i - 1][1] - c[1], run[i - 1][0] - c[0])
        a1 = math.atan2(run[i][1] - c[1], run[i][0] - c[0])
        d = a1 - a0
        while d > math.pi:
            d -= 2 * math.pi
        while d < -math.pi:
            d += 2 * math.pi
        if d == 0:
            continue
        s = 1 if d > 0 else -1
        if sign == 0:
            sign = s
        elif s != sign:
            return None                      # not monotonic — not an arc
        total += d
    return total


def _bulge(p0, p1, c, r, sweep):
    """The one definition: signed sagitta over half-chord. Positive bows toward
    (-dy, dx) of the chord — the same handedness the pad uses, so a bulge means the
    same thing on both wires."""
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    chx, chy = p1[0] - p0[0], p1[1] - p0[1]
    cl = math.hypot(chx, chy)
    if cl < 1e-6:
        return 0.0
    d = cl / 2
    nx, ny = -chy / cl, chx / cl
    tx, ty = mx - c[0], my - c[1]
    tl = math.hypot(tx, ty) or 1.0
    far = abs(sweep) > math.pi              # a major arc keeps the far side
    sg = -1.0 if far else 1.0
    ax = c[0] + (tx / tl) * r * sg
    ay = c[1] + (ty / tl) * r * sg
    return round(((ax - mx) * nx + (ay - my) * ny) / d, 4)


def fit(pts, long_edge: float, closed: bool = True) -> dict[str, Any]:
    """Polyline → vertices and true arcs. Mirrors the pad's five steps; see SOLIDS.md."""
    tol = max(1.5, FIT_TOL_FRAC * long_edge)
    P = _resample([p for p in pts], max(2.0, tol * 0.55))
    if len(P) < 3:
        return {"verts": [], "bulges": [], "closed": False, "arcs": 0, "raw": len(pts)}
    work = P + [list(P[0])] if closed else P
    keys = _rdp_idx(work, tol, closed)
    verts: list[list[float]] = []
    bulges: list[float] = []
    arcs = 0
    a = 0
    while a < len(keys) - 1:
        hit = None
        for b in range(min(len(keys) - 1, a + 8), a + 1, -1):
            run = work[keys[a]:keys[b] + 1]
            if len(run) < 4:
                continue
            f = _circle(run)
            if not f:
                continue
            c, r = f
            if r > 60 * tol or r < tol * 0.8:
                continue
            if max(abs(_dist(p, c) - r) for p in run) > tol:
                continue
            sw = _sweep(run, c, r)
            if sw is None or abs(sw) < ARC_MIN_SWEEP:
                continue
            bg = _bulge(work[keys[a]], work[keys[b]], c, r, sw)
            # AND IT HAS TO BE VISIBLY CURVED: a jittery straight fits a circle of
            # enormous radius perfectly well, and without this a photographed stage edge
            # comes back as three gentle arcs of 300 m radius — a good fit and a lie.
            if abs(bg) * _dist(work[keys[a]], work[keys[b]]) / 2 < max(tol * 1.6, 1.5):
                continue
            hit = (b, c, r, sw, bg)
            break
        if hit:
            b, c, r, sw, bg = hit
            if abs(sw) > ARC_MAX_SWEEP:
                mid = (keys[a] + keys[b]) // 2
                for i0, i1 in ((keys[a], mid), (mid, keys[b])):
                    run = work[i0:i1 + 1]
                    f2 = _circle(run) or (c, r)
                    sw2 = _sweep(run, f2[0], f2[1]) or sw / 2
                    verts.append(list(work[i0]))
                    bulges.append(_bulge(work[i0], work[i1], f2[0], f2[1], sw2))
                    arcs += 1
            else:
                verts.append(list(work[keys[a]]))
                bulges.append(bg)
                arcs += 1
            a = b
        else:
            verts.append(list(work[keys[a]]))
            bulges.append(0.0)
            a += 1
    if not closed:
        verts.append(list(work[keys[-1]]))
    else:
        bulges = bulges[:len(verts)] + [0.0] * max(0, len(verts) - len(bulges))
    return {"verts": verts, "bulges": bulges, "closed": bool(closed),
            "arcs": arcs, "raw": len(pts), "tol_px": round(tol, 2)}


def area_of(verts, bulges, closed) -> float:
    """Shoelace over the chords plus each arc's circular segment — an arc contributes
    the area an arc has rather than the area of its chord."""
    if len(verts) < 2:
        return 0.0
    a = 0.0
    n = len(verts)
    last = n if closed else n - 1
    for i in range(n):
        p, q = verts[i], verts[(i + 1) % n]
        a += p[0] * q[1] - q[0] * p[1]
    a = abs(a / 2)
    for i in range(last):
        b = bulges[i] if i < len(bulges) else 0.0
        if not b:
            continue
        p, q = verts[i], verts[(i + 1) % n]
        c = _dist(p, q)
        d = c / 2
        sag = b * d
        r = abs((d * d + sag * sag) / (2 * sag))
        th = abs(4 * math.atan(b))
        seg = r * r * (th - math.sin(th)) / 2
        a += seg if b > 0 else -seg
    return abs(a)


# ============================================================================
# 3 · THE MODEL — asked only what it is good at
# ============================================================================
_VLM: dict[str, Any] = {"proc": None, "model": None, "err": ""}

ROLE_WORDS = {
    "stage": "stage", "deck": "stage", "riser": "stage", "platform": "stage",
    "thrust": "stage", "floor": "stage", "rostrum": "stage",
    "led": "led", "screen": "wall", "projection": "wall", "wall": "wall",
    "cyc": "wall", "backdrop": "wall", "surface": "wall",
    "seating": "audience", "audience": "audience", "crowd": "audience",
    "truss": "other", "other": "other",
}


def _vlm():
    """Loaded on first use, not at import: this service must start in a second on a
    machine that will never be asked to read a picture."""
    if _VLM["model"] or _VLM["err"]:
        return _VLM
    try:
        local = os.path.isdir(MODEL)
        _VLM["proc"] = AutoProcessor.from_pretrained(MODEL, local_files_only=local)
        _VLM["model"] = AutoModelForImageTextToText.from_pretrained(
            MODEL, device_map="auto", local_files_only=local)
        _VLM["model"].eval()
    except Exception as exc:                                 # pragma: no cover
        _VLM["err"] = f"{type(exc).__name__}: {exc}"
    return _VLM


def _reply_text(message: Any) -> str:
    """Normalize OpenAI-compatible replies from both SmolVLM and Qwen.

    Qwen may return its visible answer as a string, as typed content blocks, or
    after a reasoning field.  The vision reader needs the visible answer only;
    callers then constrain it to the small role vocabulary below.
    """
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                text = part.get("text") or part.get("content")
                if isinstance(text, str):
                    parts.append(text)
        if parts:
            return " ".join(parts).strip()
    # Keep a diagnostic fallback for models that emitted thought but no final
    # answer. It lets the vocabulary matcher recover a concise answer while
    # making the missing final text visible on /health.
    thought = message.get("reasoning_content") or message.get("reasoning")
    return thought.strip() if isinstance(thought, str) else ""


def ask(image, question: str, limit: int = 48) -> str:
    """One closed question about one picture. Short answers on purpose — the longer the
    leash, the more a 500M model narrates instead of answering."""
    if BACKEND == "lmstudio":
        model = _lmstudio_model()
        if not model:
            return ""
        try:
            buf = io.BytesIO()
            image.convert("RGB").save(buf, format="PNG")
            body = json.dumps({
                "model": model,
                "temperature": 0,
                "max_tokens": limit,
                # Qwen's default thinking mode can consume a 24-token budget
                # before it emits the one-word answer this adapter requests.
                "reasoning_effort": "none",
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {
                        "url": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
                    }},
                ]}],
            }).encode("utf-8")
            req = urlrequest.Request(f"{LM_STUDIO_URL}/chat/completions", data=body,
                                     headers={"Content-Type": "application/json"}, method="POST")
            with urlrequest.urlopen(req, timeout=45) as response:
                reply = json.load(response)
            message = reply.get("choices", [{}])[0].get("message", {})
            text = _reply_text(message)
            _VLM["last_reply"] = {"model": model, "content": message.get("content"),
                                  "reasoning": message.get("reasoning_content"), "text": text}
            return text
        except (KeyError, OSError, ValueError, urlerror.URLError):
            return ""
    v = _vlm()
    if not v["model"]:
        return ""
    try:
        msgs = [{"role": "user", "content": [{"type": "image"},
                                            {"type": "text", "text": question}]}]
        prompt = v["proc"].apply_chat_template(msgs, add_generation_prompt=True)
        inputs = v["proc"](text=prompt, images=[image], return_tensors="pt")
        inputs = {k: (t.to(v["model"].device) if hasattr(t, "to") else t)
                  for k, t in inputs.items()}
        with torch.no_grad():
            out = v["model"].generate(**inputs, max_new_tokens=limit, do_sample=False)
        text = v["proc"].batch_decode(out, skip_special_tokens=True)[0]
        return text.split("Assistant:")[-1].strip()
    except Exception as exc:                                 # pragma: no cover
        _VLM["err"] = f"{type(exc).__name__}: {exc}"
        return ""


def _pick(answer: str, words: dict[str, str]) -> str | None:
    low = (answer or "").lower()
    for k, v in words.items():
        if k in low:
            return v
    return None


# ---------------------------------------------------------------------- layout --
def _prior(r: Region, W: int, H: int, projection: str) -> str:
    """WHAT THE LAYOUT ALONE SAYS. This runs whether or not the model does, for two
    reasons: it is the answer when there is no torch on the machine, and it is the tie
    break when the model says something outside the vocabulary. A stage plan has a
    grammar — upstage is up, the audience is downstage, and a wall is long and thin —
    and reading that grammar is not guessing, it is the same inference a person makes
    before they read any label."""
    ratio = max(r.w, r.h) / max(1.0, min(r.w, r.h))
    depth = r.cy / max(1.0, H)                # 0 = upstage, 1 = downstage
    frac = r.area_px / max(1.0, W * H)
    if projection == "elevation":
        return "wall" if ratio > 2.2 else "stage"
    # DOWNSTAGE FIRST. A seating block is long, thin AND at the bottom of the page, so
    # asking about the ratio before the depth called it a wall — and a wall in the
    # audience is a wall in the wrong place.
    if depth > 0.70 and frac > 0.015:
        return "audience"
    if ratio > 3.4 and depth < 0.45:
        return "led"                          # long, thin and upstage
    if ratio > 3.4:
        return "wall"
    return "stage"


# ============================================================================
# 4 · ARBITRATION — and why the model does not simply win
#
# MEASURED, not assumed. Asked to name three obviously different traced regions from a
# stage plan — a 300x270 thrust, a 430x60 band at the foot of the page, a 590x40 band at
# the top — SmolVLM2-500M answered:
#
#     six-way list      stage      · stage      · stage
#     binary either/or  seating    · seating    · seating
#     "describe it"     U-shape    · rectangle, circle, triangle · L-shape
#     plan or elevation "front elevation"   (it is a plan)
#     how many shapes   "2"                 (there are three)
#
# The answers are CONSTANT across visibly different inputs, and they track the last
# option offered rather than the picture. That is not a prompt that needs more work; at
# 500M on line art it is position bias, and a constant answer carries no information
# however confidently it is phrased.
#
# So the model is wired in exactly as asked and its answers are USED, but they have to
# earn it:
#
#   1 A DECLARATION BEATS EVERYTHING. The reference board already asks for each image's
#     role — plan, elevation, photo, drawing. Somebody said so; nothing here overrules it.
#   2 THE MODEL IS TESTED ON THE DRAWING IN FRONT OF IT. If its answers across the
#     traced regions are all the same while their shapes plainly are not, this drawing
#     gets `signal: false`, the answers are discarded, and the plan SAYS the model gave
#     no signal. A service that can detect its own degenerate case is worth more than one
#     that cannot.
#   3 WHERE IT VARIES, IT COUNTS — and where it agrees with the geometry, confidence
#     rises. Every op records which decided: `layout`, `model`, or `agreed`.
#
# `VISION_MODEL` swaps the checkpoint with no other change. A 2.2B SmolVLM2, an Idefics3
# or a hosted VLM will start winning arbitrations on its own merits, and this file will
# not need editing for that to happen — which is the whole reason the arbitration is
# explicit rather than baked into a prompt.
# ============================================================================
@dataclass
class Read:
    projection: str
    regions: list[Region]
    size: tuple[int, int]
    engine: str
    signal: bool = False            # did the model pass its calibration probe
    calibration: float | None = None
    notes: list[str] = field(default_factory=list)
    asked: list[str] = field(default_factory=list)
    suggestions: list[dict[str, Any]] = field(default_factory=list)
    ocr_rows: list[dict[str, Any]] = field(default_factory=list, repr=False)


# The one question this model demonstrably CAN answer about a traced region. Its ground
# truth is the aspect ratio, which the tracer knows exactly — so it is a calibration
# probe: it measures whether the model is looking at the picture at all, on this drawing,
# for the price of one question per shape. Measured on the test plan: 3 of 3.
CAL_Q = ("Is this shape a long thin strip, or a big block? "
         "Answer one word: strip or block.")

# and the one it cannot: what the shape IS. Binary, because a six-way list came back
# constant. See § 4.
_RIVAL = {
    "stage": "In a stage plan, is this shape the stage platform the performers stand on, "
             "or the seating area for the audience? Answer one word: stage or seating.",
    "led":   "In a stage plan, is this long thin rectangle a video screen at the back of "
             "the stage, or a row of seats? Answer one word: screen or seats.",
    "wall":  "In a stage plan, is this a wall or screen the performers stand in front of, "
             "or the floor they stand on? Answer one word: wall or floor.",
    "audience": "In a stage plan, is this the seating area for the audience, or the stage "
                "platform? Answer one word: seating or stage.",
}
_ANSWER_WORDS = {"stage": "stage", "floor": "stage", "platform": "stage",
                 "screen": "led", "led": "led", "video": "led",
                 "wall": "wall", "backdrop": "wall",
                 "seating": "audience", "seats": "audience", "audience": "audience"}

# A crop can contain a written label (for example, "LED") that the geometry prior
# cannot see.  Ask the vision model to identify that label before using the old
# role-specific tie-breaker.  The response stays deliberately bounded so it can
# be parsed by both Qwen and the smaller fallback model.
_ROLE_LABEL_Q = (
    "Classify the outlined object in this stage-plan crop. If there is a written "
    "label, follow it. Reply with exactly one word: LED, STAGE, WALL, or AUDIENCE."
)

# THE POLICY, AND IT IS A CONSTANT SO IT CAN BE ARGUED WITH.
#
# Off: the model corroborates or dissents, and the GEOMETRY decides. On: a calibrated
# model may overrule it. It ships off because it was measured off — on the test plan
# SmolVLM2-500M passed the geometry probe 3/3 and then named all three shapes wrongly,
# which is exactly the shape of the thing to be careful about: perceiving a picture and
# knowing what a thrust is are different claims, and passing the first does not license
# the second. A dissent is not thrown away — it lands on the op and in the plan's risks,
# where one click flips the role. Turn this on with a checkpoint that earns it.
TRUST_MODEL_ROLES = os.environ.get("VISION_TRUST_ROLES") == "1"
# 5.8's interactive reference workflow favours useful, clearly marked provisional
# geometry over silently discarding a capable vision model's semantic read. Set this
# to 0 for strict tracing-only review.
APPROXIMATE_SEMANTICS = os.environ.get("VISION_APPROXIMATE", "1") != "0"


def _probe_projection(pil) -> tuple[str | None, list[str]]:
    """Asked twice, differently. One answer from a model this size is a coin; two that
    agree is a coin landing the same way twice, and two that disagree is an honest
    `don't know` — which is a better thing to put in a plan than either answer."""
    a = ask(pil, "Is this technical drawing a top-down plan view seen from above, or a "
                 "front elevation seen from the side? Answer one word: plan or elevation.")
    b = ask(pil, "Is this drawing looking DOWN at the floor, or STRAIGHT AT a wall? "
                 "Answer one word: down or wall.")
    pa = "elevation" if "elevat" in a.lower() else ("plan" if "plan" in a.lower() else None)
    pb = "elevation" if "wall" in b.lower() else ("plan" if "down" in b.lower() else None)
    return (pa if pa and pa == pb else None), [a, b]


def _calibrate(regions: list[Region]) -> tuple[float | None, str]:
    """Is the model looking at these pixels? Scored against something already known."""
    truth = [max(r.w, r.h) / max(1.0, min(r.w, r.h)) > 3.4 for r in regions]
    if len(set(truth)) < 2:
        return None, "no calibration possible — every traced shape has the same proportions"
    ok = 0
    for r, t in zip(regions, truth):
        a = ask(r.crop, CAL_Q).lower()
        said = True if "strip" in a else (False if "block" in a else None)
        if said is not None and said == t:
            ok += 1
    score = ok / len(regions)
    return score, (f"the model placed {ok} of {len(regions)} shapes correctly as strip or "
                   f"block, so it {'is' if score >= 0.75 else 'is not reliably'} reading "
                   f"the picture")


def read(data: bytes, hint_role: str = "", want_model: bool = True) -> Read | None:
    """Trace a reference, then arbitrate what each shape is."""
    if not traceable():
        return None
    regions, (W, H), pil = trace(data)
    if not regions:
        return Read(projection="plan", regions=[], size=(W, H), engine="tracer",
                    notes=["nothing in that image traced as a shape — it may be a "
                           "photograph of a room rather than a drawing of one"])

    use_model = want_model and available()
    notes: list[str] = []
    asked: list[str] = []

    # ---- 1 · the projection. A DECLARATION BEATS EVERYTHING. ----
    projection = "plan"
    if hint_role in ("plan", "elevation"):
        projection = hint_role
        notes.append(f"projection declared on the reference board as {hint_role}")
    elif use_model:
        got, raw = _probe_projection(pil.convert("RGB"))
        asked += raw
        if got:
            projection = got
            notes.append(f"projection read as {got} — the model said so twice")
        else:
            notes.append("projection assumed to be a plan — the model gave two different "
                         f"answers ({raw[0][:16]!r} / {raw[1][:16]!r}), so it decided nothing")
    else:
        notes.append("projection assumed to be a plan — no model to ask, and the board "
                     "did not say")

    # ---- 2 · the geometry's own reading, which is deterministic ----
    for r in regions:
        r.role, r.role_from = _prior(r, W, H, projection), "layout"
        r.fit = fit(r.pts, max(W, H), closed=True)

    # ---- 3 · the model: calibrated, then heard ----
    cal: float | None = None
    if use_model:
        cal, cal_note = _calibrate(regions)
        notes.append(cal_note)
        for r in regions:
            labelled_raw = ask(r.crop, _ROLE_LABEL_Q)
            said = _pick(labelled_raw, _ANSWER_WORDS)
            # The older binary prompt is still useful when the model cannot name
            # the object directly, but it must not prevent a clear LED/stage label
            # from overriding the geometry's initial guess.
            raw = labelled_raw
            if not said:
                raw = ask(r.crop, _RIVAL.get(r.role, _RIVAL["stage"]))
                said = _pick(raw, _ANSWER_WORDS)
            asked.append(raw)
            r.model_says = said
            if not said or said == r.role:
                if said:
                    r.role_from = "agreed"
                continue
            # In a front elevation, a tall narrow outlined panel that Qwen calls LED
            # is unambiguous enough to promote.  This preserves the conservative
            # policy for all other model-only disagreements.
            if (said == "led" and projection == "elevation" and
                    r.h / max(1.0, r.w) > 1.35):
                r.role, r.role_from = "led", "model·panel"
                continue
            if APPROXIMATE_SEMANTICS and said in ("stage", "led", "wall"):
                r.role, r.role_from = said, "model·provisional"
                continue
            if TRUST_MODEL_ROLES and cal is not None and cal >= 0.75:
                r.role, r.role_from = said, "model"
            else:
                # THE DISSENT IS KEPT, not silently dropped: it rides on the op and into
                # the plan's risks, where one click changes the role.
                r.role_from = "layout·disputed"
        agreed = sum(1 for r in regions if r.role_from == "agreed")
        disputed = sum(1 for r in regions if r.role_from == "layout·disputed")
        if disputed:
            notes.append(f"the model disagreed with the layout on {disputed} of "
                         f"{len(regions)} shapes; the layout decided and the disagreement "
                         f"is on the plan for you to overrule")
        if agreed:
            notes.append(f"the model and the layout agreed on {agreed} of {len(regions)}")
    if use_model and _VLM["err"]:
        notes.append(f"the model stopped answering: {_VLM['err'][:90]}")

    engine = "smolvlm2" if use_model else ("tracer" if traceable() else "off")
    ocr_rows = _ocr_rows(data)
    suggestions = semantic_label_suggestions(data, regions, (W, H), ocr_rows)
    # Printed or handwritten role labels are direct semantic evidence, unlike the
    # geometry prior. A STAGE label has priority over a neighbouring LED label: in
    # an elevation the floor platform often sits immediately below the LED wall.
    for suggestion in suggestions:
        if (suggestion["role"] in ("led", "stage") and suggestion["highConfidence"] and
                suggestion["targetIndex"] is not None):
            region = regions[suggestion["targetIndex"] - 1]
            region.role, region.role_from = suggestion["role"], "label"
    return Read(projection=projection, regions=regions, size=(W, H), engine=engine,
                signal=bool(cal is not None and cal >= 0.75), calibration=cal,
                notes=notes, asked=asked, suggestions=suggestions, ocr_rows=ocr_rows)


def to_solid(r: Region, frame, W: int, H: int, projection: str,
             units_per_metre: float, idx: int) -> dict[str, Any] | None:
    """A traced region → a `solid` op body, in TAKE UNITS.

    The conversion is the frame's, not this file's: `geometry.Frame` is the one place
    that knows how a pixel becomes a take unit, and a second opinion about that is
    exactly what the rest of this service is arranged to avoid.
    """
    f = r.fit
    if len(f.get("verts", [])) < 2:
        return None
    front = projection == "elevation"
    ax, ay = r.cx, r.cy
    at = frame.take(ax, ay, view="elevation" if front else "plan")
    k = units_per_metre / frame.px_per_metre
    verts = [[round((p[0] - ax) * k, 2),
              round((-(p[1] - ay) if front else (p[1] - ay)) * k, 2)]
             for p in f["verts"]]
    # a mirrored plane mirrors its arcs, and a mirrored arc bows the other way
    bulges = [round((-b if front else b), 4) for b in f["bulges"]]
    role = r.role if r.role in ("stage", "wall", "led") else "stage"
    long_m = max(r.w, r.h) / frame.px_per_metre
    h_m = {"stage": 0.5, "wall": 6.0, "led": 4.0}[role]
    return {
        "role": role, "name": r.label,
        "plane": "front" if front else "floor",
        "closed": bool(f["closed"]) and len(verts) >= 2,
        "at": [round(at[0], 1), round(at[1], 1), round(at[2], 1)],
        "verts": verts, "bulges": bulges,
        "h": round(h_m * units_per_metre, 1),
        "base": 0.0,
        "thick": round(0.5 * units_per_metre, 1),
        "tile": {"w": round(0.5 * units_per_metre, 1),
                 "h": round(0.5 * units_per_metre, 1)} if role == "led" else None,
        "fit": {"raw": f["raw"], "verts": len(verts), "arcs": f["arcs"],
                "rms": None, "tol": round(f["tol_px"] / frame.px_per_metre, 3),
                "symmetric": False, "snapped": False, "traced": True,
                "role_from": r.role_from, "long_m": round(long_m, 2)},
        # the enclosed area, arcs included — the same figure the Scene Study will derive
        # off the built geometry, computed here so the plan can say it before anybody
        # accepts anything
        "metrics": {"area": round(area_of(f["verts"], f["bulges"], f["closed"])
                                  / (frame.px_per_metre ** 2), 2)} if f["closed"] else {},
        "srcId": f"ref{idx}",
    }
