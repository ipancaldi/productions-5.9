# The local content pipeline — Draw Things · Z Image Turbo · Wan 2.1 · Qwen

Everything here runs on this Mac Studio. No cloud service is called, no API key
exists, and no model file is downloaded, copied or duplicated by any of this code.

    AI Content panel  ──POST /v1/image──▶  AID3N :3904
      Still / Video switch                    │   { kind: "image" | "video" }
                                              │
                                              ├─ 2. optional: LM Studio :4096 · Qwen 3.8 27B
                                              │      expands the brief into a diffusion prompt
                                              │
                                              ├─ 3. kind: "image"  — seconds
                                              │      ├─ drawthings ─▶ POST /sdapi/v1/txt2img :7860
                                              │      │                 └─ Z Image Turbo, locally
                                              │      └─ qwen-svg ──▶ fallback when Draw Things is off
                                              │
                                              ├─ 3. kind: "video"  — minutes, two stages
                                              │      ├─ a. Z Image Turbo draws ONE frame
                                              │      │      (or the panel supplies a still it has)
                                              │      ├─ b. POST /sdapi/v1/img2img :7860
                                              │      │      Wan 2.1 14B I2V ─▶ N PNG frames
                                              │      └─ c. mux.py ─▶ H.264 MP4 (AVFoundation)
                                              │
                                              ├─ 4. save PNG/MP4 to IMAGE_OUT_DIR
                                              └─ 5. return base64 + metadata to the panel

The video path is not a second pipeline. An image-to-video model needs a starting
picture, and this workspace already has a good source of one, so video is the image
pipeline with one more stage bolted to the end of it.

| File | What it is |
|---|---|
| [agent/drawthings.py](agent/drawthings.py) | The Draw Things client: config, geometry, save, metadata, named failures |
| [agent/prompt.py](agent/prompt.py) | Step 2 — Qwen expanding the brief. Optional, and it can never fail the job |
| [agent/imagegen.py](agent/imagegen.py) | The router — `kind` dispatch, plus the `qwen-svg` fallback engine |
| [agent/video.py](agent/video.py) | Stage two — Wan 2.1 I2V, model discovery on disk, named failures |
| [agent/mux.py](agent/mux.py) | Frames into an MP4. ffmpeg if present, AVFoundation otherwise |
| [agent/native/frames2mp4.swift](agent/native/frames2mp4.swift) | The AVFoundation encoder, compiled on first use and cached |
| [agent/serve.py](agent/serve.py) | `POST /v1/image`, `GET /v1/image/health` |
| [agent/stub_drawthings.py](agent/stub_drawthings.py) | A stand-in for the app, so this can be tested without the checkpoint |
| [HUB_5.9.html](HUB_5.9.html) | The **AI Content** panel — the user-facing interface, unchanged in shape |

## Why the A1111 API and not gRPC

Draw Things 1.20260716.0 has these three strings in its binary, and nothing else in
it looks like a server:

    /sdapi/v1/txt2img   /sdapi/v1/img2img   /sdapi/v1/options

So it speaks a subset of the AUTOMATIC1111 REST API, and the integration is JSON over
HTTP with `urllib` — the same thing this service already uses to reach LM Studio. No
gRPC, no protobuf, no SDK, no new dependency.

**What is absent decides the design.** There is no `/sdapi/v1/sd-models` and no
`/sdapi/v1/progress`, so this pipeline **cannot enumerate or choose a model and
cannot report progress**. Whatever checkpoint Draw Things has loaded is what
generates; the adapter reads its name from `/sdapi/v1/options` and reports it rather
than pretending it chose it.

## Before it can generate — where things stand

1. ~~The checkpoint is downloading~~ — **done.** All three files are in place:

   | File | Size | What it is |
   |---|---|---|
   | `z_image_turbo_1.0_q8p.ckpt` | 5.94 GB | the model |
   | `qwen_3_vl_4b_instruct_q8p.ckpt` | 4.54 GB | its **text encoder** |
   | `flux_1_vae_f16.ckpt` | 168 MB | its VAE |

   Worth knowing: Z Image Turbo encodes prompts with **Qwen3-VL-4B**, which is a
   different Qwen from the 27B in LM Studio. The LM Studio one only ever writes the
   prompt (step 2); the one inside Draw Things reads it. Two Qwens, two jobs.

