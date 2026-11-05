"""Build and (optionally) send a batch of probe transactions into one leader window.

Each probe is a 1-lamport self-transfer plus compute-budget instructions, so
the only things that differ between probes are the priority fee, the fee payer
and the moment it is sent. Dry-run (the default) builds, signs and simulates
every probe and prints the send plan; nothing reaches the network.
"""
import base64
import json
import random
import time
from urllib.parse import urlparse
from dataclasses import dataclass, asdict

from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solders.hash import Hash
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.message import MessageV0
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction

from .budget import Ledger, max_fee_lamports
from concurrent.futures import ThreadPoolExecutor

from .rpc import SEND_URLS, Rpc

SLOT_SEC = 0.4


def redact(url: str) -> str:
    """Scheme and host only: a paid RPC URL can carry its API key in the query or userinfo."""
    u = urlparse(url)
    return f"{u.scheme}://{u.hostname}"

CU_LIMIT = 600  # a system transfer uses 150 CU; ComputeBudget ixs are free. Series 5 varies it per probe.


@dataclass
class Probe:
    idx: int
    payer: str
    cu_price: int
    send_rank: int
    cu_limit: int = CU_LIMIT
    signature: str = ""
    sent_at: float = 0.0
    sim_err: str | None = None
    sim_units: int | None = None


def build_tx(kp: Keypair, cu_price: int, lamports: int, blockhash: Hash, to: Pubkey | None = None,
             cu_limit: int = CU_LIMIT) -> VersionedTransaction:
    """A transfer to self by default. With `to` set, every probe of a run credits the same
    account, so all of them write-lock it and the scheduler cannot run them in parallel."""
    ixs = [
        set_compute_unit_limit(cu_limit),
        set_compute_unit_price(cu_price),
        transfer(TransferParams(from_pubkey=kp.pubkey(), to_pubkey=to or kp.pubkey(), lamports=lamports)),
    ]
    msg = MessageV0.try_compile(kp.pubkey(), ixs, [], blockhash)
    return VersionedTransaction(msg, [kp])


def plan(payers: list[Keypair], fees: list[int], order: str, seed: int, limits: list[int] | None = None) -> list[Probe]:
    """order: 'asc' sends cheapest first, 'desc' dearest first, 'random' shuffles,
    'burst' fires all probes at once (send_rank then only records list order)."""
    probes = [Probe(i, str(payers[i % len(payers)].pubkey()), f, 0, (limits or [CU_LIMIT] * len(fees))[i])
              for i, f in enumerate(fees)]
    ranked = sorted(probes, key=lambda p: p.cu_price, reverse=(order == "desc"))
    if order == "random":
        random.Random(seed).shuffle(ranked)
    for r, p in enumerate(ranked):
        p.send_rank = r
    return probes


def next_window(now: int, slots_ahead: list[int], min_lead: int = 40) -> int | None:
    for s in slots_ahead:
        if s >= now + min_lead and s % 4 == 0:  # first slot of a 4-slot leader block
            return s
    return None


class SlotClock:
    """Local slot estimate, re-anchored on the cluster every few seconds.

    Polling getSlot every 50 ms runs into public RPC rate limits, and a 429 back-off
    costs more slots than the window lasts, so the clock interpolates between reads.

    One RPC can lag the cluster by a handful of slots (publicnode drifted 2-6, once
    50), which lands a probe after the window. Anchoring on the MAX slot several
    endpoints report is closer to the true cluster tip, since no endpoint reports
    a slot the cluster has not reached.
    """
    def __init__(self, rpc: Rpc, extra_urls: list[str] | None = None, measure: bool = False):
        self.clocks = [rpc] + [Rpc(u, timeout=3) for u in (extra_urls or []) if u != rpc.url]
        self.sec = SLOT_SEC
        self.anchor()
        if measure:  # series 6: measured slot length; on 2026-11-05 mainnet ran ~0.21 s per slot, not 0.4
            s1, t1 = self.slot, self.at
            time.sleep(2.0)
            self.anchor()
            if self.slot > s1:
                self.sec = min(0.5, max(0.1, (self.at - t1) / (self.slot - s1)))

    def anchor(self):
        best, at = None, time.time()
        for c in self.clocks:
            t0 = time.time()
            try:
                s = c.call("getSlot", [{"commitment": "processed"}], retries=1)
            except Exception:
                continue
            mid = (t0 + time.time()) / 2
            if best is None or s > best:
                best, at = s, mid
        if best is None:
            raise RuntimeError("no RPC answered getSlot")
        self.slot, self.at = best, at

    def now(self) -> float:
        if time.time() - self.at > 3:
            self.anchor()
        return self.slot + (time.time() - self.at) / self.sec

    def sleep_until(self, slot: float):
        while True:
            left = (slot - self.now()) * self.sec
            if left <= 0:
                return
            time.sleep(min(left, 1.0))


