"""AID3N drawing CONTENT for an LED wall — the `image` capability.

TWO ENGINES, ONE CONTRACT. This module is the router; the engines are beside it.

    drawthings   Z Image Turbo, generated locally by the Draw Things app over its
                 A1111-compatible HTTP API. Real diffusion, real pixels, no cloud.
                 See drawthings.py.
    qwen-svg     Qwen writes the frame as an SVG document and the panel rasterises
                 it. No diffusion model involved — see the section below.

`IMAGE_ENGINE` picks one; `auto` (the default) prefers Draw Things whenever it
answers and falls back to `qwen-svg` when it does not. That fallback is the point of
the arrangement rather than a hedge: Draw Things has to be running with its API
server switched on and a checkpoint loaded, and on the days it is not, a panel that
still makes something beats a panel that reports an error.

Every answer names the engine that produced it, so nothing downstream — and nobody
looking at a frame — has to guess which of the two drew it.

WHAT `qwen-svg` IS, AND WHAT IT IS HONESTLY NOT
-----------------------------------------------
LM Studio serves language and vision-language models: they read pictures and they
write text, and its API has no `/v1/images/generations` at all. `qwen/qwen3.8-27b` is
a TEXT model. So this engine cannot mean diffusion, and pretending otherwise would
put a fake in the Content Bin.

What Qwen can do is WRITE THE PICTURE. It is asked for one standalone SVG document
and the panel rasterises it at the wall's own pixel size. For this workspace that is
not a workaround, it is arguably the right medium:

  · What goes on these walls is very often procedural — gradients, sweeps, curtains,
    scan lines, colour fields, grids, test cards, abstract backdrops. That is the
    part of the content space SVG is actually good at.
  · It is resolution-independent, so the same prompt fills a 2 640 × 1 408 canvas
    and a 15 360 × 1 080 ribbon without resampling.
  · It arrives as text, which means it can be checked before it is rendered. A
    diffusion model hands you pixels you have to trust; this hands you a document
    this module can read, strip and refuse.

A DIFFUSION MODEL DID ARRIVE, and it went behind this same endpoint exactly as the
previous version of this note said it would: the panel asks AID3N for content and
does not care what drew it. Nothing in the panel changed but the badge.

THE SANITISER IS NOT OPTIONAL. What comes back is a document written by a model and
about to be rendered by a browser, which is the definition of untrusted markup. It
is parsed, stripped of everything executable or remote, and refused if it is not a
closed SVG. See `sanitise`.
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
from urllib import error as urlerror
from urllib import request as urlrequest

# One source of truth for where the models are, shared with the vision adapter so a
# machine that moved LM Studio off 4096 moves it once.
try:
    from vision import LM_STUDIO_URL
except Exception:                                            # pragma: no cover
    LM_STUDIO_URL = os.environ.get("LM_STUDIO_URL", "http://127.0.0.1:4096/v1")

ENGINE = "qwen-svg"          # this module's own engine; the router is `pick()` below

# ---------------------------------------------------------------------- routing --
try:
    import drawthings
except Exception:                                            # pragma: no cover
    drawthings = None
try:
    import prompt as promptmod
except Exception:                                            # pragma: no cover
    promptmod = None
try:
    import video as videomod
except Exception:                                            # pragma: no cover
    videomod = None

WANT = os.environ.get("IMAGE_ENGINE", "auto").strip().lower()


def engines() -> dict:
    """Every engine and whether it can run right now — what `/v1/image/health`
    reports. Both are named even when one is unavailable, because "which engine drew
    this" is a question somebody will ask about a frame later."""
    out = {}
    if drawthings is not None:
        ok, why, opts = drawthings.available()
        out["drawthings"] = {"ok": ok, "why": why,
                             "model": drawthings.loaded_model(opts) if ok else None,
                             "config": drawthings.config()}
    ok, m = available()
    out["qwen-svg"] = {"ok": ok, "why": "" if ok else m, "model": m if ok else None}
    # The video stage is not a third engine competing for `auto`; it is a stage that
    # runs AFTER an image engine. It is reported here because the panel has to know
    # whether to offer the toggle at all, and if not, precisely why not.
    if videomod is not None:
        out["wan-i2v"] = videomod.state()
    return out


