#!/usr/bin/env python3
"""−3% equity kill for dump-protected LP (S002 companion to mainnet watchdog).

Polls wallet+LP MTM. If equity ≤ open × (1 − kill_pct), stop bots and close
ALL Czfq positions (no redeploy). Persists baseline + kill events under
data/equity_kill/.

Does not place or open LP. Auth: HB_API_USER / HB_API_PASS.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "research"))

from mainnet_lib import (  # noqa: E402
    DEFAULT_WALLET,
    MAINNET_NETWORK,
    MAINNET_POOL,
    MAINNET_PREFIX,
    ApiClient,
    bot_status,
    close_position,
    docker_rm_force,
    matching_bots,
    portfolio_state,
    positions_owned,
    stop_bot,
    utc_now,
)
from devnet_run_reporter import snapshot_once  # noqa: E402

STATE_DIR = ROOT / "data" / "equity_kill"
STATE_PATH = STATE_DIR / "state.json"
LOG_PATH = STATE_DIR / "equity_kill.jsonl"


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=str) + "\n")


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, default=str) + "\n", encoding="utf-8")


def should_kill(equity: float, open_equity: float, kill_pct: float) -> bool:
    """True when equity has fallen kill_pct or more from open (e.g. 0.03 → −3%)."""
    if open_equity <= 0 or equity < 0:
        return False
    return equity <= open_equity * (1.0 - kill_pct)


def flatten_all(client: ApiClient) -> dict[str, Any]:
    """Stop bots and close every owned Czfq position; confirm on-chain flat."""
    log: dict[str, Any] = {"ts": utc_now(), "mode": "equity_kill_flatten", "steps": []}

    bots = matching_bots(bot_status(client), MAINNET_PREFIX)
    names = list(bots.keys())
    for name in names:
        try:
            stop_bot(client, name)
            log["steps"].append({"stop": name, "ok": True})
        except Exception as e:
            log["steps"].append({"stop": name, "ok": False, "error": str(e)})
        time.sleep(1)
    errs = docker_rm_force(names)
    log["steps"].append({"docker_rm": names, "errors": errs})

    # Cup orphan lesson: close *all* positions, not just the first.
    deadline = time.time() + 300
    closed: list[str] = []
    while time.time() < deadline:
        pos = positions_owned(
            client, network=MAINNET_NETWORK, pool=MAINNET_POOL, wallet=DEFAULT_WALLET
        )
        if not pos:
            log["flat"] = True
            log["closed"] = closed
            log["ok"] = True
            return log
        for p in pos:
            addr = p.get("position_address")
            if not addr:
                continue
            try:
                resp = close_position(
                    client,
                    network=MAINNET_NETWORK,
                    position_address=addr,
                    wallet=DEFAULT_WALLET,
                    pool=MAINNET_POOL,
                    slippage_pct=3.0,
                )
                log["steps"].append({"close": addr, "resp": resp})
                closed.append(str(addr))
            except Exception as e:
                # Gateway may 400 while close lands on-chain
                log["steps"].append({"close_error": addr, "error": str(e)})
        time.sleep(3)

    pos_left = positions_owned(
        client, network=MAINNET_NETWORK, pool=MAINNET_POOL, wallet=DEFAULT_WALLET
    )
    log["flat"] = not pos_left
    log["closed"] = closed
    log["positions_left"] = [p.get("position_address") for p in pos_left]
    log["ok"] = log["flat"]
    return log


def resolve_open_equity(
    *,
    env_open: Optional[float],
    state: dict[str, Any],
    current: float,
) -> tuple[float, str]:
    if env_open is not None and env_open > 0:
        return float(env_open), "env"
    existing = state.get("open_equity")
    if existing is not None and float(existing) > 0:
        return float(existing), "state"
    return float(current), "baseline_now"


def run_once(
    client: ApiClient,
    *,
    kill_pct: float,
    env_open: Optional[float],
    dry_run: bool,
) -> dict[str, Any]:
    state = load_state()
    if state.get("killed"):
        row = {
            "ts": utc_now(),
            "event": "already_killed",
            "killed_at": state.get("killed_at"),
            "open_equity": state.get("open_equity"),
            "kill_equity": state.get("kill_equity"),
        }
        append_jsonl(LOG_PATH, row)
        return row

    snap = snapshot_once(
        client,
        pool=MAINNET_POOL,
        wallet=DEFAULT_WALLET,
        bot_filter=MAINNET_PREFIX,
        network=MAINNET_NETWORK,
        quote_token="USDC",
    )
    equity = float(snap.get("total_mtm_quote") or 0)
    open_eq, source = resolve_open_equity(env_open=env_open, state=state, current=equity)
    state["open_equity"] = open_eq
    state["open_source"] = source
    state["last_equity"] = equity
    state["last_ts"] = snap.get("ts")
    save_state(state)

    row: dict[str, Any] = {
        "ts": utc_now(),
        "event": "poll",
        "equity": equity,
        "open_equity": open_eq,
        "open_source": source,
        "kill_pct": kill_pct,
        "threshold": open_eq * (1.0 - kill_pct),
        "n_positions": snap.get("n_positions"),
        "pool_price": snap.get("pool_price"),
    }

    if not should_kill(equity, open_eq, kill_pct):
        append_jsonl(LOG_PATH, row)
        return row

    row["event"] = "kill_trigger"
    append_jsonl(LOG_PATH, row)

    if dry_run:
        row["event"] = "kill_dry_run"
        append_jsonl(LOG_PATH, row)
        return row

    flatten_log = flatten_all(client)
    state["killed"] = True
    state["killed_at"] = utc_now()
    state["kill_equity"] = equity
    state["flatten"] = flatten_log
    save_state(state)
    done = {
        "ts": utc_now(),
        "event": "killed",
        "equity": equity,
        "open_equity": open_eq,
        "flatten_ok": flatten_log.get("ok"),
        "flatten": flatten_log,
    }
    append_jsonl(LOG_PATH, done)
    return done


def main() -> int:
    p = argparse.ArgumentParser(description="−3% equity kill for dump-protected LP")
    p.add_argument("--kill-pct", type=float, default=float(os.environ.get("EQUITY_KILL_PCT", "0.03")))
    p.add_argument("--interval", type=float, default=float(os.environ.get("EQUITY_KILL_INTERVAL", "60")))
    p.add_argument("--once", action="store_true", help="Single poll then exit")
    p.add_argument("--dry-run", action="store_true", help="Log kill but do not flatten")
    p.add_argument(
        "--open-equity",
        type=float,
        default=None,
        help="Override baseline (else EQUITY_KILL_OPEN env, else persisted/auto)",
    )
    args = p.parse_args()

    env_open_raw = os.environ.get("EQUITY_KILL_OPEN")
    env_open = float(env_open_raw) if env_open_raw else args.open_equity

    client = ApiClient()
    if args.once:
        out = run_once(client, kill_pct=args.kill_pct, env_open=env_open, dry_run=args.dry_run)
        print(json.dumps(out, indent=2, default=str))
        return 0 if out.get("event") != "killed" or out.get("flatten_ok", True) else 1

    while True:
        try:
            out = run_once(client, kill_pct=args.kill_pct, env_open=env_open, dry_run=args.dry_run)
            print(json.dumps(out, default=str), flush=True)
            if out.get("event") == "killed" and out.get("flatten_ok"):
                return 0
            if out.get("event") == "already_killed":
                time.sleep(max(args.interval, 30.0))
                continue
        except Exception as e:
            append_jsonl(LOG_PATH, {"ts": utc_now(), "event": "error", "error": str(e)})
            print(json.dumps({"ts": utc_now(), "event": "error", "error": str(e)}), flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