def run(rpc: Rpc, payers: list[Keypair], fees: list[int], order: str, target_slot: int,
        ledger: Ledger | None, live: bool, seed: int = 0, lead_slots: float = 3.0,
        resend_until: int = 4, gap_ms: float | None = None, shared: Pubkey | None = None,
        limits: list[int] | None = None, send_urls: list[str] | None = None,
        tpu_addr: str | None = None) -> dict:
    """Wait for the window, THEN build, sign and send.

    A blockhash lives about 150 slots and the next window of a given client can
    be minutes away, so signing first would send expired transactions. Probes go
    out in send-rank order to every SEND_URLS endpoint at once, starting
    `lead_slots` before the window, and are re-sent (same signature: cannot land
    twice or cost twice) every ~150 ms until `resend_until` slots into it.

    With `gap_ms` set (series 4) the first round is timed instead: each probe goes to all
    endpoints at once without waiting for the replies, and the next probe follows
    `gap_ms` later. Re-sends after that are bursts.
    """
    probes = plan(payers, fees, order, seed, limits)
    send_urls = send_urls or SEND_URLS
    by_pk = {str(k.pubkey()): k for k in payers}
    clock = SlotClock(rpc, SEND_URLS, measure=bool(tpu_addr))
    send_at = target_slot - lead_slots
    if live:
        clock.sleep_until(send_at - 10)
    bh = Hash.from_string(rpc.call("getLatestBlockhash", [{"commitment": "confirmed"}])["value"]["blockhash"])
    raws = {}
    for p in probes:
        tx = build_tx(by_pk[p.payer], p.cu_price, 1 + p.idx, bh, shared, p.cu_limit)
        p.signature = str(tx.signatures[0])
        raws[p.idx] = base64.b64encode(bytes(tx)).decode()
        if not live:
            sim = rpc.call("simulateTransaction", [raws[p.idx], {"encoding": "base64", "sigVerify": True,
                                                                "commitment": "processed"}])["value"]
            p.sim_err = json.dumps(sim["err"]) if sim["err"] else None
            p.sim_units = sim.get("unitsConsumed")
    result = {"mode": "live" if live else "dry-run", "order": order, "seed": seed, "gap_ms": gap_ms,
              "shared_account": str(shared) if shared else None, "target_slot": target_slot,
              "send_at_slot": send_at, "blockhash": str(bh), "send_urls": [redact(u) for u in send_urls], "probes": [], "sends": 0}
    if live:
        assert ledger is not None, "live sending needs a ledger"
        for p in probes:
            ledger.reserve(max_fee_lamports(p.cu_limit, p.cu_price))
        if tpu_addr:  # series 6: our own QUIC connection to the leader, no RPC in the path
            result["via"] = "tpu"
            result["send_urls"] = []
            result["tpu"] = _send_tpu(clock, tpu_addr, probes, raws, target_slot, resend_until, lead_slots=0.5)
            result["sends"] = result["tpu"]["streams"]
            result["probes"] = [asdict(p) for p in probes]
            return result
        senders = [Rpc(u, timeout=5) for u in send_urls]
        ranked = sorted(probes, key=lambda x: x.send_rank)

        def fire(r: Rpc, raw: str):
            try:
                r.call("sendTransaction", [raw, {"encoding": "base64", "skipPreflight": True, "maxRetries": 0}], retries=1)
                return 1
            except Exception:
                return 0

        clock.sleep_until(send_at)
        pending = []
        with ThreadPoolExecutor(max_workers=len(senders) * len(probes)) as pool:
            first = True
            while clock.now() < target_slot + resend_until:
                if first and gap_ms is not None:  # timed first round: fire and move on, count replies later
                    for i, p in enumerate(ranked):
                        if i:
                            time.sleep(gap_ms / 1000)
                        p.sent_at = time.time()
                        pending += [pool.submit(fire, r, raws[p.idx]) for r in senders]
                elif order == "burst" or gap_ms is not None:  # every probe to every endpoint in one go
                    if first:
                        for p in probes:
                            p.sent_at = time.time()
                    jobs = [(r, raws[p.idx]) for p in probes for r in senders]
                    result["sends"] += sum(pool.map(lambda j: fire(*j), jobs))
                else:
                    for p in ranked:  # rank order is kept: each probe goes to all endpoints before the next one
                        if first:
                            p.sent_at = time.time()
                        result["sends"] += sum(pool.map(lambda r: fire(r, raws[p.idx]), senders))
                first = False
                time.sleep(0.15)
            result["sends"] += sum(f.result() for f in pending)
    result["probes"] = [asdict(p) for p in probes]
    return result


