#!/usr/bin/env python3
"""Tear down, test the dust floor, tear the test down, then start T016.

  python3 scripts/t016_cutover.py unit
  python3 scripts/t016_cutover.py smoke
  python3 scripts/t016_cutover.py production
  python3 scripts/t016_cutover.py all

`all` runs unit tests, a live OPEN (smoke), closes that LP, then the T016 OPEN.
LaunchAgents stay stopped until the production position is in range, so the
watchdog cannot hard-restart mid-test.

Width stays 1.0 and threshold stays 0.05. This does not fund the $800 book.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mainnet_lib import (  # noqa: E402
    DEFAULT_WALLET,
    MAINNET_NETWORK,
    MAINNET_POOL,
    MAINNET_PREFIX,
    ApiClient,
    _docker_bin,
    bot_status,
    close_position,
    matching_bots,
    positions_owned,
    utc_now,
)

RUN_ID = "T016_mainnet_100_hb217_20260928"
SRC_DUST = ROOT / "src" / "orca_tight_range" / "dust_floor.py"
MOUNTED_DUST = (
    Path.home()
    / "proj/hummingbot-v216/hummingbot-api/bots/controllers/generic/lp_rebalancer/dust_floor.py"
)
LAUNCH_AGENTS = Path.home() / "Library" / "LaunchAgents"
AGENT_PLISTS = (
    "com.hummingbot.mainnet-watchdog.plist",
    "com.hummingbot.mainnet-reporter.plist",
)
DUST_MARKERS = ("NO_ROUTE_FOUND", "swap SELL 0.000000", "SELL 0.000000 on SOL-USDC")


def log(msg: str) -> None:
    print(f"[{utc_now()}] {msg}", flush=True)


def sync_dust() -> None:
    MOUNTED_DUST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC_DUST, MOUNTED_DUST)
    log(f"synced dust floor -> {MOUNTED_DUST}")


def run_unit() -> int:
    log("unit tests")
    pytest_bin = shutil.which("pytest")
    cmd = [pytest_bin] if pytest_bin else [sys.executable, "-m", "pytest"]
    cmd += ["tests/test_dust_floor.py", "tests/test_watchdog_flat.py", "-q"]
    proc = subprocess.run(cmd, cwd=str(ROOT))
    return proc.returncode


def _uid() -> int:
    return os.getuid()


def pause_agents() -> None:
    uid = _uid()
    for name in AGENT_PLISTS:
        label = name.replace(".plist", "")
        subprocess.run(
            ["launchctl", "bootout", f"gui/{uid}/{label}"],
            check=False,
            capture_output=True,
            text=True,
        )
        log(f"paused {label}")


def resume_agents() -> None:
    uid = _uid()
    for name in AGENT_PLISTS:
        src = ROOT / "scripts" / name
        dst = LAUNCH_AGENTS / name
        shutil.copyfile(src, dst)
        subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(dst)], check=True)
        log(f"started {dst}")


def ops(*args: str) -> int:
    cmd = [sys.executable, str(ROOT / "scripts" / "mainnet_bot_ops.py"), *args]
    log("ops " + " ".join(args))
    return subprocess.call(cmd, cwd=str(ROOT))


def _client() -> ApiClient:
    return ApiClient()


def _running(client: ApiClient) -> list[str]:
    status = bot_status(client)
    bots = matching_bots(status, MAINNET_PREFIX)
    return [n for n, m in bots.items() if (m or {}).get("status") == "running"]


def _positions(client: ApiClient) -> list[dict]:
    return positions_owned(client, network=MAINNET_NETWORK, pool=MAINNET_POOL, wallet=DEFAULT_WALLET)


def wait_in_range(client: ApiClient, timeout_s: int) -> dict | None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        pos = _positions(client)
        running = _running(client)
        if len(running) == 1 and len(pos) == 1 and pos[0].get("in_range") is True:
            return pos[0]
        time.sleep(5)
    return None


def dust_hits(container: str) -> list[str]:
    proc = subprocess.run(
        [_docker_bin(), "logs", container],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    text = (proc.stdout or "") + (proc.stderr or "")
    hits = []
    for line in text.splitlines():
        if any(marker in line for marker in DUST_MARKERS):
            hits.append(line.strip())
    return hits


def flatten(client: ApiClient) -> int:
    """Stop bots first, then close every LP. A live bot would reopen a close."""
    log(f"flatten: stop bots before close; currently bots={_running(client)}")
    code = ops("cleanup")
    if code != 0:
        return code
    time.sleep(2)
    pos = _positions(client)
    log(f"flatten: {len(pos)} position(s) after bot stop")
    for p in pos:
        addr = p.get("position_address")
        if not addr:
            continue
        closed = False
        last_err = ""
        for attempt in range(1, 4):
            log(f"close {addr} attempt {attempt}/3")
            try:
                close_position(
                    client,
                    network=MAINNET_NETWORK,
                    position_address=addr,
                    wallet=DEFAULT_WALLET,
                    pool=MAINNET_POOL,
                    slippage_pct=2.0,
                )
                closed = True
                break
            except Exception as e:
                last_err = str(e)
                log(f"close failed: {last_err[:400]}")
                time.sleep(8)
        if not closed:
            still = [p.get("position_address") for p in _positions(client)]
            if addr not in still:
                log(f"close tx uncertain but {addr} is gone")
            else:
                log(f"close exhausted retries: {last_err[:400]}")
                return 1
    deadline = time.time() + 180
    while time.time() < deadline:
        if len(_positions(client)) == 0:
            break
        time.sleep(5)
    else:
        log("flatten: position still open after close")
        return 1
    if _running(client):
        code = ops("cleanup")
        if code != 0:
            return code
    left = _positions(client)
    running = _running(client)
    if left or running:
        log(f"flatten incomplete positions={len(left)} running={running}")
        return 1
    log("flat: 0 LP, 0 bots")
    return 0


def _open_and_check(client: ApiClient, label: str) -> int:
    code = ops("--wait-s", "300", "hard-restart")
    log(f"{label} hard-restart exit {code}")
    pos = wait_in_range(client, 120)
    if pos is None:
        log(f"{label} FAIL: no in-range LP")
        return 1
    addr = pos.get("position_address")
    log(f"{label} in-range {addr}")
    log(f"{label} waiting 45s for a dust retry loop")
    time.sleep(45)
    running = _running(client)
    if len(running) != 1:
        log(f"{label} FAIL: expected 1 bot, saw {running}")
        return 1
    hits = dust_hits(running[0])
    if hits:
        log(f"{label} FAIL: dust markers in {running[0]}")
        for line in hits[:8]:
            log(line[:300])
        return 1
    log(f"{label} PASS: in-range, no dust sell")
    return 0


def smoke() -> int:
    client = _client()
    log("smoke: tear down current book")
    if flatten(client) != 0:
        return 1
    log("smoke: open a test LP")
    code = _open_and_check(client, "smoke")
    log("smoke: tear down the test LP")
    flat_code = flatten(client)
    if code != 0:
        return code
    return flat_code


def production() -> int:
    client = _client()
    if _positions(client) or _running(client):
        log("production: book not flat; tearing down first")
        if flatten(client) != 0:
            return 1
    log(f"production: start {RUN_ID}")
    code = _open_and_check(client, "production")
    if code != 0:
        log("production FAIL — LaunchAgents left stopped")
        return code
    resume_agents()
    log(f"production PASS {RUN_ID}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase", choices=("unit", "smoke", "production", "all"))
    args = p.parse_args()

    if args.phase == "unit":
        sync_dust()
        return run_unit()

    if args.phase == "all":
        sync_dust()
        if run_unit() != 0:
            return 1
        pause_agents()
        if smoke() != 0:
            log("smoke failed — production not started, LaunchAgents still stopped")
            return 1
        return production()

    sync_dust()
    pause_agents()
    if args.phase == "smoke":
        return smoke()
    return production()


if __name__ == "__main__":
    raise SystemExit(main())