2. **Draw Things is running translocated** from `/private/var/folders/…/AppTranslocation/…`
   — it was opened from the DMG or Downloads. The container and the models are safe,
   but the app path changes per launch. Worth moving to `/Applications`.

3. ~~The API server is off~~ — **on, and generating.** The control is **API Server**
   in the app, with **Protocol = HTTP** and a **Port**; on this machine, 7860.

   Two things cost an hour of confusion and are worth writing down:

   - **"Server Offload" is a different feature, in the opposite direction** — it lets
     this Mac borrow *another* machine's compute. Enabling it starts a local-network
     peer listener on an ephemeral port (63313 here) that accepts a TCP connection and
     closes it without a byte: not HTTP, not HTTP/2, not TLS. It is not the API server
     and probing it will never succeed.
   - **The port is discovered from the PROCESS, not guessed.** A fixed candidate list
     was the wrong shape of answer, because the app lets you choose the port and 63313
     was never going to be on any sensible list. `app_ports()` asks `lsof` which ports
     the Draw Things process holds and probes those first; each still has to prove
     itself by answering `/sdapi/v1/options`, which is exactly what rejected 63313.

Until then the router falls back to `qwen-svg` and the panel says why. That fallback
is the point of the arrangement, not a hedge: Draw Things needs its server on and a
model loaded, and on the days it is not, a panel that still makes something beats a
panel that reports an error.

## Run it

```bash
# 1 · the dev server (port 3900 is not arbitrary — see serve.py)
python3 serve.py

# 2 · AID3N, which owns the pipeline
cd agent && .venv/bin/python -m uvicorn serve:app --host 127.0.0.1 --port 3904 --app-dir .

# 3 · Draw Things: switch its API server on, load Z Image Turbo 1.0
# 4 · open the app, choose SEQUENCE CONTENT, and use the AI Content panel
open http://localhost:3900/HUB_5.9.html
```

The panel polls `/v1/image/health` on mount and shows which engine would run. A
`DRAW THINGS` badge means real diffusion; `QWEN · SVG` means the fallback, with the
reason printed underneath.

## Test it — without the checkpoint

```bash
# stand in for the app on its own default port
#   ok | refuse | noimage | slow | notdt | video | stillmodel
python3 agent/stub_drawthings.py 7860 ok

curl -s localhost:3904/v1/image/health | python3 -m json.tool
# -> "engine": "drawthings", "model": "z_image_turbo_1.0_q8p.ckpt"

curl -s -X POST localhost:3904/v1/image -H 'Content-Type: application/json' \
  -d '{"v":1,"prompt":"deep teal to magenta light curtain","w":2640,"h":1408}' \
  | python3 -m json.tool
```

Swap the stub's mode to walk each failure path. All five are verified:

| Mode | What the panel is told |
|---|---|
| *(not running)* | `nothing is answering on http://127.0.0.1:7860 — switch the API server on in Draw Things, or set DRAWTHINGS_URL to the port it is using` |
| `notdt` | `…answered 404 for /sdapi/v1/options — that port is serving something other than Draw Things` |
| `refuse` | `Draw Things refused the job (422). Check that a model is loaded and generation works in the app itself.` |
| `noimage` | `Draw Things answered without an image. That is what it does when generation itself failed — the app's own console will say why.` |
| `slow` + `DT_TIMEOUT=2` | `Draw Things did not finish inside 2s. A Turbo model should take seconds — check the app is not still loading the checkpoint…` |

Step 2 against the real Qwen, measured: `"amber caustics, moody"` →
`"amber caustics, moody lighting, bold geometric light patterns, warm orange and deep
brown palette, digital art, wide shot, high contrast, large LED stage wall"` in 2.6 s.

## Video — what the HTTP API can and cannot do

The Draw Things HTTP surface is **four routes**, and this was established by probing
every A1111 path rather than by reading anything:

| Route | |
|---|---|
| `GET /` | the whole options blob |
| `GET /sdapi/v1/options` | the same, as options |
| `POST /sdapi/v1/txt2img` | generate |
| `POST /sdapi/v1/img2img` | generate from an image |

Everything else — `sd-models`, `progress`, `interrupt`, `reload-checkpoint`,
`samplers`, `docs` — answers **404**. Two consequences shape the whole design:

**Settings are read-only over HTTP.** `POST /sdapi/v1/options` is 404, so there is no
way to "switch to the video model" as a separate step. Every knob has to travel in the
generation body — and all of them can: `model`, `num_frames`, `fps`, `shift`,
`motion_scale`, `start_frame_guidance`, `guiding_frame_noise` are all accepted there.