def _send_tpu(clock: SlotClock, addr: str, probes: list[Probe], raws: dict, target_slot: int,
              resend_until: int, lead_slots: float = 0.5) -> dict:
    """Open one unstaked QUIC connection to the leader's TPU two slots before its window,
    write every probe back to back in send-rank order half a slot before the window
    (first round, 0 ms gap), then re-write the same bytes every 100 ms until
    `resend_until` slots into the window. Same signature, so a probe can land once."""
    import asyncio
    from aioquic.asyncio import connect
    from . import tpu

    ranked = sorted(probes, key=lambda x: x.send_rank)
    blobs = {p.idx: base64.b64decode(raws[p.idx]) for p in probes}
    out = {"addr": addr, "handshake_ms": None, "streams": 0, "acked": 0, "error": None}

    # One fresh anchor, then wall-clock time only. Re-anchoring inside the waits makes blocking
    # RPC calls (several endpoints, 3 s timeouts) that overshot whole windows in the pilot.
    clock.anchor()
    sec = clock.sec
    t_slot0 = clock.at + (target_slot - clock.slot) * sec   # wall time the window opens
    t_connect = t_slot0 - 2 * sec
    t_start = t_slot0 - lead_slots * sec
    t_end = t_slot0 + resend_until * sec
    out["late_ms"] = None
    out["slot_sec"] = round(sec, 4)

    async def go():
        host, port = tpu.parse_addr(addr)
        t0 = time.time()
        async with connect(host, port, configuration=tpu.config(), wait_connected=True) as proto:
            out["handshake_ms"] = round((time.time() - t0) * 1000, 1)
            q, sids, first = proto._quic, [], True
            while time.time() < t_start:
                await asyncio.sleep(0.005)
            out["late_ms"] = round((time.time() - t_start) * 1000, 1)
            while time.time() < t_end:
                for p in ranked:
                    sid = q.get_next_available_stream_id(is_unidirectional=True)
                    q.send_stream_data(sid, blobs[p.idx], end_stream=True)
                    proto.transmit()
                    if first:
                        p.sent_at = time.time()
                    sids.append(sid)
                first = False
                await asyncio.sleep(0.1)
            await asyncio.sleep(0.5)
            out["streams"] = len(sids)
            out["acked"] = sum(1 for s in sids if q._streams.get(s) is None or q._streams[s].sender.is_finished)

    if time.time() < t_connect:
        time.sleep(t_connect - time.time())
    try:
        asyncio.run(asyncio.wait_for(go(), timeout=(resend_until + 6) * SLOT_SEC + 5))
    except Exception as e:  # refused, timed out, closed by peer: recorded, never retried through RPC
        out["error"] = f"{type(e).__name__}: {str(e)[:120]}"
    return out