def pick(want: str | None = None) -> tuple[str, str]:
    """(engine, why). `auto` prefers real diffusion and falls back to the writer."""
    want = (want or WANT or "auto").strip().lower()
    st = engines()
    if want in st:
        return (want, "pinned") if st[want]["ok"] else (want, st[want]["why"])
    if "drawthings" in st and st["drawthings"]["ok"]:
        return "drawthings", "Draw Things is answering"
    if st["qwen-svg"]["ok"]:
        dt = st.get("drawthings", {}).get("why", "the Draw Things engine is not installed")
        return "qwen-svg", f"falling back — {dt}"
    return "none", st["qwen-svg"]["why"]


def generate(brief: str, w: int, h: int, variant: int | None = None,
             refine: bool = False, want: str | None = None,
             steps: int | None = None, cfg: float | None = None,
             kind: str = "image", motion: str = "", frames: int | None = None,
             fps: int | None = None, keyframe: bytes | None = None) -> dict:
    """THE PIPELINE, end to end, in one place: expand the prompt if asked, choose an
    engine, generate, and hand back what happened. Every step is reported — which
    prompt was used, which engine ran, why it was chosen — because a pipeline whose
    decisions are invisible is one nobody can debug."""
    exp = (promptmod.expand(brief) if (refine and promptmod is not None)
           else {"used": False, "prompt": (brief or "").strip(), "model": None,
                 "why": "" if not refine else "the prompt module is not installed"})
    final = exp["prompt"] or (brief or "").strip()
    if (kind or "image").strip().lower() == "video":
        out = _video(final, w, h, variant, motion, frames, fps, keyframe, steps, cfg)
        why = out.pop("chose", "")
    else:
        which, why = pick(want)
        if which == "drawthings":
            out = drawthings.draw(final, w, h, seed=variant, steps=steps, cfg=cfg)
        elif which == "qwen-svg":
            out = draw(final, w, h, variant)
        else:
            out = {"ok": False, "engine": "none", "why": why, "ms": 0}
    out["kind"] = "video" if (kind or "image").strip().lower() == "video" else "image"
    out["chose"] = why
    out["prompt"] = brief
    out["promptUsed"] = final
    out["refined"] = exp
    return out

def _video(final: str, w: int, h: int, variant: int | None, motion: str,
           frames: int | None, fps: int | None, keyframe: bytes | None,
           steps: int | None, cfg: float | None) -> dict:
    """THE TWO-STAGE PASS. Stage one is a still and stage two animates it, so a failure
    in either has to say WHICH — "video failed" after four minutes is not a diagnosis.

    There is no `qwen-svg` fallback here and there should not be: an SVG document does
    not animate, and quietly handing back a still when someone asked for a clip would
    be the worst answer available."""
    if videomod is None:
        return {"ok": False, "engine": "wan-i2v", "ms": 0, "stage": "setup",
                "chose": "", "why": "the video stage is not installed"}
    ok, why, _ = videomod.available()
    if not ok:
        return {"ok": False, "engine": "wan-i2v", "ms": 0, "stage": "setup",
                "chose": "", "why": why, "config": videomod.config()}

    # STAGE ONE. A keyframe handed in — a still the user already generated and liked —
    # skips this entirely, which is both cheaper and how this gets used in practice
    # once someone is actually working rather than exploring.
    key, kfrom = keyframe, "supplied"
    if not key:
        if drawthings is None:
            return {"ok": False, "engine": "wan-i2v", "ms": 0, "stage": "keyframe",
                    "chose": "", "why": "there is no image engine to draw the first frame"}
        shot = drawthings.draw(final, w, h, seed=variant, steps=steps, cfg=cfg,
                               long_edge=videomod.LONG_EDGE, grid=videomod.GRID)
        if not shot.get("ok"):
            shot.update(engine="wan-i2v", stage="keyframe", chose="",
                        why="the first frame could not be drawn — " + shot.get("why", ""))
            return shot
        key, kfrom = base64.b64decode(shot["png"]), "generated"

    # STAGE TWO. The motion brief is optional and falls back to the picture's own
    # prompt, because "what it looks like" is a usable description of how it should
    # move and an empty prompt is not.
    out = videomod.animate(key, (motion or "").strip() or final,
                           frames=frames, fps=fps, seed=variant,
                           asked={"w": int(w), "h": int(h)})
    out["stage"] = "animate" if not out.get("ok") else "done"
    out["keyframe"] = kfrom
    out["motion"] = (motion or "").strip()
    out["chose"] = f"Wan animated a {kfrom} first frame"
    return out


