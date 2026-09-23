#!/usr/bin/env python3
"""Simple Devnet bot watchdog for Orca lp_rebalancer.

Purpose:
- Poll Hummingbot API for bot status and open CLMM positions
- Re-deploy the configured bot when it dies and the wallet is flat
- Avoid making bad state worse: if positions are still open, log and do not redeploy

This script intentionally does not use any LLM/AI component.
Auth via HB_API_USER / HB_API_PASS.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POOL = "3KBZiL2g8C7tiJ32hTv5v3KM7aK9htpqTw4cTXz1HvPt"
DEFAULT_WALLET = "2ZuShDjgEkdiTtEqbSSCzGUhh5kaFqMjhiuC2VPUNXoB"
DEFAULT_INSTANCE_PREFIX = "orca_tight_devnet"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=str) + "\n")


def api_auth_header() -> str:
    user = os.environ.get("HB_API_USER", "admin")
    password = os.environ.get("HB_API_PASS", "admin")
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"


class ApiClient:
    def __init__(self, base: str = "http://127.0.0.1:8000"):
        self.base = base.rstrip("/")
        self.auth = api_auth_header()

    def request(self, method: str, path: str, body: Optional[dict] = None, timeout: float = 30.0) -> Any:
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": self.auth,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            raise RuntimeError(f"HTTP {e.code} {path}: {detail}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"API unreachable {path}: {e}") from e


def get_status(client: ApiClient) -> dict:
    return client.request("GET", "/bot-orchestration/status") or {}


def matching_bots(status: dict, prefix: str) -> dict:
    data = status.get("data") or {}
    return {name: meta for name, meta in data.items() if name.startswith(prefix)}


def positions_owned(client: ApiClient, pool: str, wallet: str) -> list[dict]:
    rows = client.request(
        "POST",
        "/gateway/clmm/positions_owned",
        {
            "connector": "orca",
            "network": "solana-devnet",
            "pool_address": pool,
            "wallet_address": wallet,
        },
        timeout=60.0,
    )
    return rows if isinstance(rows, list) else []


def deploy(client: ApiClient, instance_prefix: str, config_name: str, credentials_profile: str, image: str) -> dict:
    return client.request(
        "POST",
        "/bot-orchestration/deploy-v2-controllers",
        {
            "instance_name": instance_prefix,
            "credentials_profile": credentials_profile,
            "controllers_config": [config_name],
            "image": image,
            "headless": True,
        },
        timeout=180.0,
    )


def stop_bot(client: ApiClient, bot_name: str) -> dict:
    return client.request(
        "POST",
        "/bot-orchestration/stop-bot",
        {
            "bot_name": bot_name,
            "skip_order_cancellation": True,
        },
        timeout=60.0,
    )


def check_once(args: argparse.Namespace, client: ApiClient, log_path: Path) -> dict:
    status = get_status(client)
    bots = matching_bots(status, args.instance_prefix)
    running = [name for name, meta in bots.items() if (meta or {}).get("status") == "running"]
    positions = positions_owned(client, args.pool, args.wallet)

    row = {
        "ts": utc_now(),
        "running_bots": running,
        "n_matching_bots": len(bots),
        "n_positions": len(positions),
        "position_addresses": [p.get("position_address") for p in positions],
        "action": "none",
        "detail": "",
    }

    if len(running) > 1:
        row["detail"] = "multiple running bots detected; no auto-stop in safe mode"
    elif len(positions) > 1:
        row["detail"] = "duplicate LP positions detected; no auto-redeploy in safe mode"
    elif running:
        row["detail"] = "bot healthy"
    elif len(positions) == 1 and not args.redeploy_with_open_position:
        row["detail"] = "bot down but LP still open; conservative mode skips redeploy"
    else:
        if args.dry_run:
            row["action"] = "would_deploy"
            row["detail"] = "dry-run"
        else:
            resp = deploy(
                client,
                instance_prefix=args.instance_prefix,
                config_name=args.config_name,
                credentials_profile=args.credentials_profile,
                image=args.image,
            )
            row["action"] = "deploy"
            row["detail"] = (resp or {}).get("message", "deploy requested")
            row["deploy_response"] = resp

    append_jsonl(log_path, row)
    return row


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--api", default=os.environ.get("HB_API_URL", "http://127.0.0.1:8000"))
    p.add_argument("--instance-prefix", default=DEFAULT_INSTANCE_PREFIX)
    p.add_argument("--config-name", default="orca_tight_devnet")
    p.add_argument("--credentials-profile", default="master_account")
    p.add_argument("--image", default="hummingbot/hummingbot:latest")
    p.add_argument("--pool", default=DEFAULT_POOL)
    p.add_argument("--wallet", default=DEFAULT_WALLET)
    p.add_argument("--interval", type=int, default=120)
    p.add_argument("--once", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--redeploy-with-open-position",
        action="store_true",
        help="Allow redeploy when exactly one LP position is already open.",
    )
    p.add_argument(
        "--stop-extra-bots",
        action="store_true",
        help="Reserved for future use; currently logs only in safe mode.",
    )
    args = p.parse_args()

    client = ApiClient(args.api)
    log_path = ROOT / "data" / "devnet_watchdog" / "watchdog.jsonl"

    stop = {"flag": False}

    def _stop(_sig, _frame):
        stop["flag"] = True

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    while not stop["flag"]:
        try:
            row = check_once(args, client, log_path)
            print(json.dumps(row))
        except Exception as e:
            row = {"ts": utc_now(), "action": "error", "detail": str(e)}
            append_jsonl(log_path, row)
            print(json.dumps(row), file=sys.stderr)
        if args.once:
            break
        time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
