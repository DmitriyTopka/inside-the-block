"""Direct delivery to a leader's TPU over QUIC (series 6).

Series 1-5 went through public RPC `sendTransaction`, so a probe passed an RPC
node and its forwarder before reaching the leader. Here we open our own
unstaked QUIC connection to the `tpuQuic` address the leader advertises in
gossip (`getClusterNodes`) and write each signed transaction on its own
unidirectional stream, which is how Agave and Firedancer clients submit
transactions. No stake is needed; an unstaked peer simply gets the smallest
share of the leader's QoS budget, which two probes per window do not exceed.

The connection is opened before the window so the handshake does not eat into
the send gap. `send_many` writes all probes of a run on one connection with the
requested gaps and returns the wall-clock time each stream was flushed.
"""
import asyncio
import datetime
import ssl
import time

from aioquic.asyncio import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.configuration import QuicConfiguration
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.x509.oid import NameOID

ALPN = "solana-tpu"


def _self_signed():
    """Agave expects a client certificate; any self-signed ed25519 one is accepted
    for an unstaked peer (the key is not tied to a validator identity)."""
    key = ed25519.Ed25519PrivateKey.generate()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Solana node")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(1)
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=30))
            .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), False)
            .sign(key, None))
    return cert, key


def config() -> QuicConfiguration:
    cfg = QuicConfiguration(is_client=True, alpn_protocols=[ALPN],
                            verify_mode=ssl.CERT_NONE, idle_timeout=10)
    cfg.certificate, cfg.private_key = _self_signed()
    cfg.server_name = ALPN
    return cfg


def parse_addr(addr: str) -> tuple[str, int]:
    host, port = addr.rsplit(":", 1)
    return host, int(port)


async def _write(proto: QuicConnectionProtocol, raw: bytes) -> float:
    sid = proto._quic.get_next_available_stream_id(is_unidirectional=True)
    proto._quic.send_stream_data(sid, raw, end_stream=True)
    proto.transmit()
    return time.time()


async def send_many(addr: str, raws: list[bytes], gaps_ms: list[float],
                    start_at: float | None = None, connect_timeout: float = 3.0) -> dict:
    """Open one QUIC connection to `addr`, optionally wait until `start_at`
    (unix time), then write `raws[i]` after `gaps_ms[i]` ms from the previous
    write. Returns handshake time and per-probe flush times; never raises on
    network errors, it records them so the run file shows what happened."""
    host, port = parse_addr(addr)
    out = {"tpu": addr, "handshake_ms": None, "sent_at": [None] * len(raws), "error": None}
    t0 = time.time()
    try:
        async with connect(host, port, configuration=config(), wait_connected=True) as proto:
            out["handshake_ms"] = round((time.time() - t0) * 1000, 1)
            if start_at:
                delay = start_at - time.time()
                if delay > 0:
                    await asyncio.sleep(delay)
            for i, raw in enumerate(raws):
                if i and gaps_ms[i] > 0:
                    await asyncio.sleep(gaps_ms[i] / 1000)
                out["sent_at"][i] = await _write(proto, raw)
            # give the transport a moment to flush before the context closes the connection
            await asyncio.sleep(0.3)
    except Exception as e:  # handshake refused, timeout, connection closed by peer
        out["error"] = f"{type(e).__name__}: {str(e)[:120]}"
    return out


def send_many_sync(addr, raws, gaps_ms, start_at=None, connect_timeout=3.0) -> dict:
    return asyncio.run(asyncio.wait_for(
        send_many(addr, raws, gaps_ms, start_at, connect_timeout), timeout=connect_timeout + 30))