That is the better outcome rather than the compromise. Body settings **do not persist**
into the app (a video pass leaves the app's own `num_frames` and loaded checkpoint
exactly as they were), so each request is self-contained: no settings dance around a
generation, nothing to restore in a `finally`, and no way for a clip to leave a 16 GB
checkpoint loaded under the next still.

**The body is strictly validated**, in two ways worth knowing because both are 422s:

- an unrecognised key is refused outright — `Unrecognized keys: ["…"]` — so nothing
  speculative can be sent on the off-chance it helps;
- `init_images` must match `width`/`height` **exactly**. So `video.py` reads the frame
  size out of the keyframe PNG's IHDR rather than recomputing it, because a
  recomputation that disagrees with the actual file by one pixel fails the whole job.

An unknown checkpoint name is also a 422 — `Unrecognized model name "…"` — which is a
useful, cheap way to ask the app what it will accept.

### The model is found on disk, not over HTTP

With no `sd-models` endpoint, the checkpoint list comes from Draw Things' own Models
directory. That turns out to be a feature: a half-downloaded checkpoint sits there as
`<name>.ckpt.partial`, so the panel can say **"still downloading — stills work now"**
instead of the useless "generation failed" a POST would produce. The Video switch stays
disabled, with that sentence printed under it, until the file is real.

### Why H.264 in an MP4, and why not ffmpeg

Draw Things returns a video model the same way it returns an image: base64 PNGs in an
`images` array. There is no movie file in that exchange, so something has to encode.

ffmpeg is not installed on this machine and would be a download plus a dependency for
one job on a box that already ships a hardware H.264 encoder. So the default encoder is
AVFoundation through a small Swift helper, compiled on first use (~15 s) and cached;
`mux.py` uses ffmpeg instead if it is ever on `PATH`.

H.264/MP4 rather than the smaller WebM because this lands in a browser four times over
— the panel, the Content Bin thumbnail, the Video Preview, and a `THREE.VideoTexture`
on an LED wall in the Scene Study — and MP4 is the one encoding all four read, in
Safari and Chrome alike, with no negotiation. It is also exactly what the Scene Study
already builds for any clip that is not a still, so **the landing path needed no
changes at all**.

### Two things measured on the first real clip

**The app quantises the size to 64, whatever you ask for.** A 1920x1080 canvas requested
at a 16-pixel stride came back **832x448**, not the 832x464 the arithmetic predicted. So
`DT_VIDEO_GRID` is 64 — not because Wan wants 64, but because predicting a size the app
will not produce made this module's own reported geometry wrong. The consequence is that
16:9 is 4.4% off at this resolution; 1024x576 would be exact if the frame budget allows
it, and that is worth trying.

This is also the concrete reason `animate()` reads the frame size out of the keyframe
PNG's IHDR rather than recomputing it. `init_images` must match `width`/`height` exactly,
so had it trusted its own 464, the animation pass would have been refused with a 422.

**The MP4 timescale has to divide the frame rate.** The first encoder used a timescale of
600, and 600/16 is 37.5 — rounded to 38, which made every clip **1.3% long**: a 30-second
cue landing 0.4s late against a timeline counting frames. Fixed by using the MPEG
timescale 90000 (2^4 x 3^2 x 5^4, so it divides 8, 10, 12, 15, 16, 20, 24, 25, 30, 48, 50
and 60 exactly) **and** setting `input.mediaTimeScale` — the presentation times alone were
not enough, because the writer picks its own media timescale and resamples into it.
Verified exact at 8, 12, 16, 24, 25 and 30 fps.

## How long it will take — an estimate, and honest about being one

Draw Things has **no progress endpoint**; `/sdapi/v1/progress` answers 404. So there is
no way to show real model progress, and the panel does not pretend to: the bar is
elapsed time against how long *this machine* has taken for a job that size before.

- Under three samples it uses the service's measured constants — `DT_SECS_PER_IMAGE`
  (21 s) and `DT_VIDEO_SECS_PER_FRAME` (10.8 s).
- At three or more it uses the **median** of the last eight, kept in `localStorage`.
- Past the estimate the bar drops back to the indeterminate sweep and says "any moment
  now", because a bar parked at 99% repeats the same wrong thing for as long as it is wrong.

