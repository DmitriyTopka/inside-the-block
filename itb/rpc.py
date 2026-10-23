"""Thin JSON-RPC client with retry. RPC URL comes from env, never hardcoded keys."""
import os
import time

import httpx

RPC_URL = os.environ.get("RPC_URL", "https://solana-rpc.publicnode.com")
# Extra endpoints that only receive sendTransaction, so a probe reaches the
# leader through more than one forwarder.
SEND_URLS = [u for u in os.environ.get("SEND_URLS", "https://solana-rpc.publicnode.com,https://api.mainnet-beta.solana.com").split(",") if u]


class Rpc:
    def __init__(self, url: str = RPC_URL, timeout: float = 60):
        self.url = url
        self.client = httpx.Client(timeout=timeout)

    def call(self, method, params=None, retries=4):
        body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
        for attempt in range(retries):
            try:
                r = self.client.post(self.url, json=body)
            except httpx.TransportError:  # public endpoints drop connections now and then
                if attempt == retries - 1:
                    raise
                time.sleep(1.5 * (attempt + 1))
                continue
            if r.status_code == 429:
                time.sleep(1.5 * (attempt + 1))
                continue
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                raise RuntimeError(f"{method}: {data['error']}")
            return data["result"]
        raise RuntimeError(f"{method}: rate limited after {retries} tries")
