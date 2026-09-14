# Vision — reading a reference, v5.5

How an uploaded sketch becomes geometry. The fourth contract in the set, written the
same way as the others: if the halves disagree, this file is what to fix first.

| | |
|---|---|
| **Model** | `HuggingFaceTB/SmolVLM2-500M-Video-Instruct`, via `transformers` · `AutoProcessor` + `AutoModelForImageTextToText`, `device_map="auto"` |
| **Reader** | `agent/vision.py` — the tracer, the fit, the model, the arbitration |
| **Frame** | `agent/geometry.py` · `frame_for_image` — the one place a pixel becomes a take unit |
| **Consumers** | `agent/stub.py` · `_refs` (the mock engine) · `agent/agent.py` · the `read_reference` tool (the model engine) |
| **Surfaced** | `/health` → `vision: { ok, engine, model, why }` · the Reference Board's **VISION** chip |
| **Output** | `solid` and `audience` ops — the same ops the Sketch Pad produces, so nothing downstream knows the difference |

---

## The division of labour

A 500M vision-language model is genuinely good at one thing here and hopeless at
another, and the gap between them is the whole design.

**Good at judgement over a picture** — *is this a plan or an elevation · is this shape
a deck or a seating block*. Short, closed questions about what something IS.

**Hopeless at measurement.** Ask any language model for `verts: [[-60,-40], …]` and it
returns a plausible list of numbers that is not the shape in the picture. Nothing
downstream can tell an invented coordinate from a measured one, so a model that guesses
geometry poisons every figure the Scene Study derives from it — the throw distance, the
image size, the lit area, the cabinet count.

So the geometry is **traced**, deterministically, from the pixels:

```
threshold → close the gaps → find the regions the lines enclose → follow each
boundary → fit it to vertices and true circular arcs
```

and the model is asked only what each traced region **is**. Same rule the rest of the
service already follows — *judgement in the model, arithmetic in Python* — and the same
rule the Sketch Pad follows when it hands over a fit rather than pixels.

The fit is a deliberate mirror of the pad's (`SOLIDS.md`): RDP simplify, Kåsa circle fit
with a sagitta gate, bulges on the wire. Duplicated rather than shared because the pad
fits what a person traced with a pointer and this fits what a camera photographed off a
wall — neither can call the other, and a pure function of five numbers is the cheapest
thing in this system to keep honest.

---

## What the model actually does — measured, not assumed

Asked to name three obviously different traced regions from a test plan — a 293×272
thrust, a 432×63 band at the foot of the page, a 593×39 band at the top:

| question | answers |
|---|---|
| six-way list (`stage/led/screen/seating/truss/other`) | `stage` · `stage` · `stage` |
| binary either/or | `seating` · `seating` · `seating` |
| "describe this shape in three words" | `U-shape` · `rectangle, circle, triangle` · `L-shape` |
| plan or elevation? | *"front elevation"* — it is a plan |
| how many shapes? | `2` — there are three |
| **strip or block?** | **`block` · `strip` · `strip` — correct 3/3** |

The role answers are **constant across visibly different inputs** and track the last
option offered rather than the picture. That is not a prompt needing more work; at 500M
on line art it is position bias, and a constant answer carries no information however
confidently it is phrased.

But the last row is real signal: *strip or block* is a coarse geometric discrimination
the model genuinely perceives. That gives the pipeline something it can use.

---

## The arbitration

Four rules, in order.

**1 · A declaration beats everything.** The Reference Board already asks for each
image's role — plan · elevation · photo · drawing · mood. Somebody said so; nothing
here overrules it. A **mood** reference is deliberately never traced: geometry taken
off a photograph of a nightclub is measured-looking and meaningless, which is the worst
output of the two.

**2 · The model is calibrated on the drawing in front of it.** *Strip or block* has
ground truth the tracer already knows exactly — the aspect ratio — so one question per
shape measures whether the model is looking at these pixels at all. The score goes in
the plan's narration and reads, in words, *"the model placed 3 of 3 shapes correctly as
strip or block, so it is reading the picture"*.

**3 · The geometry decides the role; the model corroborates or dissents.** The layout
of a stage plan has a grammar — upstage is up, the audience is downstage, a wall is long
and thin — and reading that grammar is not guessing, it is the inference a person makes
before reading any label. Every op records which decided: `layout` · `agreed` ·
`model` · `layout·disputed`.

A dissent is **kept, not dropped**. It lands in the op's `why` and in the plan's risks —
*"the vision model called that stage shape an audience — the layout decided; change the
role on the shape if it was right"* — where one click flips it.

**4 · The policy is a constant, so it can be argued with.** `VISION_TRUST_ROLES=1` lets
a calibrated model overrule the layout. It ships **off**, because it was measured off:
SmolVLM2-500M passed the geometry probe 3/3 and then named all three shapes wrongly.
Perceiving a picture and knowing what a thrust is are different claims, and passing the
first does not license the second.

`VISION_MODEL` swaps the checkpoint with no other change. A 2.2B SmolVLM2, an Idefics3
or a hosted VLM will start winning arbitrations on merit, and this file will not need
editing for that to happen — which is the whole reason the arbitration is explicit
rather than baked into a prompt.