# WHICH MODEL DRAWS. Not the vision preference order — that one prefers whatever can
# look at a picture, and this asks a model to WRITE one. Biggest capable text model
# first; `IMAGE_MODEL` pins one.
PREFER = ("qwen3.8", "qwen3", "qwen2.5", "qwen", "llama", "mistral")
PINNED = os.environ.get("IMAGE_MODEL", "")

# Measured on qwen/qwen3.8-27b on this machine, and it scales with how much you ask
# for: a plain frame ("flat black field, one centred magenta bar") lands in ~12 s, a
# dense one ("light curtain, scan lines, caustics") takes 45–70 s and 1 200–1 900
# completion tokens. A budget of 1 800 truncated one mid-attribute and the document
# came back unclosed, which is why this is what it is — and why `sanitise` refuses an
# unclosed document rather than trying to repair it.
MAX_TOKENS = int(os.environ.get("IMAGE_MAX_TOKENS", "5000"))
TIMEOUT = float(os.environ.get("IMAGE_TIMEOUT", "300"))

SYSTEM = (
    "You generate CONTENT FOR AN LED VIDEO WALL as ONE standalone SVG document.\n"
    "OUTPUT ONLY the SVG: start with <svg, end with </svg>. No markdown fence, no "
    "commentary, no explanation.\n"
    "Rules:\n"
    "- Use viewBox=\"0 0 W H\" for the canvas you are given, and set width and height to match.\n"
    "- Fill the frame edge to edge. No white margins, no letterboxing, no visible page.\n"
    "- No <script>, no <foreignObject>, no <image>, no <use>, no <a>, no external href, "
    "no web fonts. Reference your own gradients and filters with url(#id) as normal.\n"
    "- Gradients, shapes, paths, filters, masks and opacity only.\n"
    "- BE ECONOMICAL: at most 60 elements. Bold stage-scale forms that read from 30 "
    "metres, not fine detail — this is going on a wall, not a page.\n"
    "- Respect the direction words in the prompt: vertical means vertical, horizontal "
    "means horizontal."
)

# ------------------------------------------------------------------ the model --
def _models() -> list[str]:
    try:
        with urlrequest.urlopen(f"{LM_STUDIO_URL}/models", timeout=1.5) as r:
            rows = json.load(r).get("data", [])
    except (OSError, ValueError, urlerror.URLError):
        return []
    return [row.get("id", "") for row in rows if row.get("id")]


def model() -> str | None:
    """The model that will draw, or None — which is a NAMED state on the response and
    not an exception, for the same reason `/health` names a missing credential."""
    ids = _models()
    if not ids:
        return None
    if PINNED:
        return PINNED if PINNED in ids else None
    for want in PREFER:
        hit = next((m for m in ids if want in m.lower()), None)
        if hit:
            return hit
    return None


def available() -> tuple[bool, str]:
    if not _models():
        return False, f"no model server answering on {LM_STUDIO_URL}"
    m = model()
    if not m:
        return False, ("the model server is up but none of its models is one this can "
                       "draw with" + (f" (IMAGE_MODEL={PINNED} is not loaded)" if PINNED else ""))
    return True, m


# --------------------------------------------------------------- the sanitiser --
# Everything that can execute or reach off the machine. `on*` covers the event
# attributes; the href pair covers <a> and <use> pointing anywhere at all.
_KILL_TAGS = ("script", "foreignObject", "iframe", "image", "audio", "video", "use", "a")
_KILL_ATTR = re.compile(r"\s(?:on\w+|xlink:href|href|xmlns:xlink)\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
                        re.IGNORECASE)
# A url() that points OFF the document, replaced whole by the valid SVG value `none`.
#
# THE `#` GUARD IS THE WHOLE POINT. `url(#bg)` is how every gradient, mask and filter
# in an SVG is referenced. The first version of this took out EVERY url() and then
# cheerfully reported "stripped: url() references" on a frame whose gradients had all
# just been deleted — a silent downgrade of every picture, reported as a success.
#
# The whitespace sits INSIDE the lookahead on purpose. With `url\s*\(\s*(?!["\']?#)`
# the engine backtracks `\s*` to zero and the guard passes on ` \'#f\'` — so a
# perfectly good internal reference written with a space still got neutralised. Inside
# the lookahead there is nothing to backtrack into.
# The quote may also arrive ENTITY-ENCODED — `url(&quot;#g&quot;)` is a legal way to
# write an internal reference inside a double-quoted attribute — and a guard that does
# not know that flattens a gradient and reports it as a strip. Same false positive as
# the spaced form above, one encoding further out.
_Q = r"""(?:["']|&quot;|&\#34;|&apos;|&\#39;)?"""
_STYLE_URL = re.compile(rf"""url\s*\((?!\s*{_Q}\#)[^)]*\)""", re.IGNORECASE)


