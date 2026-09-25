#!/usr/bin/env python3
"""Mainnet bot ops: status / cleanup / soft-restart / hard-restart / adopt / restart-reporter.

One-liners (zsh-safe — no multi-line JSON):

  python3 scripts/mainnet_bot_ops.py status
  python3 scripts/mainnet_bot_ops.py cleanup
  python3 scripts/mainnet_bot_ops.py soft-restart
  python3 scripts/mainnet_bot_ops.py hard-restart
  python3 scripts/mainnet_bot_ops.py adopt
  python3 scripts/mainnet_bot_ops.py adopt --recycle
  python3 scripts/mainnet_bot_ops.py restart-reporter --run-id T010_mainnet_100_20260924

Auth: HB_API_USER / HB_API_PASS (default admin/admin). Never commit secrets.

Note: official lp_rebalancer cannot attach an orphan on-chain LP into a new executor.
`adopt` therefore stops bots (no second OPEN). `adopt --recycle` closes the LP then
deploys a clean OPEN the controller can manage.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mainnet_lib import (  # noqa: E402
    MAINNET_CONFIG,
    MAINNET_NETWORK,
    MAINNET_POOL,
    MAINNET_PREFIX,
    DEFAULT_WALLET,
    ApiClient,
    bot_status,
    close_position,
    deploy_mainnet,
    docker_restart,
    docker_rm_force,
    gateway_status,
    mainnet_balances,
    matching_bots,
    portfolio_state,
    position_info,
    positions_owned,
    restart_gateway,
    stop_bot,
    utc_now,
)


def print_json(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def cmd_status(args: argparse.Namespace) -> int:
    client = ApiClient(args.api)
    report: dict = {"ts": utc_now(), "ok": True, "checks": {}}

    try:
        gw = gateway_status(client)
        report["gateway"] = {"running": bool(gw.get("running")), "port": gw.get("port")}
        report["checks"]["gateway"] = "PASS" if gw.get("running") else "FAIL"
    except Exception as e:
        report["gateway"] = {"error": str(e)}
        report["checks"]["gateway"] = "FAIL"
        report["ok"] = False

    try:
        status = bot_status(client)
        bots = matching_bots(status, args.prefix)
        report["bots"] = {n: (m or {}).get("status") for n, m in bots.items()}
        running = [n for n, m in bots.items() if (m or {}).get("status") == "running"]
        report["checks"]["single_running_bot"] = (
            "PASS" if len(running) == 1 else ("WARN" if len(running) == 0 else "FAIL")
        )
        if len(running) > 1:
            report["ok"] = False
    except Exception as e:
        report["bots"] = {"error": str(e)}
        report["checks"]["single_running_bot"] = "FAIL"
        report["ok"] = False

    try:
        pf = portfolio_state(client)
        bals = mainnet_balances(pf)
        report["portfolio_mainnet"] = {b.get("token"): b.get("units") for b in bals}
        # note: API portfolio can lag chain; still useful
        report["checks"]["portfolio"] = "PASS" if bals else "WARN"
    except Exception as e:
        report["portfolio_mainnet"] = {"error": str(e)}
        report["checks"]["portfolio"] = "FAIL"
        report["ok"] = False

    try:
        pos = positions_owned(client, network=args.network, pool=args.pool, wallet=args.wallet)
        slim = []
        for p in pos:
            addr = p.get("position_address")
            info = None
            if addr:
                try:
                    info = position_info(client, network=args.network, position_address=addr)
                except Exception as e:
                    info = {"error": str(e)}
            slim.append(
                {
                    "address": addr,
                    "in_range": p.get("in_range"),
                    "price": p.get("current_price"),
                    "lower": p.get("lower_price"),
                    "upper": p.get("upper_price"),
                    "base": p.get("base_token_amount"),
                    "quote": p.get("quote_token_amount"),
                    "fee_base": p.get("base_fee_amount"),
                    "fee_quote": p.get("quote_fee_amount"),
                    "position_info_ok": info is not None and "error" not in (info or {}),
                }
            )
        report["positions"] = slim
        n = len(pos)
        if n == 0:
            report["checks"]["positions"] = "WARN"
        elif n == 1:
            report["checks"]["positions"] = "PASS"
            if pos[0].get("in_range") is False:
                report["checks"]["in_range"] = "FAIL"
                report["ok"] = False
            else:
                report["checks"]["in_range"] = "PASS"
            if slim and not slim[0].get("position_info_ok"):
                report["checks"]["position_info"] = "FAIL"
                report["ok"] = False
            else:
                report["checks"]["position_info"] = "PASS"
        else:
            report["checks"]["positions"] = "FAIL"
            report["ok"] = False
    except Exception as e:
        report["positions"] = {"error": str(e)}
        report["checks"]["positions"] = "FAIL"
        report["ok"] = False

    print_json(report)
    return 0 if report.get("ok") else 1


def cmd_cleanup(args: argparse.Namespace) -> int:
    client = ApiClient(args.api)
    status = bot_status(client)
    bots = matching_bots(status, args.prefix)
    names = list(bots.keys())
    # also try docker names that match prefix even if not in status
    out = {"ts": utc_now(), "stopped": [], "docker_rm": [], "errors": []}
    for name in names:
        try:
            stop_bot(client, name)
            out["stopped"].append(name)
        except Exception as e:
            out["errors"].append(f"stop {name}: {e}")
        time.sleep(1)
    errs = docker_rm_force(names)
    out["docker_rm"] = names
    out["errors"].extend(errs)
    # second pass status
    time.sleep(2)
    left = matching_bots(bot_status(client), args.prefix)
    out["remaining_api_bots"] = {n: (m or {}).get("status") for n, m in left.items()}
    print_json(out)
    return 0 if not out["errors"] else 1


def cmd_soft_restart(args: argparse.Namespace) -> int:
    """Restart the single running mainnet container in place (keeps open LP)."""
    client = ApiClient(args.api)
    status = bot_status(client)
    bots = matching_bots(status, args.prefix)
    running = [n for n, m in bots.items() if (m or {}).get("status") == "running"]
    if len(running) != 1:
        print_json({"ok": False, "error": f"need exactly 1 running bot, found {running}"})
        return 1
    name = running[0]
    code, detail = docker_restart(name)
    time.sleep(args.wait_s)
    result = {"ts": utc_now(), "restarted": name, "docker_code": code, "detail": detail.strip()}
    print_json(result)
    if code != 0:
        return 1
    return cmd_status(args)


def cmd_hard_restart(args: argparse.Namespace) -> int:
    """Stop/rm all prefix bots, optional gateway restart, redeploy, wait for OPEN, validate."""
    client = ApiClient(args.api)
    log: dict = {"ts": utc_now(), "steps": []}

    # cleanup
    status = bot_status(client)
    bots = matching_bots(status, args.prefix)
    names = list(bots.keys())
    for name in names:
        try:
            stop_bot(client, name)
            log["steps"].append({"stop": name, "ok": True})
        except Exception as e:
            log["steps"].append({"stop": name, "ok": False, "error": str(e)})
        time.sleep(1)
    docker_rm_force(names)
    log["steps"].append({"docker_rm": names})

    pos = positions_owned(client, network=args.network, pool=args.pool, wallet=args.wallet)
    log["positions_before_deploy"] = [
        {"address": p.get("position_address"), "in_range": p.get("in_range")} for p in pos
    ]
    if len(pos) > 1 and not args.force:
        log["ok"] = False
        log["error"] = "multiple open positions — refuse hard-restart without --force"
        print_json(log)
        return 2
    if len(pos) == 1 and not args.allow_open_position and not args.force:
        log["ok"] = False
        log["error"] = (
            "open LP exists — use: python3 scripts/mainnet_bot_ops.py adopt "
            "(stop open-spam, no deploy) or adopt --recycle (close LP then clean OPEN)"
        )
        print_json(log)
        return 2

    if args.restart_gateway:
        try:
            restart_gateway(client)
            log["steps"].append({"gateway_restart": True})
            time.sleep(8)
        except Exception as e:
            log["steps"].append({"gateway_restart": False, "error": str(e)})

    try:
        dep = deploy_mainnet(client, instance_name=args.prefix, config_name=args.config)
        log["deploy"] = dep
    except Exception as e:
        log["ok"] = False
        log["deploy_error"] = str(e)
        print_json(log)
        return 1

    # wait for running + preferably 1 in-range position
    deadline = time.time() + args.wait_s
    last = {}
    while time.time() < deadline:
        status = bot_status(client)
        bots = matching_bots(status, args.prefix)
        running = [n for n, m in bots.items() if (m or {}).get("status") == "running"]
        pos = positions_owned(client, network=args.network, pool=args.pool, wallet=args.wallet)
        last = {
            "running": running,
            "n_pos": len(pos),
            "in_range": [p.get("in_range") for p in pos],
            "addresses": [p.get("position_address") for p in pos],
        }
        if len(running) >= 1 and len(pos) == 1 and pos[0].get("in_range") is True:
            break
        if len(running) >= 1 and len(pos) == 1 and args.allow_oor_ok:
            break
        time.sleep(5)

    log["after_wait"] = last
    print_json(log)
    # final validation
    return cmd_status(args)


def _cleanup_prefix_bots(client: ApiClient, prefix: str) -> dict:
    status = bot_status(client)
    bots = matching_bots(status, prefix)
    names = list(bots.keys())
    out: dict = {"stopped": [], "docker_rm": names, "errors": []}
    for name in names:
        try:
            stop_bot(client, name)
            out["stopped"].append(name)
        except Exception as e:
            out["errors"].append(f"stop {name}: {e}")
        time.sleep(1)
    out["errors"].extend(docker_rm_force(names))
    time.sleep(2)
    return out


def cmd_adopt(args: argparse.Namespace) -> int:
    """Stop bots / skip deploy-open when exactly one LP exists.

    Default: cleanup bots only (no second OPEN). LP stays on-chain.
    --recycle: close that LP, then hard-restart deploy for a clean managed OPEN.
    """
    client = ApiClient(args.api)
    log: dict = {"ts": utc_now(), "mode": "adopt", "deploy_skipped": True, "steps": []}

    pos = positions_owned(client, network=args.network, pool=args.pool, wallet=args.wallet)
    if len(pos) == 0:
        log["ok"] = False
        log["error"] = "no LP to adopt — use hard-restart for a fresh OPEN"
        print_json(log)
        return 2
    if len(pos) > 1:
        log["ok"] = False
        log["error"] = f"refuse adopt with {len(pos)} positions — close extras manually"
        log["positions"] = [p.get("position_address") for p in pos]
        print_json(log)
        return 2

    kept = pos[0]
    addr = kept.get("position_address")
    log["existing_lp"] = {
        "address": addr,
        "in_range": kept.get("in_range"),
        "price": kept.get("current_price"),
        "lower": kept.get("lower_price"),
        "upper": kept.get("upper_price"),
        "base": kept.get("base_token_amount"),
        "quote": kept.get("quote_token_amount"),
    }

    cleanup = _cleanup_prefix_bots(client, args.prefix)
    log["steps"].append({"cleanup": cleanup})

    if not args.recycle:
        # Monitor-only: do not deploy (avoids FAILED open spam on insufficient free USDC)
        left = matching_bots(bot_status(client), args.prefix)
        running = [n for n, m in left.items() if (m or {}).get("status") == "running"]
        still = positions_owned(client, network=args.network, pool=args.pool, wallet=args.wallet)
        log["ok"] = len(still) == 1 and len(running) == 0
        log["remaining_bots"] = {n: (m or {}).get("status") for n, m in left.items()}
        log["positions_after"] = [
            {"address": p.get("position_address"), "in_range": p.get("in_range")} for p in still
        ]
        log["next"] = (
            "LP kept; no bot managing it. "
            "Watch via: python3 scripts/mainnet_bot_ops.py status. "
            "To put it under bot control: python3 scripts/mainnet_bot_ops.py adopt --recycle"
        )
        print_json(log)
        return 0 if log["ok"] else 1

    # recycle: close → deploy clean OPEN
    log["deploy_skipped"] = False
    log["mode"] = "adopt-recycle"
    try:
        close_resp = close_position(
            client,
            network=args.network,
            position_address=addr,
            wallet=args.wallet,
            pool=args.pool,
            slippage_pct=args.slippage_pct,
        )
        log["steps"].append({"close": close_resp})
    except Exception as e:
        log["ok"] = False
        log["error"] = f"close failed: {e}"
        print_json(log)
        return 1

    deadline = time.time() + args.wait_s
    flat = False
    while time.time() < deadline:
        pos2 = positions_owned(client, network=args.network, pool=args.pool, wallet=args.wallet)
        if len(pos2) == 0:
            flat = True
            break
        # closed address gone even if list flakes
        addrs = {p.get("position_address") for p in pos2}
        if addr not in addrs and len(pos2) == 0:
            flat = True
            break
        if addr not in addrs:
            flat = True
            break
        time.sleep(3)
    log["steps"].append({"flat": flat})
    if not flat:
        log["ok"] = False
        log["error"] = "LP still open after close — check Condor /lp or explorer before deploy"
        print_json(log)
        return 1

    if args.restart_gateway:
        try:
            restart_gateway(client)
            log["steps"].append({"gateway_restart": True})
            time.sleep(8)
        except Exception as e:
            log["steps"].append({"gateway_restart": False, "error": str(e)})

    try:
        dep = deploy_mainnet(client, instance_name=args.prefix, config_name=args.config)
        log["deploy"] = dep
    except Exception as e:
        log["ok"] = False
        log["deploy_error"] = str(e)
        print_json(log)
        return 1

    deadline = time.time() + args.wait_s
    last = {}
    while time.time() < deadline:
        status = bot_status(client)
        bots = matching_bots(status, args.prefix)
        running = [n for n, m in bots.items() if (m or {}).get("status") == "running"]
        pos3 = positions_owned(client, network=args.network, pool=args.pool, wallet=args.wallet)
        last = {
            "running": running,
            "n_pos": len(pos3),
            "in_range": [p.get("in_range") for p in pos3],
            "addresses": [p.get("position_address") for p in pos3],
        }
        if len(running) >= 1 and len(pos3) == 1 and pos3[0].get("in_range") is True:
            break
        if len(running) >= 1 and len(pos3) == 1 and args.allow_oor_ok:
            break
        time.sleep(5)
    log["after_wait"] = last
    print_json(log)
    return cmd_status(args)


def cmd_restart_reporter(args: argparse.Namespace) -> int:
    """Kill existing reporter for run-id (if any) and start a new one in background."""
    run_id = args.run_id
    log_path = ROOT / "data" / "devnet_runs" / f"{run_id}.reporter.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # pkill matching run-id
    subprocess.run(
        ["pkill", "-f", f"devnet_run_reporter.py --run-id {run_id}"],
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["pkill", "-f", f"devnet_run_reporter.py.*{run_id}"],
        check=False,
        capture_output=True,
    )
    time.sleep(1)

    cmd = [
        sys.executable,
        "-u",
        str(ROOT / "research" / "devnet_run_reporter.py"),
        "--run-id",
        run_id,
        "--network",
        args.network,
        "--quote-token",
        args.quote_token,
        "--pool",
        args.pool,
        "--wallet",
        args.wallet,
        "--bot-filter",
        args.prefix,
        "--width",
        str(args.width),
        "--threshold",
        str(args.threshold),
        "--total-amount-quote",
        str(args.total_amount_quote),
        "--interval",
        str(args.interval),
    ]
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    with log_path.open("a", encoding="utf-8") as logf:
        logf.write(f"\n# restart-reporter {utc_now()}\n")
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=logf,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
    print_json(
        {
            "ts": utc_now(),
            "ok": True,
            "pid": proc.pid,
            "run_id": run_id,
            "log": str(log_path),
            "cmd": cmd,
        }
    )
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--api", default=os.environ.get("HB_API_URL", "http://127.0.0.1:8000"))
    p.add_argument("--prefix", default=MAINNET_PREFIX)
    p.add_argument("--config", default=MAINNET_CONFIG)
    p.add_argument("--network", default=MAINNET_NETWORK)
    p.add_argument("--pool", default=MAINNET_POOL)
    p.add_argument("--wallet", default=DEFAULT_WALLET)
    p.add_argument("--wait-s", type=int, default=90)

    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Validate gateway, bots, portfolio, positions")
    sub.add_parser("cleanup", help="API-stop + docker rm -f all prefix bots")

    sp_soft = sub.add_parser("soft-restart", help="docker restart the single running bot")
    sp_soft.set_defaults()

    sp_hard = sub.add_parser("hard-restart", help="cleanup + redeploy + validate")
    sp_hard.add_argument("--restart-gateway", action="store_true")
    sp_hard.add_argument("--allow-open-position", action="store_true")
    sp_hard.add_argument("--allow-oor-ok", action="store_true", help="don't wait for in_range")
    sp_hard.add_argument("--force", action="store_true")

    sp_adopt = sub.add_parser(
        "adopt",
        help="when 1 LP exists: stop bots and skip deploy-open (use --recycle to close+redeploy)",
    )
    sp_adopt.add_argument(
        "--recycle",
        action="store_true",
        help="close the existing LP then hard-restart for a clean managed OPEN",
    )
    sp_adopt.add_argument("--restart-gateway", action="store_true")
    sp_adopt.add_argument("--allow-oor-ok", action="store_true")
    sp_adopt.add_argument("--slippage-pct", type=float, default=2.0, help="close slippage for --recycle")

    sp_rep = sub.add_parser("restart-reporter", help="restart endurance reporter")
    sp_rep.add_argument("--run-id", required=True)
    sp_rep.add_argument("--quote-token", default="USDC")
    sp_rep.add_argument("--width", default="1.5")
    sp_rep.add_argument("--threshold", default="0.05")
    sp_rep.add_argument("--total-amount-quote", default="100")
    sp_rep.add_argument("--interval", type=int, default=120)

    args = p.parse_args()
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "cleanup":
        return cmd_cleanup(args)
    if args.cmd == "soft-restart":
        return cmd_soft_restart(args)
    if args.cmd == "hard-restart":
        return cmd_hard_restart(args)
    if args.cmd == "adopt":
        return cmd_adopt(args)
    if args.cmd == "restart-reporter":
        return cmd_restart_reporter(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