---

## Scale, and the thing it refuses to do

**It never invents a scale.** A photograph of a drawing carries no grid and no scale bar
this service can read, so there are exactly two honest answers:

| basis | when | what the plan says |
|---|---|---|
| `fitted` | the Scene Study has posted venue dimensions | *"a reference image carries no scale — it was fitted to CONCERT STAGE (28.8 m across)"* |
| `guessed` | it has not | *"…and the Scene Study has posted no venue dimensions — it was fitted to a 20 m room. Every size below is a guess."* |

`guessed` ops arrive **unticked**, because that is already the rule for a guess. A
reference dropped on an empty take therefore proposes a scene whose shapes are exactly
right and whose sizes are explicitly a guess — and the panel says so before anything is
accepted.

---

## The tracer, and the two failures worth writing down

**Antialiasing doubles every stroke, and then the drawing has no regions in it at all.**
A 4-pixel line resampled by any image pipeline has a 3-pixel skirt of half-tones either
side. A flat-offset local threshold swallows the skirt, so strokes come out twice as
wide, and the dilation that closes hand-drawn corner gaps then merges the whole drawing
into one blob — one background component, no interiors, nothing traced. The failure is
invisible in the mask and total downstream, which is why the thresholds are relative to
the drawing's own contrast (`hi − lo`) rather than absolute.

**The darkest 2% of a line drawing is not ink.** Ink is a couple of *per cent* of the
pixels, so a 2nd-percentile "darkest" lands in the antialiased skirt, `span` collapses,
and the threshold rejects the drawing entirely. It is the 0.5th percentile.

**Every shape is found twice and only one of them is the shape.** A closed outline gives
an *enclosed* region — its interior, what the drawing means — and an *ink* region: the
loop of stroke itself, traced up one side and back down the other. Both are real
components. The ink twin is dropped wherever it covers the same ground, and kept only
where there is no interior at all, which is something drawn solid rather than outlined.

Polarity is decided, not assumed: a photo of a whiteboard and a screenshot of this very
panel are both references somebody will drop, and they are opposites.

---

## The `local` engine — SmolVLM2 as AID3N

AID3N had three engines and only two could think: `claude` needs a credential, `external`
needs somebody to attach an agent, and `mock` calls no model. So the panel read
**"AID3N · no model"** — true of the interpreter and false of the machine, which is the
worst kind of true.

`agent/local.py` is the fourth. It sits **above `mock` and below `claude`** in
`serve.py`'s order, and the header names the checkpoint: *AID3N · local model ·
SmolVLM2-500M*. `AGENT_ENGINE=local` pins it.

**It is consulted on every call, sketch and reference alike.**

| call | what the model is asked |
|---|---|
| **reference** | the whole of § The arbitration above — projection, then each traced region's role |
| **sketch** | each **unstamped** shape's role, cropped out of the raster the pad already sends |

The sketch case is the interesting one, and it turns on a distinction the payload now
carries: `roleFrom` is `stamp` when somebody declared the role and `default` when the pad
chose it. **A stamped shape is a declaration and is never second-guessed.** An unstamped
one is an open question — precisely the one judgement worth asking a model for — so those
are the crops it sees, calibrated and arbitrated exactly as a reference is.

A sketch where every shape is stamped still goes to the engine, and comes back saying
*"every shape in it is stamped, so there is nothing for it to guess about"* — which is an
answer, not a skipped call.

Two consequences worth stating plainly:

- **Not one coordinate in a plan produced by this engine was written by a language
  model.** Every position, size, vertex and arc comes from the deterministic reader — the
  pad's own fit for a sketch, the tracer for a reference.
- **`refine` is deliberately deterministic.** A 500M model asked to revise a plan
  produces fluent noise, and a plan is about to be applied to somebody's production. The
  correction is recorded for whichever engine answers next, and the panel says so.

## Degrading

Three states, each a different promise, all named on `/health` and on the board's chip:

| engine | what it means |
|---|---|
| `smolvlm2` | the model answers and the tracer measures |
| `tracer` | no torch on the machine — shapes are **still traced**, and their roles come from the layout, which is deterministic and says so |
| `off` | nothing can be read. The board says that rather than accepting a file and quietly doing nothing with it |

`VISION_OFF=1` pins it off; `VISION_TRACE_ONLY=1` pins the middle state, which is also
the fast one — the tracer is milliseconds, the model is ~2 s per question on CPU.

---

## Running it

```bash
v5.5/agent/.venv/bin/python -m pip install -r v5.5/agent/requirements.txt
AGENT_STUB=1 v5.5/agent/.venv/bin/python -m uvicorn serve:app \
  --host 127.0.0.1 --port 3903 --app-dir v5.5/agent
```

The first read downloads ~1 GB of weights and takes about two and a half minutes; every
read after that is a few seconds. `torch` and `torchvision` are both required —
transformers v5 resolves SmolVLM's image processor through a torchvision backend — along
with `num2words`, which its processor imports.

---

## Changing this contract

Adding a probe, a role or a note is backwards-compatible. Changing what the model is
allowed to decide is not a code change but a **policy** change: flip
`VISION_TRUST_ROLES`, and record here what you measured that justified it.