Three samples rather than one was bought the hard way. The first still measured through
the panel took **159 s instead of 21**, because it queued behind another job *and* made
Draw Things swap the 16 GB video checkpoint back out. One sample of that would have told
the next person to expect three minutes for a twenty-second frame. The median is chosen
for the same reason.

**Two costs no constant can predict:**

- **Draw Things runs one job at a time.** A request queues behind anything already
  generating — including work started in the app itself — and the estimate cannot see
  that queue.
- **Alternating Still and Video forces a checkpoint swap.** Each request pins its own
  model, which is what stops a clip leaving Wan loaded under the next still, but a still
  straight after a clip pays to load Z Image Turbo again — ~160 s in the worst case.
  Several stills, then several clips, is far cheaper than alternating.

## An output that assigns itself

Dropping a clip used to make it appear on the LED wall in the Scene Study while the
Timeline still read **OUTPUT NOT SET** — the scene was *guessing* the destination from
its own local selection and telling nobody. Two panels, two answers, and the take held
neither.

The guess is now a decision, made in the Timeline where the output belongs and where it
is displayed (`obviousRoute` / `autoRoute` in `sequencing-timeline.html`), enforced in
`publishClips` so no cue can leave that panel unrouted while the room plainly has a
destination. It fires only when the room leaves no doubt:

| Room | Assigned |
|---|---|
| one LED wall (or one linked canvas) | that wall |
| one projector | that projector |
| one wall **and** one projector | the wall |
| two or more walls, or two or more projectors | nothing — a real choice, left open |
| a cue with no media | nothing |
| a cue where somebody chose "— nowhere —" | nothing; that is an answer, not an absence |

Because the route now travels on the take, every panel obeys the same one instead of
guessing locally. The remaining gap is the ambiguous case: with two walls the Scene Study
still shows the clip on whichever is selected and does not report it, so the Timeline
correctly shows no output until somebody picks one.

## Configuration — all environment variables

| Variable | Default | Notes |
|---|---|---|
| `DRAWTHINGS_URL` | `http://127.0.0.1:7860` | Where the app's API server listens; set it and the probe is skipped |
| `DT_SNIFF_PORTS` | `7860,7859,7861,3000` | Ports tried when the configured one is dead |
| `IMAGE_OUT_DIR` | `<project>/Content/ai-generated` | Every finished PNG is written here |
| `DT_LONG_EDGE` | `1536` | Longest side generated, before any upscale |
| `DT_GRID` | `64` | Size quantum — see below |
| `DT_STEPS` | `4` | Measured — raise for fine detail |
| `DT_CFG` | `1.0` | Measured — **do not raise**, see below |
| `DT_SAMPLER` | `Euler A Trailing` | Passed through as A1111 spells it |
| `DT_NEGATIVE` | `text, watermark, signature, blurry, low quality` | Default negative prompt |
| `DT_TIMEOUT` | `240` | Seconds to wait for one image |
| `DT_IMAGE_MODEL` | `z_image_turbo_1.0_q8p.ckpt` | The checkpoint stills ask for by name. Empty = whatever the app has loaded |
| `DT_SECS_PER_IMAGE` | `21` | Measured. Reported to the panel so it can estimate before generating |
| `IMAGE_ENGINE` | `auto` | `auto` · `drawthings` · `qwen-svg` |

### Video

| Variable | Default | Notes |
|---|---|---|
| `DT_VIDEO_MODEL` | *(best I2V found)* | Pin the checkpoint |
| `DT_VIDEO_PREFER` | `wan_2.1_14b_i2v_fusionx,wan_2.1_14b_i2v,wan_2.1,skyreels,_i2v` | Preference order, best first |
| `DT_MODELS_DIR` | *(the app container)* | Where checkpoints are looked for |
| `DT_VIDEO_LONG_EDGE` | `832` | 480p is what Wan 2.1 I2V is trained for at this size class |
| `DT_VIDEO_GRID` | `64` | Measured: the app quantises to 64 itself, whatever it is asked for |
| `DT_VIDEO_FRAMES` | `33` | About 2 s. Measured: 81 frames is ~15 min, too slow to default to |
| `DT_VIDEO_MAX_FRAMES` | `161` | Ceiling, so a slider cannot ask for ten minutes of GPU |
| `DT_VIDEO_FPS` | `16` | Reported to the panel, which shows seconds and derives frames |
| `DT_VIDEO_STEPS` | `8` | FusionX is distilled — 8 is its range |
| `DT_VIDEO_CFG` | `1.0` | Same reasoning as the still path; see below |
| `DT_VIDEO_SHIFT` | `5.0` | Wan I2V default |
| `DT_VIDEO_MOTION` | `127` | `motion_scale` — how much it moves |
| `DT_VIDEO_TIMEOUT` | `3600` | An hour. The slider's longest clip is ~29 min, so 30 would have failed it |
| `DT_VIDEO_SECS_PER_FRAME` | `10.8` | Measured on 81 warm frames at 832x448. Drives the panel's estimate |
| `VIDEO_OUT_DIR` | *(`IMAGE_OUT_DIR`)* | Where MP4s are written |
| `FFMPEG` | *(auto-detected)* | Use ffmpeg instead of AVFoundation |
| `FRAMES2MP4` | `agent/native/frames2mp4` | The compiled encoder |
| `PROMPT_MODEL` | *(best Qwen loaded)* | Pin the prompt model |
| `LM_STUDIO_URL` | `http://127.0.0.1:4096/v1` | Shared with the vision adapter |

