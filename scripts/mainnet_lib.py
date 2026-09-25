#!/usr/bin/env python3
"""Shared Hummingbot API helpers for mainnet ops (no secrets committed)."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional

DEFAULT_API = os.environ.get("HB_API_URL", "http://127.0.0.1:8000")
DEFAULT_WALLET = "2ZuShDjgEkdiTtEqbSSCzGUhh5kaFqMjhiuC2VPUNXoB"
MAINNET_POOL = "Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE"
MAINNET_NETWORK = "solana-mainnet-beta"
MAINNET_CONFIG = "orca_tight_mainnet_smoke"
MAINNET_PREFIX = "orca_tight_mainnet_smoke"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def api_auth_header() -> str:
    user = os.environ.get("HB_API_USER", "admin")
    password = os.environ.get("HB_API_PASS", "admin")
    return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()


class ApiClient:
    def __init__(self, base: str = DEFAULT_API):
        self.base = base.rstrip("/")
        self.auth = api_auth_header()

    def request(self, method: str, path: str, body: Optional[dict] = None, timeout: float = 60.0) -> Any:
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
            detail = e.read().decode(errors="replace")[:800]
            raise RuntimeError(f"HTTP {e.code} {path}: {detail}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"API unreachable {path}: {e}") from e


def bot_status(client: ApiClient) -> dict[str, Any]:
    return (client.request("GET", "/bot-orchestration/status") or {}).get("data") or {}


def matching_bots(status: dict[str, Any], prefix: str) -> dict[str, Any]:
    return {n: m for n, m in status.items() if n.startswith(prefix)}


def gateway_status(client: ApiClient) -> dict[str, Any]:
    return client.request("GET", "/gateway/status") or {}


def portfolio_state(client: ApiClient) -> dict[str, Any]:
    return client.request("POST", "/portfolio/state", {}) or {}


def positions_owned(
    client: ApiClient,
    *,
    network: str,
    pool: str,
    wallet: str,
) -> list[dict]:
    rows = client.request(
        "POST",
        "/gateway/clmm/positions_owned",
        {
            "connector": "orca",
            "network": network,
            "pool_address": pool,
            "wallet_address": wallet,
        },
        timeout=90.0,
    )
    return rows if isinstance(rows, list) else []


def position_info(client: ApiClient, *, network: str, position_address: str) -> dict[str, Any] | None:
    try:
        return client.request(
            "GET",
            f"/gateway/clmm/position-info?connector=orca&network={network}&position_address={position_address}",
            timeout=90.0,
        )
    except RuntimeError as e:
        if "404" in str(e) or "not found" in str(e).lower():
            return None
        raise


def stop_bot(client: ApiClient, bot_name: str) -> Any:
    return client.request(
        "POST",
        "/bot-orchestration/stop-bot",
        {"bot_name": bot_name, "skip_order_cancellation": True},
        timeout=90.0,
    )


def deploy_mainnet(
    client: ApiClient,
    *,
    instance_name: str = MAINNET_PREFIX,
    config_name: str = MAINNET_CONFIG,
    credentials_profile: str = "master_account",
    image: str = "hummingbot/hummingbot:latest",
) -> Any:
    return client.request(
        "POST",
        "/bot-orchestration/deploy-v2-controllers",
        {
            "instance_name": instance_name,
            "credentials_profile": credentials_profile,
            "controllers_config": [config_name],
            "max_global_drawdown_quote": None,
            "max_controller_drawdown_quote": None,
            "image": image,
            "headless": True,
        },
        timeout=180.0,
    )


def restart_gateway(client: ApiClient) -> Any:
    return client.request("POST", "/gateway/restart", timeout=120.0)


def close_position(
    client: ApiClient,
    *,
    network: str,
    position_address: str,
    wallet: str,
    pool: str | None = None,
    slippage_pct: float | None = 2.0,
) -> Any:
    body: dict[str, Any] = {
        "connector": "orca",
        "network": network,
        "position_address": position_address,
        "wallet_address": wallet,
    }
    if pool:
        body["pool_address"] = pool
    if slippage_pct is not None:
        body["slippage_pct"] = slippage_pct
    return client.request("POST", "/gateway/clmm/close", body, timeout=180.0)


def docker_rm_force(names: list[str]) -> list[str]:
    """Best-effort docker rm -f. Returns stderr lines on failure."""
    errors: list[str] = []
    for name in names:
        try:
            subprocess.run(
                ["docker", "rm", "-f", name],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except Exception as e:
            errors.append(f"{name}: {e}")
    return errors


def docker_restart(name: str) -> tuple[int, str]:
    try:
        p = subprocess.run(
            ["docker", "restart", name],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return 1, str(e)


def mainnet_balances(portfolio: dict) -> list[dict]:
    acct = portfolio.get("master_account") or portfolio
    return list(acct.get(MAINNET_NETWORK) or [])
