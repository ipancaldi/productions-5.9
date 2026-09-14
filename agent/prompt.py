"""QWEN WRITING THE PROMPT, not the picture — the optional step 2 of the pipeline.

Qwen 3.8 27B in LM Studio cannot generate an image and this module does not pretend
otherwise. What a 27B model IS good at is turning a director's shorthand — "amber
caustics, moody" — into the kind of specific, comma-separated description a diffusion
model responds to, with the subject, the light, the palette, the medium and the
framing all actually said.

OFF BY DEFAULT, and that is a judgement worth stating. Expansion costs 10–15 s on top
of a Turbo generation that takes seconds, and a language model given a good brief can
talk it into a worse one — it adds adjectives, and adjectives are not free in a CLIP
or T5 embedding. So it is a per-request flag, the original prompt is always returned
alongside the expanded one, and the panel shows which was used.

IT NEVER FAILS THE JOB. If LM Studio is not running, or the model is not loaded, or
the reply is empty, the ORIGINAL prompt goes through unchanged and the reason rides
back in the metadata. A prompt refiner that can block an image pipeline is a worse
pipeline.
"""
from __future__ import annotations

import json
import os
from urllib import error as urlerror
from urllib import request as urlrequest

try:
    from vision import LM_STUDIO_URL
except Exception:                                            # pragma: no cover
    LM_STUDIO_URL = os.environ.get("LM_STUDIO_URL", "http://127.0.0.1:4096/v1")

PREFER = ("qwen3.8", "qwen3", "qwen2.5", "qwen")
PINNED = os.environ.get("PROMPT_MODEL", "")
MAX_TOKENS = int(os.environ.get("PROMPT_MAX_TOKENS", "220"))
TIMEOUT = float(os.environ.get("PROMPT_TIMEOUT", "60"))

SYSTEM = (
    "You rewrite a short brief into ONE image-generation prompt for a diffusion model.\n"
    "Output ONLY the prompt: one line, comma-separated phrases, no preamble, no quotes, "
    "no explanation, no negative prompt, under 60 words.\n"
    "Say the subject, the light, the palette, the medium and the framing. Keep every "
    "concrete thing the brief asked for — especially colours, directions and named "
    "objects — and do not introduce people, text or logos that were not asked for.\n"
    "This is content for a large LED stage wall: prefer bold forms that read from "
    "distance over fine detail."
)


def _model() -> str | None:
    try:
        with urlrequest.urlopen(f"{LM_STUDIO_URL}/models", timeout=1.5) as r:
            ids = [x.get("id", "") for x in json.load(r).get("data", []) if x.get("id")]
    except (OSError, ValueError, urlerror.URLError):
        return None
    if PINNED:
        return PINNED if PINNED in ids else None
    for want in PREFER:
        hit = next((m for m in ids if want in m.lower()), None)
        if hit:
            return hit
    return None


def expand(brief: str) -> dict:
    """{used, prompt, model, why}. `used` is False whenever the original is going
    through, and `why` says which of the ways that happened."""
    brief = (brief or "").strip()
    out = {"used": False, "prompt": brief, "model": None, "why": ""}
    if not brief:
        out["why"] = "nothing to expand"
        return out
    m = _model()
    if not m:
        out["why"] = f"no Qwen model answering on {LM_STUDIO_URL} — the brief went through as written"
        return out
    body = json.dumps({
        "model": m, "temperature": 0.6, "max_tokens": MAX_TOKENS,
        "reasoning_effort": "none",
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": brief}],
    }).encode("utf-8")
    try:
        req = urlrequest.Request(f"{LM_STUDIO_URL}/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
        with urlrequest.urlopen(req, timeout=TIMEOUT) as r:
            reply = json.load(r)
        text = ((reply.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    except (OSError, ValueError, urlerror.URLError) as exc:
        out["why"] = f"the prompt model did not answer ({exc}) — the brief went through as written"
        return out
    # A chat model will occasionally wrap it, prefix it, or hand back a paragraph.
    # Take the first non-empty line and strip the wrapping; if nothing survives, keep
    # the original rather than sending it a sentence about prompts.
    line = next((l.strip().strip('"').strip("'") for l in text.splitlines() if l.strip()), "")
    line = line.removeprefix("Prompt:").removeprefix("prompt:").strip()
    if len(line) < 8:
        out["why"] = "the prompt model returned nothing usable — the brief went through as written"
        return out
    out.update(used=True, prompt=line, model=m)
    return out
