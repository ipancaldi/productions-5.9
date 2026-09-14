"""The wire types, exactly as AGENT-BRIDGE.md declares them.

Everything the host sends is validated here and nowhere else. Blobs the API only
forwards or reads opportunistically — `scene`, `catalogues`, `derived` — are
declared `extra="allow"` dicts rather than mirrored field by field: they are the
host's projection of the take, and transcribing their shape here would be a copy
that drifts. The bridge document is the contract; this file is its parser.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

AGENT_V = 1

Confidence = Literal["declared", "fitted", "guessed"]
OpKind = Literal["add", "place", "aim", "decide", "remove", "duplicate",
                 "venue", "track", "route", "note", "audience", "block", "solid"]
Projection = Literal["plan", "elevation"]
RefRole = Literal["plan", "elevation", "photo", "drawing", "mood"]


class Loose(BaseModel):
    """Base for pass-through structures: keep what we do not model."""
    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------- the sketch --
class Scale(Loose):
    pxPerMetre: float
    # "drawn" = somebody drew a scale bar and typed a distance; "grid" = the panel's
    # own 1 m squares, which is the default and needs no asking
    basis: str = "drawn"
    metres: float | None = None
    frm: list[float] | None = Field(default=None, alias="from")
    to: list[float] | None = None


class Stroke(Loose):
    pts: list[list[float]] = []
    w: float = 2
    kind: str = "pen"
    # WHICH VIEW DREW IT. The pad is one sketch seen two ways, so a payload can carry
    # items from both and each one has to be converted through its own page.
    view: str = "plan"


class Stamp(Loose):
    label: str
    at: list[float]
    rot: float = 0
    note: str = ""
    # a drag out of the anchor: degrees in CANVAS space (0 = +x, clockwise) and how
    # far it went in pixels. What it means in the room depends on the projection.
    aim: float | None = None
    aimLen: float | None = None
    view: str = "plan"


class Label(Loose):
    text: str
    at: list[float]
    view: str = "plan"


class SemanticSuggestion(Loose):
    """A reversible OCR/model proposal, never an already accepted declaration.

    `targetId` identifies the nearest traced/built object.  The client may accept the
    proposal unchanged, edit its label/role, reassign it to another target, or reject
    it.  Keeping that workflow in the wire type prevents an OCR result from quietly
    becoming authoritative geometry or a normal stamp.
    """
    id: str
    status: Literal["proposed", "accepted", "rejected"] = "proposed"
    text: str
    label: str
    role: str
    targetId: str | None = None
    at: list[float]
    confidence: float = 0.0
    source: Literal["ocr", "model"] = "ocr"
    actions: list[Literal["accept", "edit", "reassign", "reject"]] = [
        "accept", "edit", "reassign", "reject"
    ]


class Solid(Loose):
    """v5.5 - a FITTED outline, and the one thing in this payload that is not in
    pixels.

    The pad declares and converts nothing everywhere else: pixels travel and this
    service does the arithmetic. A solid is the deliberate exception, because the pad
    holds the FIT - it decided which runs of ink were circular arcs, which vertices
    survived and what radius each arc was rounded to. It is therefore not a second
    opinion about the geometry, it is the only one, and re-deriving it here from
    pixels would be the second opinion. So it arrives in TAKE UNITS and says so on
    itself.

    `verts` are local to `at`, two numbers each: on a floor-plane solid (across,
    depth); on a front-plane one (across, up). `bulges` is one per segment - the CAD
    signed sagitta over half-chord, so 0 is a straight and +/-1 is a semicircle.
    """
    id: str = "s1"
    units: str = "take"
    role: Literal["stage", "wall", "led"] = "stage"
    name: str | None = None
    plane: Literal["floor", "front"] = "floor"
    view: str = "plan"
    closed: bool = False
    at: list[float] = [0, 0, 0]
    verts: list[list[float]] = []
    bulges: list[float] = []
    h: float = 10
    base: float = 0
    thick: float = 10
    tile: dict[str, float] | None = None
    # what the fit gave away, so the model can say so rather than imply precision it
    # was not handed: raw points in, vertices out, arc radii, RMS in METRES
    fit: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    # v5.5 - 'stamp' when somebody declared the role, 'default' when the pad chose it.
    # The only thing that decides whether a model is allowed an opinion about this shape.
    roleFrom: str = "default"
    # v5.5 - already in the take. The pad builds a traced, stamped shape directly, so
    # restaging it would be a plan full of ops that change nothing - and a plan under
    # review parks the tool's derived figures. Narrate a built solid; do not propose it.
    built: bool = False


class Sketch(Loose):
    # the panel's grid, which is the scale unless a scale bar overrides it
    """The vector record. `png_b64` is the raster the model looks at; the vectors
    are what make its answers snap to what was actually drawn."""
    png_b64: str | None = None
    canvas: dict[str, float] = {"w": 1600, "h": 1000}
    # Required: defaulting a missing declaration to plan silently turns an elevation's
    # page Y into room depth. The client must say which coordinate contract it used.
    projection: Projection
    scale: Scale | None = None
    origin: list[float] | None = None
    groundLine: float | None = None
    grid: dict[str, float] = {"px": 40, "metres": 1}
    # both of the page's zeros: the top view measures depth from the origin, the front
    # view measures height from the ground line, and a mixed payload needs both
    groundLine_elevation: float | None = None
    origin_y: float | None = None
    strokes: list[Stroke] = []
    stamps: list[Stamp] = []
    labels: list[Label] = []
    semanticSuggestions: list[SemanticSuggestion] = []
    # v5.5 - fitted outlines, in take units. See Solid.
    solids: list[Solid] = []
    note: str = ""


class RefImage(Loose):
    name: str = "reference"
    mime: str = "image/png"
    b64: str
    role: RefRole = "photo"
    note: str = ""


class Venue(Loose):
    preset: str | None = None
    label: str | None = None
    glb: str | None = None
    # the tool's own figures, when it has posted them; never invented here
    stage: dict[str, float] | None = None
    bounds: dict[str, float] | None = None


class Checklist(Loose):
    items: list[str] = []
    counts: dict[str, int] = {}


# ------------------------------------------------------------- the requests --
class InterpretRequest(Loose):
    v: int = AGENT_V
    takeId: str | None = None
    unitsPerMetre: float = 10.0
    intentHint: str | None = None
    sketch: Sketch | None = None
    images: list[RefImage] = []
    scene: dict[str, Any] = {}
    venue: Venue | None = None
    checklist: Checklist = Checklist()
    catalogues: dict[str, Any] = {}
    derived: dict[str, Any] = {}


class RefineRequest(Loose):
    v: int = AGENT_V
    planId: str
    message: str


class AnswerRequest(Loose):
    v: int = AGENT_V
    planId: str
    askId: str
    result: dict[str, Any] = {}


class AcceptedRequest(Loose):
    v: int = AGENT_V
    planId: str
    accepted: list[str] = []
    rejected: list[str] = []
    edited: list[dict[str, Any]] = []
    asFork: bool = False


# ------------------------------------------------------------------- the ops --
class Op(Loose):
    """One proposed change. `why` and `confidence` are mandatory by design: the
    plan panel ramps a row off the confidence and unticks `guessed` by default,
    so an op that cannot say how sure it is has no row to sit in."""
    id: str
    kind: OpKind
    why: str
    confidence: Confidence

    req: str | None = None
    model: str | None = None
    objId: str | None = None
    at: list[float] | None = None
    rot: dict[str, float] | None = None
    stepId: str | None = None
    value: Any = None
    preset: str | None = None
    bounds: dict[str, float] | None = None
    # physical size in TAKE UNITS, for the things a catalogue cannot know: how wide
    # the LED wall on the plan is, how deep the crowd standing in front of it goes
    w: float | None = None
    d: float | None = None
    h: float | None = None
    name: str | None = None
    startMs: int | None = None
    route: str | None = None
    frm: str | None = Field(default=None, alias="from")
    to: str | None = None
    medium: str | None = None
    text: str | None = None
    # v5.5 - a `solid` op carries a fitted outline. Same fields as Solid, and the
    # same units: local verts in take units, one bulge per segment, 0 for a straight.
    role: str | None = None
    plane: str | None = None
    closed: bool | None = None
    verts: list[list[float]] | None = None
    bulges: list[float] | None = None
    base: float | None = None
    thick: float | None = None
    tile: dict[str, float] | None = None
    fit: dict[str, Any] | None = None
    # the pad's own id for the trace this solid came from, when it came from one.
    # The host replaces rather than appends when it recognises one.
    srcId: str | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class IntentCall(Loose):
    intent: str
    confidence: float = 0.5
    why: str = ""
    add: list[str] = []
    drop: list[str] = []
    reason: str = ""
