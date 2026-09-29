#!/usr/bin/env python3
"""Mainnet health watchdog for Orca lp_rebalancer.

Unlike research/devnet_watchdog.py this script:
  - NEVER auto-deploys Devnet bots
  - NEVER opens a second LP while one is still open (except via adopt --recycle)
  - Restarts Gateway on repeated position-info failures (with cooldown)
  - Soft-restarts only for mild OOR (inside limit-price hysteresis)
  - Auto adopt --recycle when past auto-close limits (stranded LP after FAILED close)
  - Hard-restart when a bot is running and LP is *confirmed* gone (anti false-flat)
  - Optionally restarts the endurance reporter if its log goes stale

Anti-flake (R003m postmortem 2026-09-29):
  RPC/Gateway often returns n_positions=0 while the LP is still open. We keep a
  sticky last-known position address and re-probe it before counting a flat poll
  or restarting Gateway / hard-restarting the bot.

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
    mainnet_balances,
    matching_bots,
    portfolio_state,
    position_info,
    positions_owned,
    restart_gateway,
    utc_now,
)


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=str) + "\n")


STATE_PATH = ROOT / "data" / "mainnet_watchdog" / "watchdog_state.json"


def load_persisted_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_persisted_state(state: dict[str, Any]) -> None:
    """Persist sticky LP + cooldowns so a LaunchAgent restart does not forget the open position."""
    keep = {
        "sticky_addr": state.get("sticky_addr"),
        "sticky_seen_ts": state.get("sticky_seen_ts"),
        "last_gateway_restart_ts": state.get("last_gateway_restart_ts"),
        "last_flat_restart_ts": state.get("last_flat_restart_ts"),
        "last_recycle_ts": state.get("last_recycle_ts"),
        "last_soft_restart_ts": state.get("last_soft_restart_ts"),
        "last_pool": state.get("last_pool"),
        "pool_switch_timestamps": state.get("pool_switch_timestamps") or [],
        "pool_switch": state.get("pool_switch", 0),
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(keep, indent=2), encoding="utf-8")


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


def flat_restart_decision(
    *,
    n_running: int,
    n_pos: int,
    flat_streak: int,
    flat_polls: int,
    cooldown_active: bool,
    confirmed_flat: bool = True,
) -> str:
    """Action name when a bot is up and the wallet has no LP. Empty string otherwise."""
    if n_running != 1 or n_pos != 0:
        return ""
    if not confirmed_flat:
        return "rpc_flake_hold"
    if flat_streak < flat_polls:
        return "watching_flat"
    if cooldown_active:
        return "flat_restart_cooldown"
    return "flat_hard_restart"


def positions_owned_stable(
    client: ApiClient,
    *,
    network: str,
    pool: str,
    wallet: str,
    attempts: int = 3,
    delay_s: float = 2.0,
) -> tuple[list[dict], str]:
    """Retry positions_owned; return first non-empty, else empty after all attempts."""
    last: list[dict] = []
    errors: list[str] = []
    for i in range(max(1, attempts)):
        try:
            last = positions_owned(client, network=network, pool=pool, wallet=wallet)
            if last:
                return last, f"ok_attempt_{i+1}"
        except Exception as e:
            errors.append(str(e)[:120])
            last = []
        if i + 1 < attempts:
            time.sleep(delay_s)
    if errors and not last:
        return [], "errors:" + "|".join(errors)[:200]
    return last, f"empty_after_{attempts}"


def probe_sticky_alive(
    client: ApiClient,
    *,
    network: str,
    sticky_addr: Optional[str],
) -> tuple[str, Optional[dict]]:
    """Check sticky position. Returns (status, info).

    status: alive | gone | unknown
    """
    if not sticky_addr:
        return "gone", None
    try:
        info = position_info(client, network=network, position_address=sticky_addr)
    except Exception:
        return "unknown", None
    if info is None:
        return "gone", None
    # Any successful info payload means the NFT/account still resolves.
    return "alive", info if isinstance(info, dict) else {"raw": True}


def free_usdc_units(client: ApiClient) -> Optional[float]:
    try:
        pf = portfolio_state(client)
        bals = mainnet_balances(pf)
        for b in bals:
            if (b.get("token") or "").upper() == "USDC":
                return float(b.get("units") or 0)
    except Exception:
        return None
    return None


def whirlpool_liquidity(position_address: str) -> Optional[int]:
    """Public-RPC Whirlpool liquidity. None=account gone; -1=RPC error."""
    import base64
    import struct
    import urllib.request

    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccountInfo",
            "params": [position_address, {"encoding": "base64"}],
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.mainnet-beta.solana.com",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            val = json.load(resp)["result"]["value"]
    except Exception:
        return -1
    if val is None:
        return None
    raw = base64.b64decode(val["data"][0])
    if len(raw) < 88:
        return -1
    lo, hi = struct.unpack_from("<QQ", raw, 72)
    return int(lo | (hi << 64))


def confirm_flat(
    client: ApiClient,
    *,
    network: str,
    pool: str,
    wallet: str,
    sticky_addr: Optional[str],
    min_free_usdc: float,
) -> tuple[bool, str, list[dict]]:
    """True only when we believe the LP is really gone.

    Requires: stable empty positions_owned AND sticky probe not alive.
    If sticky is unknown (RPC error), refuse to confirm (prevents false flat).
    When Gateway says sticky is gone, verify on-chain Whirlpool liquidity
    (Gateway 404'd Ee7c… while liquidity>0 under Helius 429).
    """
    pos, how = positions_owned_stable(client, network=network, pool=pool, wallet=wallet)
    if pos:
        return False, f"positions_visible:{how}", pos

    sticky_status, _info = probe_sticky_alive(client, network=network, sticky_addr=sticky_addr)
    if sticky_status == "alive":
        return False, "sticky_still_alive", []
    if sticky_status == "unknown":
        return False, "sticky_probe_unknown_rpc", []

    if sticky_addr:
        onchain = whirlpool_liquidity(sticky_addr)
        if onchain is not None and onchain < 0:
            return False, "sticky_onchain_rpc_error", []
        if onchain is not None and onchain > 0:
            return False, f"sticky_onchain_liq={onchain}", []
        # onchain None (account gone) or 0 liquidity — confirmed flat
        usdc = free_usdc_units(client)
        return True, f"sticky_onchain_gone_usdc={usdc}", []

    # No sticky ever: require free USDC evidence so we don't nuke a brand-new open
    usdc = free_usdc_units(client)
    if usdc is None:
        return False, "no_sticky_and_portfolio_unknown", []
    if usdc < min_free_usdc:
        return False, f"no_sticky_and_usdc_low={usdc:.4f}", []
    return True, f"no_sticky_usdc_ok={usdc:.4f}", []


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


def flat_hard_restart() -> dict[str, Any]:
    """Redeploy when the bot is running and no LP exists. adopt --recycle refuses that case."""
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "mainnet_bot_ops.py"),
        "--wait-s",
        "300",
        "hard-restart",
    ]
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=420)
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
        "pool_switch": int(state.get("pool_switch", 0)),
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

    pos, pos_how = positions_owned_stable(
        client,
        network=args.network,
        pool=args.pool,
        wallet=args.wallet,
        attempts=args.pos_retries,
        delay_s=args.pos_retry_delay_s,
    )
    row["positions_probe"] = pos_how
    row["n_positions"] = len(pos)
    row["in_range"] = [p.get("in_range") for p in pos]
    row["addresses"] = [p.get("position_address") for p in pos]
    row["watch_pool"] = args.pool
    row["sticky_addr"] = (state.get("sticky_addr") or "")[:16] or None

    # Update sticky last-known LP
    if len(pos) == 1 and pos[0].get("position_address"):
        state["sticky_addr"] = pos[0]["position_address"]
        state["sticky_seen_ts"] = time.time()
    row["sticky_addr"] = (state.get("sticky_addr") or "")[:16] or None

    # Pool-switch counter (48h rolling).
    switch_ts: list[float] = list(state.get("pool_switch_timestamps") or [])
    switch_log = ROOT / "data" / "mainnet_watchdog" / "pool_switches.jsonl"
    if switch_log.exists():
        try:
            for line in switch_log.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                ev = json.loads(line)
                ts = float(ev.get("ts_unix") or 0)
                if ts and ts not in switch_ts:
                    switch_ts.append(ts)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    last_pool = state.get("last_pool")
    if last_pool and args.pool and args.pool != last_pool:
        switch_ts.append(time.time())
    if args.pool:
        state["last_pool"] = args.pool
    now = time.time()
    switch_ts = [t for t in switch_ts if now - t <= 48 * 3600]
    state["pool_switch_timestamps"] = switch_ts
    state["pool_switch"] = len(switch_ts)
    row["pool_switch"] = len(switch_ts)
    if len(switch_ts) > 3:
        row["action"] = "alert_pool_switch_cap"
        row["detail"] = f"pool_switch={len(switch_ts)} > 3 in 48h"
        append_jsonl(log_path, row)
        return row

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

    # Flat confirmation (anti false-flat)
    confirmed_flat = False
    flat_reason = ""
    if len(running) == 1 and len(pos) == 0:
        confirmed_flat, flat_reason, recovered = confirm_flat(
            client,
            network=args.network,
            pool=args.pool,
            wallet=args.wallet,
            sticky_addr=state.get("sticky_addr"),
            min_free_usdc=args.min_free_usdc_flat,
        )
        row["flat_confirm"] = flat_reason
        if recovered:
            pos = recovered
            row["n_positions"] = len(pos)
            row["in_range"] = [p.get("in_range") for p in pos]
            row["addresses"] = [p.get("position_address") for p in pos]
            if len(pos) == 1 and pos[0].get("position_address"):
                state["sticky_addr"] = pos[0]["position_address"]
                state["sticky_seen_ts"] = time.time()
            confirmed_flat = False
            flat_reason = "recovered_on_confirm"
            row["flat_confirm"] = flat_reason
            state["flat_streak"] = 0
        elif confirmed_flat:
            state["flat_streak"] = state.get("flat_streak", 0) + 1
        else:
            # RPC flake — do not advance flat_streak toward hard-restart
            state["flat_streak"] = 0
    else:
        state["flat_streak"] = 0
        if len(pos) >= 1:
            # clear sticky death path
            pass

    row["oor_streak"] = state["oor_streak"]
    row["past_limit_streak"] = state["past_limit_streak"]
    row["info_fail_streak"] = state["info_fail_streak"]
    row["flat_streak"] = state["flat_streak"]
    row["confirmed_flat"] = confirmed_flat

    gw_cooldown = (time.time() - (state.get("last_gateway_restart_ts") or 0)) < args.gateway_restart_cooldown_s

    if not row["gateway_running"]:
        row["action"] = "alert_gateway_down"
        row["detail"] = "gateway not running"
    elif (
        state["info_fail_streak"] >= args.info_fail_limit
        and len(pos) == 1  # only bounce gateway when we still see an LP
        and not gw_cooldown
    ):
        if args.dry_run:
            row["action"] = "would_restart_gateway"
        else:
            try:
                restart_gateway(client)
                row["action"] = "restart_gateway"
                row["detail"] = f"after {state['info_fail_streak']} position-info failures"
                state["info_fail_streak"] = 0
                state["last_gateway_restart"] = utc_now()
                state["last_gateway_restart_ts"] = time.time()
            except Exception as e:
                row["action"] = "error"
                row["detail"] = f"gateway restart failed: {e}"
    elif state["info_fail_streak"] >= args.info_fail_limit and gw_cooldown:
        row["action"] = "gateway_restart_cooldown"
        row["detail"] = f"info_fail={state['info_fail_streak']} but gateway cooldown active"
    elif len(running) == 0 and len(pos) == 0:
        # Confirm before screaming — sticky may still be alive
        sticky_status, _ = probe_sticky_alive(
            client, network=args.network, sticky_addr=state.get("sticky_addr")
        )
        if sticky_status == "alive":
            row["action"] = "rpc_flake_hold"
            row["detail"] = "no bot listed but sticky LP still alive — do not hard-restart"
        else:
            row["action"] = "alert_flat_no_bot"
            row["detail"] = "no bot and no LP — run: python3 scripts/mainnet_bot_ops.py hard-restart"
    elif len(pos) == 1 and (
        (len(running) == 0)  # orphan LP
        or (past and state["past_limit_streak"] >= args.past_limit_polls)
    ):
        reason = past_detail if past else "orphan_lp_no_running_bot"
        if len(running) == 0 and not past:
            reason = "orphan_lp_no_running_bot"
        last = state.get("last_recycle_ts") or 0
        if time.time() - last < args.recycle_cooldown_s:
            row["action"] = "orphan_or_past_cooldown"
            row["detail"] = (
                f"{reason} streak_past={state['past_limit_streak']} "
                f"but recycle cooldown active"
            )
        elif args.dry_run:
            row["action"] = "would_adopt_recycle"
            row["detail"] = reason
        else:
            result = adopt_recycle(restart_gateway_flag=True)
            code = (result or {}).get("code", 1)
            row["action"] = "adopt_recycle"
            row["detail"] = {
                "reason": reason,
                "orphan": len(running) == 0,
                "past": past,
                "streak": state["past_limit_streak"],
                "result": result,
            }
            state["last_recycle_ts"] = time.time()
            state["past_limit_streak"] = 0
            state["oor_streak"] = 0
            if code != 0:
                state["recycle_fail_streak"] = state.get("recycle_fail_streak", 0) + 1
                row["action"] = "adopt_recycle_failed"
                if state["recycle_fail_streak"] >= args.recycle_fail_alert:
                    row["action"] = "alert_recycle_failed"
                    row["detail"] = {
                        **row["detail"],
                        "fail_streak": state["recycle_fail_streak"],
                        "hint": "manual: python3 scripts/mainnet_bot_ops.py --wait-s 300 adopt --recycle --restart-gateway",
                    }
            else:
                state["recycle_fail_streak"] = 0
                state["sticky_addr"] = None
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
    elif len(running) == 1 and len(pos) == 0:
        cooldown_active = (time.time() - (state.get("last_flat_restart_ts") or 0)) < args.flat_restart_cooldown_s
        decision = flat_restart_decision(
            n_running=len(running),
            n_pos=len(pos),
            flat_streak=state["flat_streak"],
            flat_polls=args.flat_polls,
            cooldown_active=cooldown_active,
            confirmed_flat=confirmed_flat,
        )
        row["action"] = decision
        row["detail"] = (
            f"running bot, 0 LP, streak {state['flat_streak']}/{args.flat_polls}, "
            f"confirm={flat_reason or confirmed_flat}"
        )
        if decision == "flat_hard_restart":
            if args.dry_run:
                row["action"] = "would_flat_hard_restart"
            else:
                result = flat_hard_restart()
                code = (result or {}).get("code", 1)
                row["detail"] = {"streak": state["flat_streak"], "confirm": flat_reason, "result": result}
                state["last_flat_restart_ts"] = time.time()
                state["flat_streak"] = 0
                state["sticky_addr"] = None
                if code != 0:
                    row["action"] = "flat_hard_restart_failed"
                elif args.reporter_run_id:
                    row["reporter"] = restart_reporter(args.reporter_run_id)
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
    p.add_argument(
        "--info-fail-limit",
        type=int,
        default=8,
        help="Gateway restart only after N position-info fails WHILE LP is visible",
    )
    p.add_argument(
        "--gateway-restart-cooldown-s",
        type=int,
        default=1800,
        help="Min seconds between Gateway restarts (anti-flap)",
    )
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
    p.add_argument(
        "--flat-polls",
        type=int,
        default=8,
        help="Confirmed-flat polls required before hard-restart (~16m at 120s)",
    )
    p.add_argument(
        "--flat-restart-cooldown-s",
        type=int,
        default=3600,
        help="Minimum seconds between flat hard-restarts",
    )
    p.add_argument("--pos-retries", type=int, default=3, help="positions_owned retries per poll")
    p.add_argument("--pos-retry-delay-s", type=float, default=2.0)
    p.add_argument(
        "--min-free-usdc-flat",
        type=float,
        default=40.0,
        help="When no sticky addr, require this free USDC before confirming flat",
    )
    p.add_argument(
        "--recycle-fail-alert",
        type=int,
        default=2,
        help="Escalate to alert_recycle_failed after N failed adopt --recycle attempts",
    )
    p.add_argument("--reporter-run-id", default="")
    p.add_argument("--reporter-stale-s", type=int, default=600)
    p.add_argument(
        "--seed-sticky",
        default="",
        help="Optional last-known LP address if state file is empty (orphan recovery)",
    )
    args = p.parse_args()

    log_path = ROOT / "data" / "mainnet_watchdog" / "watchdog.jsonl"
    state: dict[str, Any] = load_persisted_state()
    # Seed sticky from known R003m LP if empty (account may still hold capital while RPC is blind)
    if not state.get("sticky_addr") and args.seed_sticky:
        state["sticky_addr"] = args.seed_sticky
        state["sticky_seen_ts"] = time.time()

    while True:
        try:
            row = check_once(args, state, log_path)
            save_persisted_state(state)
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