`steps` and `cfg` can also be overridden per request. `/v1/image/health` reports the
whole live config, so a misconfigured pipeline can be diagnosed from the panel.

## Two decisions that are visible in the metadata

**Generated size is not canvas size.** Z-Image is a ~1024px-native model; asked for a
2 640 × 1 408 wall directly it would be slow and degraded. So the request is fitted to
`DT_LONG_EDGE` on the asked-for aspect, and **both** sizes come back (`w`/`h` and
`asked`). Upscaling to the wall stays a separate, explicit step.

**The size grid costs aspect fidelity, and the response says how much.** 16:9 at a
1 536 long edge is 1 536 × 864, and 864 is a multiple of 32 but not 64 — so on the
default grid the nearest legal frame is 1 536 × 896, a 3.6% error. Measured:

| Canvas | grid 64 | error | grid 32 | error |
|---|---|---|---|---|
| 1920 × 1080 | 1536 × 896 | 3.6% | 1536 × 864 | **0%** |
| 2640 × 1408 | 1536 × 832 | 1.5% | 1536 × 832 | 1.5% |
| 15360 × 1080 | 1536 × 256 | **58%** | 1536 × 128 | 16% |

`64` is the conservative default because every SD-family model accepts it. **Try 32
once Z Image Turbo is loaded** — most modern models take it, and the common aspects
then come out exact. Any frame more than 5% off its canvas carries a `warn` string
and an amber `!` on the panel; an ultra-wide ribbon genuinely needs tiling or
outpainting rather than one pass, and this pipeline says so instead of quietly
handing back something that will be stretched.

## Placing a frame — the panel to the wall in one click

The panel has a destination row under the frame: every **LED surface** drawn in the
take and every **projector** in it, which is exactly the set the Scene Study accepts a
route to. **PLACE** does the whole chain:

1. makes a new sequence track (`addDevice('sequence')` — the item and its steps too, if
   the take had none);
2. writes the destination onto the take (`mediaRoute`);
3. lands the bytes on that track and closes its ASSIGN MEDIA step, on the same
   `landAsset` path the Content Bin's own drops take — one door, two callers;
4. moves the take's focus to the new track, and selects the wall in the room.

Dragging still works and is quicker when the timeline is on screen. PLACE is for when
it is not — and it is the only path that also names the destination.

**Two ordering bugs had to be fixed to make this work, and both affected video too:**

- **The route now travels with the bytes.** The scene push is a *watcher*: it sends on
  the next flush, i.e. after the function that changed the take has returned. So a
  panel that lands bytes and sets a route in one act sent the bytes first and the
  destination a tick later — the room installed the clip in between, found no route,
  guessed from its own selection and put the picture nowhere. `installClip` had always
  accepted an explicit route; it was simply never given one.

- **The Sequencing Timeline no longer asserts a route it does not have.** A route is
  held per *track* on the take — what the bin, the room and this panel all set — and a
  sequence route is an override on top of it. But `publishClips` and `reportMedia` both
  sent `q.route || null`, and a fresh sequence has no route, so **every timeline
  republish broadcast "throw these clips at nowhere" over a perfectly good
  destination** — and `reportMedia`'s null was written straight onto the take, so it
  did not just darken a wall, it forgot where the content was going. Now there are
  three states, in one function (`seqRoute`): a sequence route overrides, an explicit
  *— nowhere —* means nowhere, and no route at all means **no opinion**. This is the
  most likely cause of "content in the sequences is not showing in the assigned LEDs"
  on video as well as on stills.