def sanitise(svg: str) -> tuple[str, list[str]]:
    """Strip what must never render and report what was taken out. The report is
    returned rather than swallowed: a prompt that keeps producing stripped documents
    is a prompt problem, and the panel can only say so if it is told."""
    removed: list[str] = []
    for tag in _KILL_TAGS:
        pair = re.compile(rf"<{tag}\b[^>]*>.*?</{tag}\s*>", re.IGNORECASE | re.DOTALL)
        solo = re.compile(rf"<{tag}\b[^>]*/?>", re.IGNORECASE)
        svg, n1 = pair.subn("", svg)
        svg, n2 = solo.subn("", svg)
        if n1 + n2:
            removed.append(f"<{tag}> ×{n1 + n2}")
    svg, n = _KILL_ATTR.subn("", svg)
    if n:
        removed.append(f"link/event attributes ×{n}")
    svg, n = _STYLE_URL.subn("none", svg)
    if n:
        removed.append(f"external url() references ×{n}")
    # the xmlns has to survive the href sweep above, and it is what makes it an SVG
    if "xmlns=" not in svg:
        svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    return svg, removed


def extract(text: str) -> str | None:
    """The document, or None if the model did not finish one. A truncated SVG is NOT
    repaired: half a document renders as half a picture, and a half picture that
    reaches the Content Bin is worse than an error somebody can act on."""
    if not text:
        return None
    i = text.find("<svg")
    j = text.rfind("</svg>")
    if i < 0 or j < i:
        return None
    return text[i:j + 6]


# -------------------------------------------------------------------- drawing --
def draw(prompt: str, w: int, h: int, seed: int | None = None,
         temperature: float = 0.75) -> dict:
    """One frame. Returns a dict the endpoint hands straight back — including every
    failure, named, because a panel can only report what it is told."""
    t0 = time.time()
    ok, m = available()
    if not ok:
        return {"ok": False, "why": m, "engine": ENGINE, "model": None, "ms": 0}

    ask = (f"Prompt: {prompt.strip()}\nCanvas: {w} x {h} pixels"
           f" (aspect {w / h:.3f}).")
    if seed is not None:
        # not a diffusion seed — there is nothing deterministic to seed here. It is a
        # nudge in the text so a re-roll of the same prompt comes back different, and
        # it is named `variant` on the wire for exactly that reason.
        ask += f"\nVariant {seed}: take a different compositional approach to the same brief."
    body = json.dumps({
        "model": m,
        "temperature": temperature,
        "max_tokens": MAX_TOKENS,
        "reasoning_effort": "none",      # the budget is for the document, not for thinking
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": ask}],
    }).encode("utf-8")

    try:
        req = urlrequest.Request(f"{LM_STUDIO_URL}/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
        with urlrequest.urlopen(req, timeout=TIMEOUT) as r:
            reply = json.load(r)
    except urlerror.URLError as exc:
        return {"ok": False, "why": f"the model server did not answer: {exc.reason}",
                "engine": ENGINE, "model": m, "ms": int((time.time() - t0) * 1000)}
    except (OSError, ValueError) as exc:
        return {"ok": False, "why": f"{type(exc).__name__}: {exc}",
                "engine": ENGINE, "model": m, "ms": int((time.time() - t0) * 1000)}

    choice = (reply.get("choices") or [{}])[0]
    text = (choice.get("message") or {}).get("content") or ""
    usage = reply.get("usage") or {}
    ms = int((time.time() - t0) * 1000)
    svg = extract(text)
    if not svg:
        cut = choice.get("finish_reason") == "length"
        return {"ok": False, "engine": ENGINE, "model": m, "ms": ms,
                "why": ("the model ran out of budget before it closed the document — "
                        f"raise IMAGE_MAX_TOKENS (now {MAX_TOKENS}) or ask for something simpler"
                        if cut else
                        "the model did not return an SVG document"),
                "tokens": usage.get("completion_tokens")}
    svg, removed = sanitise(svg)
    return {"ok": True, "engine": ENGINE, "model": m, "ms": ms, "svg": svg,
            "w": w, "h": h, "bytes": len(svg.encode("utf-8")),
            "tokens": usage.get("completion_tokens"), "stripped": removed}
