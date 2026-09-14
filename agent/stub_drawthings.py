"""A STAND-IN FOR DRAW THINGS' API — how the pipeline gets tested without the app.

The same argument stub.py makes for the interpreter: this is not a fallback nobody
wants, it is how the pipeline gets built and its failure paths exercised without a
5.94 GB checkpoint, a loaded model, or a minute per image. It serves the three
endpoints Draw Things serves and nothing else.

    python3 stub_drawthings.py 7860 ok        a 64x36 PNG, instantly
    python3 stub_drawthings.py 7860 refuse    422 — what "no model loaded" looks like
    python3 stub_drawthings.py 7860 noimage   200 with an empty images list
    python3 stub_drawthings.py 7860 slow      sleeps 6s — for testing DT_TIMEOUT
    python3 stub_drawthings.py 7860 notdt     404 on options — a port owned by something else
    python3 stub_drawthings.py 7860 video     img2img returns num_frames frames, animated
    python3 stub_drawthings.py 7860 stillmodel  img2img returns ONE frame — an image
                                              checkpoint answering a video request

Point DRAWTHINGS_URL at it, or run it on 7860 and it IS the Draw Things the adapter
finds. The one thing it cannot tell you is whether a real frame looks any good.
"""
import base64, json, sys, time, zlib, struct
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODE = sys.argv[2] if len(sys.argv) > 2 else "ok"

def png(w=64, h=36, rgb=(20, 200, 170), bar=-1):
    """A flat field, optionally with a one-pixel-wide white bar at column `bar` — that
    bar is what makes a stub SEQUENCE checkable: a test can decode the frames and see
    the bar move, which is the only thing that distinguishes a real animation from the
    same frame repeated num_frames times."""
    row = bytearray()
    rows = []
    for _ in range(h):
        row = bytearray(b"\x00")
        for x in range(w):
            row += bytes((255, 255, 255)) if x == bar else bytes(rgb)
        rows.append(bytes(row))
    raw = b"".join(rows)
    def chunk(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _j(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path == "/sdapi/v1/options":
            if MODE == "notdt": return self._j(404, {"detail": "nope"})
            # Real Draw Things reports the checkpoint as `model`; the A1111 name is
            # sent alongside it because the adapter tolerates either.
            return self._j(200, {"model": "z_image_turbo_1.0_q8p.ckpt",
                                 "sd_model_checkpoint": "z_image_turbo_1.0_q8p.ckpt",
                                 "num_frames": 14, "fps": 5})
        self._j(404, {"detail": "no"})
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            body = {}
        if MODE == "refuse":   return self._j(422, {"detail": "no model loaded"})
        if MODE == "noimage":  return self._j(200, {"images": [], "info": "{}"})
        if MODE == "slow":     time.sleep(6)
        w = int(body.get("width") or 64)
        h = int(body.get("height") or 36)
        if MODE == "video" and self.path.endswith("/img2img"):
            # The real thing echoes the frame size it was given, and refuses when the
            # init image disagrees with it — so does this, because that 422 is a real
            # failure the pipeline has to get right.
            init = (body.get("init_images") or [None])[0]
            if init:
                raw = base64.b64decode(init)
                iw = int.from_bytes(raw[16:20], "big"); ih = int.from_bytes(raw[20:24], "big")
                if (iw, ih) != (w, h):
                    return self._j(422, {"detail": f"init_images height doesn't match {ih} "
                                                   f"from the parameter {h}"})
            frames = max(1, int(body.get("num_frames") or 14))
            imgs = [base64.b64encode(png(w, h, bar=int(i * (w - 1) / max(1, frames - 1)))).decode()
                    for i in range(frames)]
            return self._j(200, {"images": imgs, "info": json.dumps({"seed": 424242})})
        if MODE == "stillmodel" and self.path.endswith("/img2img"):
            return self._j(200, {"images": [base64.b64encode(png(w, h)).decode()],
                                 "info": json.dumps({"seed": 1})})
        self._j(200, {"images": [base64.b64encode(png(w, h)).decode()],
                      "info": json.dumps({"seed": 424242})})

ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
