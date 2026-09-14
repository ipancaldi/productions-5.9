"""A plan in flight.

One session per interpret. It owns the outbound event queue, the ops staged so
far, and the pending `ask` round-trips. An interpreter — the stub in phase 1, the
real agent in phase 4 — is handed a session and pushes onto it; the route drains
it into SSE. Neither knows about the other.

Nothing here is persisted. The store is a capped in-memory dict so a plan can be
replayed for a screenshot or a design review, and that is the whole ambition: the
take is the store, and it lives in the browser.
"""
from __future__ import annotations

import asyncio
import json
import time
from collections import OrderedDict
from typing import Any

from model import AGENT_V, InterpretRequest, Op

ASK_TIMEOUT_S = 4.0          # the bridge's stated budget for a ghost round-trip
OP_SOFT_CAP = 24             # past this the interpreter is warned, not cut off
STORE_CAP = 32

_END = object()


class Session:
    _seq = 0

    def __init__(self, req: InterpretRequest):
        Session._seq += 1
        self.id = f"p{Session._seq}"
        self.req = req
        self.take_id = req.takeId
        self.ops: list[Op] = []
        self.risks: list[str] = []
        self.summary = ""
        self.confidence = 0.0
        self.intent: dict[str, Any] | None = None
        self.usage: dict[str, Any] = {}
        self.transcript: list[dict[str, Any]] = []
        self.started = time.monotonic()
        self.messages: list[dict[str, Any]] = []      # phase 4 keeps the conversation here
        self.feedback: list[dict[str, Any]] = []      # what a human kept, from /v1/accepted

        self._q: asyncio.Queue = asyncio.Queue()
        self._held = asyncio.Event()          # released by `finish`, however it arrives
        self._asks: dict[str, asyncio.Future] = {}
        self._ask_seq = 0
        self._op_seq = 0
        self.closed = False

    # ------------------------------------------------------------- outbound --
    def emit(self, event: str, data: dict[str, Any] | None = None) -> None:
        payload = {"v": AGENT_V, **(data or {})}
        self.transcript.append({"event": event, "data": payload})
        self._q.put_nowait((event, payload))

    def note(self, delta: str) -> None:
        self.emit("note", {"delta": delta})

    def thinking(self, delta: str) -> None:
        self.emit("thinking", {"delta": delta})

    def stage(self, **op: Any) -> Op:
        """Append an op to the plan and stream it, so the scene ghosts in while
        the agent is still talking."""
        self._op_seq += 1
        o = Op(id=f"o{self._op_seq}", **op)
        self.ops.append(o)
        self.emit("op", o.model_dump(by_alias=True, exclude_none=True))
        if len(self.ops) == OP_SOFT_CAP:
            self.note(f"\n[{OP_SOFT_CAP} ops — holding here and describing the rest]")
        return o

    def declare_intent(self, intent: str, confidence: float, why: str,
                       add: list[str] | None = None, drop: list[str] | None = None,
                       reason: str = "") -> None:
        self.intent = {"intent": intent, "confidence": round(confidence, 2), "why": why,
                       "add": add or [], "drop": drop or [], "reason": reason}
        self.emit("intent", self.intent)

    def risk(self, text: str) -> None:
        if text and text not in self.risks:
            self.risks.append(text)

    def finish(self, summary: str, confidence: float, risks: list[str] | None = None) -> None:
        """Ends the turn — and releases a parked plan, whoever called it."""
        self.summary = summary
        self.confidence = round(confidence, 2)
        for r in risks or []:
            self.risk(r)
        self.emit("done", {
            "planId": self.id, "summary": summary, "confidence": self.confidence,
            "risks": self.risks, "opCount": len(self.ops),
            "intent": self.intent, "usage": self.usage,
            "ms": int((time.monotonic() - self.started) * 1000),
        })
        self.release()

    def fail(self, code: str, message: str) -> None:
        self.emit("error", {"code": code, "message": message})

    def close(self) -> None:
        self.closed = True
        self._q.put_nowait((_END, None))

    # ------------------------------------------------------------ parked plans --
    async def park(self, timeout: float) -> bool:
        """Hold the stream open while somebody outside this process drives the plan.
        Returns True if `finish` arrived, False on timeout."""
        self._held.clear()
        try:
            await asyncio.wait_for(self._held.wait(), timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def release(self) -> None:
        self._held.set()

    def reopen(self) -> None:
        """A refine turn is the same plan and the same conversation, so it is the
        same session — with a fresh queue, because the last stream ended."""
        self._q = asyncio.Queue()
        self.closed = False
        self.started = time.monotonic()

    # --------------------------------------------------------- the ask loop --
    async def ask(self, tool: str, args: dict[str, Any] | None = None,
                  timeout: float = ASK_TIMEOUT_S) -> dict[str, Any]:
        """A live read only the host can answer — `measure_preview` is why this
        exists. On timeout the caller is handed `{'unavailable': True}` and is
        expected to SAY so; nothing here invents a figure."""
        self._ask_seq += 1
        ask_id = f"a{self._ask_seq}"
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._asks[ask_id] = fut
        self.emit("ask", {"askId": ask_id, "tool": tool, "args": args or {}})
        try:
            return await asyncio.wait_for(fut, timeout)
        except asyncio.TimeoutError:
            self.risk(f"{tool} timed out — the Scene Study did not answer in "
                      f"{timeout:.0f}s, so that figure is unavailable rather than estimated")
            return {"unavailable": True, "reason": "timeout"}
        finally:
            self._asks.pop(ask_id, None)

    def answer(self, ask_id: str, result: dict[str, Any]) -> bool:
        fut = self._asks.get(ask_id)
        if not fut or fut.done():
            return False
        fut.set_result(result)
        return True

    # ------------------------------------------------------------ SSE drain --
    async def stream(self):
        """Drain the queue as server-sent events until the interpreter closes."""
        while True:
            event, payload = await self._q.get()
            if event is _END:
                return
            yield f"event: {event}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"

    def snapshot(self) -> dict[str, Any]:
        return {
            "v": AGENT_V, "planId": self.id, "takeId": self.take_id,
            "intent": self.intent, "summary": self.summary,
            "confidence": self.confidence, "risks": self.risks,
            "ops": [o.model_dump(by_alias=True, exclude_none=True) for o in self.ops],
            "feedback": self.feedback, "transcript": self.transcript,
        }


STORE: "OrderedDict[str, Session]" = OrderedDict()


def keep(s: Session) -> Session:
    STORE[s.id] = s
    while len(STORE) > STORE_CAP:
        STORE.popitem(last=False)
    return s
