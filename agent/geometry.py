"""Sketch pixels → take units. The one conversion, in one place.

The take counts positions in DECIMETRES (1 unit = 10 cm). The Scene Study works
in metres and converts at its boundary; this service does the same and emits take
units only, so no metre ever reaches a mutator.

Frames, pinned against the venue builders (authored in metres) and the v3 seed
positions rather than assumed:

    +x   stage right → left, as drawn
    +y   up            — flown kit is positive (the projector ring sits at y 96)
    +z   DOWNSTAGE, toward the audience — the upstage LED wall is at −z, the
         thrust and the seating banks are at +z

Which is why a PLAN sketch needs no negation: the panel prints "↑ upstage" on the
canvas, so canvas-y increasing downward *is* z increasing toward the audience.
"""
from __future__ import annotations

from dataclasses import dataclass

from model import Sketch, Venue

# When nothing declares a scale and the venue has posted no figures, the drawing
# is fitted to this much room across the canvas width, and every position it
# produces is marked `guessed` and named in the plan's risks. It is a stated
# fallback, not a plausible default printed as fact.
FALLBACK_ROOM_M = 20.0


@dataclass
class Frame:
    """How this drawing maps onto the take."""
    px_per_metre: float
    origin: tuple[float, float]
    projection: str
    ground_line: float | None
    units_per_metre: float
    basis: str          # 'declared' | 'fitted' | 'guessed' — how the scale was got
    note: str           # one sentence, for the plan's risks
    # the two zeros on the page. A TOP-view point measures depth from `plan_base`; a
    # FRONT-view point measures height from `front_base`, which is the ground line.
    # Both are carried because one payload can hold items drawn in either.
    plan_base: float = 0.0
    front_base: float = 0.0

    # ---------------------------------------------------------------- convert --
    def take(self, px: float, py: float, y_metres: float = 0.0,
             view: str | None = None) -> list[float]:
        """One canvas point → [x, up, depth] in take units.

        `view` is the view that DREW the point, which is not always the view being
        looked at: the pad is one sketch seen two ways and a payload can carry both.
        A front-view point knows its height and nothing about depth; a top-view point
        knows its depth and nothing about height. Neither is guessed at here.
        """
        v = view or self.projection
        across = (px - self.origin[0]) / self.px_per_metre
        if v == "elevation":
            up = -(py - self.front_base) / self.px_per_metre
            return [self._u(across), self._u(up), 0.0]
        depth = (py - self.plan_base) / self.px_per_metre
        return [self._u(across), self._u(y_metres), self._u(depth)]

    def metres(self, px_len: float) -> float:
        return px_len / self.px_per_metre

    def _u(self, metres: float) -> float:
        return round(metres * self.units_per_metre, 1)

    @property
    def confidence(self) -> str:
        return self.basis


def frame_for(sketch: Sketch, venue: Venue | None, units_per_metre: float,
              derived: dict | None = None) -> Frame:
    """Work out the scale and the origin, and say which of the three ways it
    happened — the plan carries that word all the way to the panel."""
    canvas = sketch.canvas or {}
    cw = float(canvas.get("w") or 1600)
    ch = float(canvas.get("h") or 1000)
    origin = tuple(sketch.origin) if sketch.origin else (cw / 2, ch / 2)

    # the page's two zeros, defaulted the way the pad defaults them
    plan_base = float(sketch.origin_y if sketch.origin_y is not None else origin[1])
    front_base = float(sketch.groundLine_elevation
                       if sketch.groundLine_elevation is not None
                       else (sketch.groundLine if sketch.groundLine is not None else ch * 0.78))

    if sketch.scale and sketch.scale.pxPerMetre:
        # THE GRID IS A SCALE. The panel draws 1 m squares and says so, so a drawing
        # with no scale bar is not a drawing with no scale — it is one measured in
        # squares. `fitted` rather than `declared` only because nobody typed a number.
        drawn = getattr(sketch.scale, "basis", "drawn") != "grid"
        return Frame(float(sketch.scale.pxPerMetre), origin, sketch.projection,
                     sketch.groundLine, units_per_metre,
                     "declared" if drawn else "fitted",
                     "scale bar drawn on the sketch" if drawn else
                     f"the sketch grid: one square = {sketch.grid.get('metres', 1)} m",
                     plan_base, front_base)

    room = _venue_extent(venue, derived)
    if room:
        width_m, source = room
        return Frame(cw / width_m, origin, sketch.projection, sketch.groundLine,
                     units_per_metre, "fitted",
                     f"no scale declared — the drawing was fitted to {source} "
                     f"({width_m:.1f} m across)", plan_base, front_base)

    return Frame(cw / FALLBACK_ROOM_M, origin, sketch.projection, sketch.groundLine,
                 units_per_metre, "guessed",
                 f"no scale declared and the Scene Study has posted no venue "
                 f"dimensions — the drawing was fitted to a {FALLBACK_ROOM_M:.0f} m "
                 f"room. Every position below is a guess.", plan_base, front_base)


def frame_for_image(w: float, h: float, projection: str, venue: Venue | None,
                    units_per_metre: float, derived: dict | None = None) -> Frame:
    """The same conversion, for a PHOTOGRAPH rather than a canvas.

    A reference image has no grid and no scale bar this service can read, so there are
    only two honest answers: fit it to the venue's own width, or say it is a guess. The
    origin is the middle of the picture and the ground line is its foot — a drawing is
    framed on its subject, so the centre of the paper is the centre of the room far more
    often than not, and where it is not, the person moves it.

    `basis` is what the plan carries all the way to the panel, which is the point: a
    position derived this way must never look like one somebody measured.
    """
    origin = (w / 2, h / 2)
    room = _venue_extent(venue, derived)
    if room:
        width_m, source = room
        return Frame(w / width_m, origin, projection, h * 0.94, units_per_metre,
                     "fitted",
                     f"a reference image carries no scale — it was fitted to {source} "
                     f"({width_m:.1f} m across)",
                     origin[1], h * 0.94)
    return Frame(w / FALLBACK_ROOM_M, origin, projection, h * 0.94, units_per_metre,
                 "guessed",
                 f"a reference image carries no scale and the Scene Study has posted no "
                 f"venue dimensions — it was fitted to a {FALLBACK_ROOM_M:.0f} m room. "
                 f"Every size below is a guess.",
                 origin[1], h * 0.94)


def _venue_extent(venue: Venue | None, derived: dict | None) -> tuple[float, str] | None:
    """The venue's real width in metres, from the tool's own figures only.

    The tool derives `venueSurface` from "the venue preset's own stage dimensions,
    or the import's bounds". This service reads that; it does not keep a table of
    preset sizes, because a transcribed table is a copy that drifts.
    """
    if venue:
        for src in (venue.stage, venue.bounds):
            if src and src.get("w"):
                # a room is wider than its stage; 1.6× is the stated assumption
                return float(src["w"]) * 1.6, (venue.label or venue.preset or "the venue")
    vs = (derived or {}).get("venueSurface") or {}
    for key in ("w", "width", "stageW"):
        if isinstance(vs, dict) and vs.get(key):
            return float(vs[key]) * 1.6, "the Scene Study's venue surface"
    return None
