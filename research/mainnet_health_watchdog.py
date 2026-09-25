#!/usr/bin/env python3
"""Mainnet health watchdog for Orca lp_rebalancer.

Unlike research/devnet_watchdog.py this script:
  - NEVER auto-deploys Devnet bots
  - NEVER opens a second LP while one is still open (except via adopt --recycle)
  - Restarts Gateway on repeated position-info failures
  - Soft-restarts only for mild OOR (inside limit-price hysteresis)
  - Auto adopt --recycle when past auto-close limits (stranded LP after FAILED close)
  - Optionally restarts the endurance reporter if its log goes stale

Why soft-restart is not enough for "stuck OOR":
  Official lp_rebalancer auto-closes via LPExecutor limit prices. If Gateway
  close returns SIMULATION_FAILED (non-retryable), the executor dies FAILED
  while the on-chain LP remains. The controller then HALTS new opens until
  manual recovery. Soft-restart clears the halt but cannot attach the orphan;
  it tries a second OPEN → INSUFFICIENT_BALANCE. Fix: Gateway close + redeploy
  (adopt --recycle).

Auth: HB_API_USER / HB_API_PASS. LLM does not place LP.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mainnet_lib import (  # noqa: E402
    DEFAULT_WALLET,
    MAINNET_NETWORK,
    MAINNET_POOL,
    MAINNET_PREFIX,
    ApiClient,
    bot_status,
    docker_restart,
    gateway_status,
    matching_bots,
    position_info,
    positions_owned,
    restart_gateway,
    utc_now,
)


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=str) + "\n")


def reporter_stale(run_id: str, max_age_s: int) -> bool:
    log = ROOT / "data" / "devnet_runs" / f"{run_id}.reporter.log"
    snap = ROOT / "data" / "devnet_runs" / run_id / "snapshots.jsonl"
    path = snap if snap.exists() else log
    if not path.exists():
        return True
    age = time.time() - path.stat().st_mtime
    return age > max_age_s


def restart_reporter(run_id: str) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "mainnet_bot_ops.py"),
        "restart-reporter",
        "--run-id",
        run_id,
    ]
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=60)
    return {"code": p.returncode, "stdout": (p.stdout or "")[:500], "stderr": (p.stderr or "")[:300]}


def adopt_recycle(*, restart_gateway_flag: bool = True) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "mainnet_bot_ops.py"),
        "adopt",
        "--recycle",
    ]
    if restart_gateway_flag:
        cmd.append("--restart-gateway")
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=300)
    return {
        "code": p.returncode,
        "stdout": (p.stdout or "")[-800:],
        "stderr": (p.stderr or "")[:400],
    }


def _f(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def past_close_limit(pos: dict[str, Any], threshold_pct: float) -> tuple[bool, str]:
    """True when spot is beyond band * (1 ± threshold/100) — executor should have closed."""
    price = _f(pos.get("current_price") or pos.get("price"))
    lower = _f(pos.get("lower_price") or pos.get("lower"))
    upper = _f(pos.get("upper_price") or pos.get("upper"))
    if price is None or lower is None or upper is None or upper <= 0 or lower <= 0:
        return False, "missing_bounds"
    thr = threshold_pct / 100.0
    upper_limit = upper * (1.0 + thr)
    lower_limit = lower * (1.0 - thr)
    if price >= upper_limit:
        return True, f"spot {price:.4f} >= upper_limit {upper_limit:.4f}"
    if price <= lower_limit:
        return True, f"spot {price:.4f} <= lower_limit {lower_limit:.4f}"
    return False, f"within_limits [{lower_limit:.4f}, {upper_limit:.4f}]"


def check_once(args: argparse.Namespace, state: dict[str, Any], log_path: Path) -> dict[str, Any]:
    client = ApiClient(args.api)
    row: dict[str, Any] = {
        "ts": utc_now(),
        "action": "none",
        "detail": "",
    }

    try:
        gw = gateway_status(client)
        row["gateway_running"] = bool(gw.get("running"))
    except Exception as e:
        row["gateway_running"] = False
        row["action"] = "error"
        row["detail"] = f"gateway status: {e}"
        append_jsonl(log_path, row)
        return row

    status = bot_status(client)
    bots = matching_bots(status, args.prefix)
    running = [n for n, m in bots.items() if (m or {}).get("status") == "running"]
    row["running_bots"] = running
    row["n_bots"] = len(bots)

    if len(running) > 1:
        row["action"] = "alert_multi_bot"
        row["detail"] = "multiple running mainnet bots — manual cleanup required"
        append_jsonl(log_path, row)
        return row

    pos = positions_owned(client, network=args.network, pool=args.pool, wallet=args.wallet)
    row["n_positions"] = len(pos)
    row["in_range"] = [p.get("in_range") for p in pos]
    row["addresses"] = [p.get("position_address") for p in pos]

    info_ok = True
    if len(pos) == 1 and pos[0].get("position_address"):
        addr = pos[0]["position_address"]
        try:
            info = position_info(client, network=args.network, position_address=addr)
            info_ok = info is not None
        except Exception as e:
            info_ok = False
            row["position_info_error"] = str(e)[:300]
    row["position_info_ok"] = info_ok

    if not info_ok:
        state["info_fail_streak"] = state.get("info_fail_streak", 0) + 1
    else:
        state["info_fail_streak"] = 0

    oor = len(pos) == 1 and pos[0].get("in_range") is False
    past = False
    past_detail = ""
    if len(pos) == 1:
        past, past_detail = past_close_limit(pos[0], args.rebalance_threshold_pct)
    row["past_close_limit"] = past
    row["past_close_detail"] = past_detail

    if oor:
        state["oor_streak"] = state.get("oor_streak", 0) + 1
    else:
        state["oor_streak"] = 0

    if past:
        state["past_limit_streak"] = state.get("past_limit_streak", 0) + 1
    else:
        state["past_limit_streak"] = 0

    row["oor_streak"] = state["oor_streak"]
    row["past_limit_streak"] = state["past_limit_streak"]
    row["info_fail_streak"] = state["info_fail_streak"]

    if not row["gateway_running"]:
        row["action"] = "alert_gateway_down"
        row["detail"] = "gateway not running"
    elif state["info_fail_streak"] >= args.info_fail_limit:
        if args.dry_run:
            row["action"] = "would_restart_gateway"
        else:
            try:
                restart_gateway(client)
                row["action"] = "restart_gateway"
                row["detail"] = f"after {state['info_fail_streak']} position-info failures"
                state["info_fail_streak"] = 0
                state["last_gateway_restart"] = utc_now()
            except Exception as e:
                row["action"] = "error"
                row["detail"] = f"gateway restart failed: {e}"
    elif len(running) == 0 and len(pos) == 0:
        row["action"] = "alert_flat_no_bot"
        row["detail"] = "no bot and no LP — run: python3 scripts/mainnet_bot_ops.py hard-restart"
    elif len(running) == 0 and len(pos) == 1:
        row["action"] = "alert_orphan_lp"
        row["detail"] = "LP open but no bot — run: python3 scripts/mainnet_bot_ops.py adopt --recycle"
    elif past and state["past_limit_streak"] >= args.past_limit_polls and len(pos) == 1:
        last = state.get("last_recycle_ts") or 0
        if time.time() - last < args.recycle_cooldown_s:
            row["action"] = "past_limit_cooldown"
            row["detail"] = (
                f"past_limit streak {state['past_limit_streak']} ({past_detail}) "
                f"but recycle cooldown active"
            )
        elif args.dry_run:
            row["action"] = "would_adopt_recycle"
            row["detail"] = past_detail
        else:
            result = adopt_recycle(restart_gateway_flag=True)
            row["action"] = "adopt_recycle"
            row["detail"] = {
                "reason": past_detail,
                "streak": state["past_limit_streak"],
                "result": result,
            }
            state["last_recycle_ts"] = time.time()
            state["past_limit_streak"] = 0
            state["oor_streak"] = 0
            if args.reporter_run_id:
                row["reporter"] = restart_reporter(args.reporter_run_id)
    elif oor and not past and state["oor_streak"] >= args.oor_limit and running:
        bot = running[0]
        last = state.get("last_soft_restart_ts") or 0
        if time.time() - last < args.restart_cooldown_s:
            row["action"] = "oor_cooldown"
            row["detail"] = f"OOR streak {state['oor_streak']} but cooldown active"
        elif args.dry_run:
            row["action"] = "would_soft_restart_bot"
            row["detail"] = bot
        else:
            code, detail = docker_restart(bot)
            row["action"] = "soft_restart_bot"
            row["detail"] = f"{bot} code={code} {detail[:200]}"
            state["last_soft_restart_ts"] = time.time()
            state["oor_streak"] = 0
    elif args.reporter_run_id and reporter_stale(args.reporter_run_id, args.reporter_stale_s):
        if args.dry_run:
            row["action"] = "would_restart_reporter"
        else:
            row["action"] = "restart_reporter"
            row["detail"] = restart_reporter(args.reporter_run_id)
    else:
        if past:
            row["detail"] = f"watching past_limit ({past_detail})"
        elif oor:
            row["detail"] = "watching mild OOR (inside limit hysteresis)"
        elif running:
            row["detail"] = "healthy"
        else:
            row["detail"] = "watching"

    append_jsonl(log_path, row)
    return row


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--api", default=os.environ.get("HB_API_URL", "http://127.0.0.1:8000"))
    p.add_argument("--prefix", default=MAINNET_PREFIX)
    p.add_argument("--network", default=MAINNET_NETWORK)
    p.add_argument("--pool", default=MAINNET_POOL)
    p.add_argument("--wallet", default=DEFAULT_WALLET)
    p.add_argument("--interval", type=int, default=120)
    p.add_argument("--once", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--info-fail-limit", type=int, default=3)
    p.add_argument("--oor-limit", type=int, default=3, help="Soft-restart after N mild-OOR polls")
    p.add_argument(
        "--past-limit-polls",
        type=int,
        default=2,
        help="Adopt-recycle after N polls with spot past auto-close limits",
    )
    p.add_argument(
        "--rebalance-threshold-pct",
        type=float,
        default=0.05,
        help="Must match live YAML rebalance_threshold_pct",
    )
    p.add_argument("--restart-cooldown-s", type=int, default=900)
    p.add_argument("--recycle-cooldown-s", type=int, default=3600)
    p.add_argument("--reporter-run-id", default="")
    p.add_argument("--reporter-stale-s", type=int, default=600)
    args = p.parse_args()

    log_path = ROOT / "data" / "mainnet_watchdog" / "watchdog.jsonl"
    state: dict[str, Any] = {}

    while True:
        try:
            row = check_once(args, state, log_path)
            print(json.dumps(row))
        except Exception as e:
            err = {"ts": utc_now(), "action": "error", "detail": str(e)}
            append_jsonl(log_path, err)
            print(json.dumps(err), file=sys.stderr)
        if args.once:
            break
        time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