## Where a generated frame ends up

A frame from this pipeline is a **still**, and until 8 Sep a still could not appear on
an LED surface in the Scene Study — it reached the timeline, looked healthy on it, and
left the wall black. That gap is closed: the room now builds an `ImageTexture` for a
still where it builds a `VideoTexture` for a video, so a frame generated here drags
onto a lane and lands on the wall like any other content. See the v5.9.4 notes in
`scene-study-3d.html` (`installClip`).

## Turbo settings — measured, not guessed

8 Sep, Z Image Turbo q8p on the M2 Ultra, generating 1536 × 832:

| steps | cfg | time |
|---|---|---|
| 8 | 1.5 | **131.5 s** ← the original guesses |
| 8 | 1.0 | 35.2 s |
| 4 | 1.0 | **17.3 s** ← the defaults now |

**CFG is the whole story.** Guidance above 1.0 turns classifier-free guidance on, which
means **two** forward passes per step — the conditional and the unconditional. So 1.5
did not cost 50% more than 1.0, it cost **3.7×** more. A distilled Turbo model has the
guidance baked in and is trained to run at 1.0; asking for more buys nothing and pays
double for it. There is no reason to raise `DT_CFG`.

Then 4 steps against 8 halves it again with no visible cost on stage-scale content —
checked by eye on a curtain-and-scan-lines frame. Raise `DT_STEPS` if you want fine
detail.

`Euler A Trailing` is accepted (the app's own default is `UniPC Trailing`); both
produce clean frames, so the sampler is worth an A/B when somebody has ten minutes.

## What is verified, and what the video path actually costs

**Wan works, and it returns a real frame sequence.** This was the assumption the whole
design rested on, and it is now measured rather than assumed:

| | |
|---|---|
| First clip, cold | 17 frames, 832x448 — **185 s**, including the 16 GB checkpoint and the `umt5_xxl` text encoder loading |
| Output | 300 KB H.264 MP4, 17 frames, `avc1 832x448` |
| Motion is real | inter-frame sizes average 16.7 KB (min 6.5 KB) — seventeen copies of one image would compress to a few hundred bytes each |
| Content | amber light curtains on black with a water reflection: stage-scale diffusion output, not noise |

Also verified: keyframe generated at the video pipeline's own dimensions and the animation
pass locked to the keyframe's actual size; the encoder exact at 8, 12, 16, 24, 25 and 30
fps; and — in the live app against `stub_drawthings.py video` — a clip generated from the
panel, playing looped in the preview, landing as a **V1 video track** on the timeline and
on the Content Bin shelf with its poster thumbnail.

Frame counts are snapped to **4k+1** in both `video.py` and the panel, because Wan
compresses time by four in its latent space — 81, its own training length, is 4x20+1.
Every slider second therefore maps to a clean length: 1 s is 17 frames, 5 s is 81.

What that leaves genuinely open:

- whether pixels from an AI clip reach an **LED wall** in the Scene Study. The path is
  the same `mediaAsset` message a dropped MP4 takes, and the scene already builds
  `video/mp4` blobs for anything that is not a still, so nothing new is involved — but
  it was not separately probed, because no take in the file has an LED surface in it
  (they come from a run drawn on the Sketch Pad with its role set to LED). The
  projector destinations in TAKE A and TAKE B are the cheaper way to check the routing.
- whether 81 frames is the right default, once the warm cost of a full 5 s clip is known;
- whether `DT_VIDEO_STEPS=8` / `cfg 1.0` is right for FusionX specifically;
- whether 1024x576 is affordable — it would make 16:9 exact instead of 4.4% off.

On the still path, what cannot be tested until the server is switched on:

- whether `DT_GRID=32` renders cleanly — it would make 16:9 exact instead of 3.6% off;
- whether `UniPC Trailing` beats `Euler A Trailing` on this model;
- how far `DT_LONG_EDGE` can go before the time becomes unreasonable (1536 → 18 s, so
  2048 is probably ~32 s);
- whether img2img is worth using for STILLS as well. It is already wired for video —
  that is how Wan is driven — so re-generating a frame from a sketch or from the room's
  own render is now a small change rather than a new integration.

Everything above the model — routing, prompt expansion, geometry, saving, metadata,
all five failure states, port discovery — is also tested against `stub_drawthings.py`,
which is how it gets exercised without occupying the GPU.
