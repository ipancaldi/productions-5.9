#!/usr/bin/env python3
"""The dev server for this project. Port 3900, and the port is not arbitrary.

TWO REASONS THIS EXISTS.

1 · PORT 3900 IS THE ONE THE AGENT ALLOWS. The Sketch Pad and the Reference Board talk to the
    AI3N agent on :3904, whose CORS allow-list is exactly
        ["http://localhost:3900", "http://127.0.0.1:3900", "null"]
    ("null" being a file:// page). Serve this folder on any other port and both panels come up
    with their agent OFFLINE and their tools greyed out — the pages load perfectly and can
    simply not reach the agent. That cost a round of "localhost:8731 doesn't load the sketchpad".

2 · NO CACHING. `python3 -m http.server` sends Last-Modified and no Cache-Control, so Chrome
    caches heuristically — and an iframe whose src has not changed is not re-fetched at all.
    That cost a round of "nothing has changed" when the change was live on disk and stale in
    the panel. Everything here is sent `no-store`.

Directory listings stay on: the Scene Study reads HDR/ to find its skies.

    python3 serve.py            # http://localhost:3900
    python3 serve.py 3901       # if you know why
"""
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class NoCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        SimpleHTTPRequestHandler.end_headers(self)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3900
    print('serving this folder on http://localhost:%d' % port)
    print('  no-store: every reload is a real reload')
    if port != 3900:
        print('  WARNING: the AI3N agent on :3904 only allows origin :3900 — the Sketch Pad')
        print('           and the Reference Board will show their agent as OFFLINE here.')
    ThreadingHTTPServer(('', port), NoCache).serve_forever()
