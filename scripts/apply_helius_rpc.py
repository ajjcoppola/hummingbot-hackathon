#!/usr/bin/env python3
"""Apply HELIUS_API_KEY into local Gateway conf (outside this git repo).

Reads HELIUS_API_KEY from the environment. Never prints or commits the key.
Updates:
  hummingbot-api/bots/gateway-files/conf/apiKeys.yml  (helius:)
  .../chains/solana/devnet.yml                         (nodeURL)
  .../chains/solana/mainnet-beta.yml                   (nodeURL) when --mainnet

Usage:
  export HELIUS_API_KEY='...'
  python3 scripts/apply_helius_rpc.py
  python3 scripts/apply_helius_rpc.py --mainnet
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

DEFAULT_GATEWAY_CONF = (
    Path.home() / "proj/hummingbot-v216/hummingbot-api/bots/gateway-files/conf"
)
DEVNET_URL = "https://devnet.helius-rpc.com/?api-key={key}"
MAINNET_URL = "https://mainnet.helius-rpc.com/?api-key={key}"


def set_yaml_scalar(path: Path, key: str, value: str) -> None:
    text = path.read_text()
    pat = re.compile(rf"^({re.escape(key)}:\s*)(.*)$", re.M)
    if not pat.search(text):
        raise SystemExit(f"{path}: missing key {key!r}")
    # Quote URLs that contain ? or &
    if any(c in value for c in "?&#:") and not (value.startswith("'") or value.startswith('"')):
        rendered = f"'{value}'"
    elif value == "" or value.lower() in {"''", '""'}:
        rendered = "''"
    else:
        rendered = value
    new_text, n = pat.subn(rf"\g<1>{rendered}", text, count=1)
    if n != 1:
        raise SystemExit(f"{path}: failed to rewrite {key}")
    path.write_text(new_text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conf-root", type=Path, default=DEFAULT_GATEWAY_CONF)
    ap.add_argument("--mainnet", action="store_true", help="Also point mainnet-beta at Helius")
    ap.add_argument("--devnet-only", action="store_true", help="Only touch devnet (default)")
    args = ap.parse_args()

    key = os.environ.get("HELIUS_API_KEY", "").strip()
    if not key or key.lower() in {"your-key", "changeme", "***"}:
        print(
            "ERROR: set HELIUS_API_KEY in the environment first "
            "(https://dashboard.helius.dev/). Key is never written into this repo.",
            file=sys.stderr,
        )
        return 2

    conf = args.conf_root
    api_keys = conf / "apiKeys.yml"
    devnet = conf / "chains/solana/devnet.yml"
    mainnet = conf / "chains/solana/mainnet-beta.yml"
    for p in (api_keys, devnet):
        if not p.exists():
            print(f"ERROR: missing {p}", file=sys.stderr)
            return 2

    set_yaml_scalar(api_keys, "helius", f"'{key}'")
    set_yaml_scalar(devnet, "nodeURL", DEVNET_URL.format(key=key))
    touched = ["apiKeys.yml", "chains/solana/devnet.yml"]

    if args.mainnet:
        if not mainnet.exists():
            print(f"ERROR: missing {mainnet}", file=sys.stderr)
            return 2
        set_yaml_scalar(mainnet, "nodeURL", MAINNET_URL.format(key=key))
        touched.append("chains/solana/mainnet-beta.yml")

    print("OK: wrote Helius into Gateway conf (key redacted):")
    for t in touched:
        print(f"  - {t}")
    print("Restart Gateway next, then verify pool-info / positions_owned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
