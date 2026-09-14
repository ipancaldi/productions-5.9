# 5.9/agent — the Studio Agent API

FastAPI on `127.0.0.1:3902`. The host's only counterpart; the contract is
[`../AGENT-BRIDGE.md`](../AGENT-BRIDGE.md).

It holds no take, writes nothing, and persists nothing. A plan is a function of
*(scene snapshot + images + conversation)*, kept in memory for replay and then
dropped.

## Run

```bash
cd ~/Documents/Productions
5.9/agent/.venv/bin/python -m uvicorn serve:app --host 127.0.0.1 --port 3902 --app-dir 5.9/agent --reload
```

Or the `agent-api` entry in `.claude/launch.json`. First time only:

```bash
python3 -m venv 5.9/agent/.venv && 5.9/agent/.venv/bin/python -m pip install -r 5.9/agent/requirements.txt
```

## Files

| | |
|---|---|
| `serve.py` | the routes and the SSE plumbing. Knows nothing about how a plan is made |
| `session.py` | one plan in flight: the event queue, the staged ops, the pending `ask` round-trips |
| `model.py` | the wire types, exactly as the bridge document declares them |
| `geometry.py` | sketch pixels → take units. The one conversion, in one place |
| `stub.py` | **phase 1** — a deterministic interpreter, no model call |
| `agent.py` | **phase 4** — the real agent. Same `run(session)` / `refine(session, msg)` signature |

## Which interpreter

`/health` says. The stub is the default; `AGENT_STUB=0` selects the real agent
once `agent.py` exists.

```bash
curl -s localhost:3902/health
# {"ok":true,"v":1,"model":"claude-opus-5","stub":true,"interpreter":"stub","plans":0}
```

The stub reads the vector record only — stamps, declared projection, declared
scale — and exists to make every state the plan panel must render reachable and
repeatable: `declared` / `fitted` / `guessed` positions, a drawing with no
anchors, references it honestly cannot read, and a `measure_preview` that goes
unanswered. Design the accept loop against it before spending a token.

## Credentials (phase 4)

From the environment only — `ANTHROPIC_API_KEY`, or an `ant auth login` profile.
Never from the browser, which is the reason the host is the API's only client.

## Two things this service will not do

- **It never applies anything.** Ops are staged into a plan; the host mutates the
  take when a human accepts. `/v1/accepted` is feedback after the fact.
- **It never invents a measured figure.** `measure_preview` returns
  `{"unavailable": true}` when the Scene Study does not answer inside 4 s, and the
  interpreter is required to say so.


---

## v5.5 · the `local` engine (`local.py`)

A fourth engine: the VLM on this machine answers as AID3N. It goes above `mock` and
below `claude` in `serve.py`'s order, so a machine with the vision requirements installed
and no Anthropic credential stops reading *"no model"* and names the checkpoint instead.

    AGENT_ENGINE=local     pin it
    /health → engine: "local", model: "SmolVLM2-500M"

Consulted on **every** call. On a reference it does the whole arbitration in `VISION.md`;
on a sketch it is asked about each **unstamped** shape only — a stamped role is a
declaration and is never second-guessed. Every number in the plan still comes from the
deterministic reader. `refine` stays deterministic on purpose.

## v5.5 · reading a reference (`vision.py`)

An uploaded plan or elevation becomes real geometry. `HuggingFaceTB/SmolVLM2-500M-Video-Instruct`
says what each shape is; a deterministic tracer measures it. Full contract and the
measurements behind the policy: `../VISION.md`.

```bash
.venv/bin/python -m pip install -r requirements.txt      # adds numpy · Pillow · torch
                                                          # · torchvision · transformers
                                                          # · accelerate · num2words
```

`torchvision` is not optional — transformers v5 resolves SmolVLM's image processor
through it — and neither is `num2words`, which the processor imports. The first read
downloads ~1 GB of weights (about 2½ minutes); reads after that are a few seconds.

| env | effect |
|---|---|
| `VISION_MODEL` | swap the checkpoint. Nothing else changes |
| `VISION_TRACE_ONLY=1` | trace shapes, take roles from the layout. No model, milliseconds |
| `VISION_TRUST_ROLES=1` | let a *calibrated* model overrule the layout's reading. Off by default — see `VISION.md § The arbitration` |
| `VISION_OFF=1` | read nothing, and say so |

Degrades in three named states on `/health` → `vision.engine`: `smolvlm2` · `tracer`
(no torch — shapes still traced) · `off`. Same discipline as the interpreter itself: a
missing dependency is a state the panel can name, never a service that will not start.
