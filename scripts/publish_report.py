#!/usr/bin/env python3
"""Turn the canonical Cup letter into channel drafts.

Source of truth: docs/blog/in-and-out-orca-cup.md
Writes docs/publish/{substack,medium,linkedin,x_thread}.*

Posting is opt-in and secret-gated. This script never reads or writes tokens
into the repo. With no tokens it prints what is missing and exits 0 after
writing drafts (delivery status: skipped).

  python3 scripts/publish_report.py            # drafts only
  python3 scripts/publish_report.py --post     # post where env tokens exist

Env (all optional; never commit):
  X_ACCESS_TOKEN + X_ACCESS_SECRET + X_API_KEY + X_API_SECRET
      OAuth 1.0a user context. App-only bearer tokens cannot post.
  LINKEDIN_ACCESS_TOKEN + LINKEDIN_AUTHOR_URN   (urn:li:person:...)
  MEDIUM_INTEGRATION_TOKEN                      (legacy; Medium stopped issuing new ones)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "blog" / "in-and-out-orca-cup.md"
OUT = ROOT / "docs" / "publish"
TITLE = "In and Out | The Orca Cup"
CANONICAL = "https://investitnow.substack.com"
X_HANDLE = "@alananjcoppola"


def load() -> str:
    return SOURCE.read_text(encoding="utf-8")


def strip_front(md: str) -> str:
    return re.sub(r"^# .+\n", "", md, count=1).strip()


def tldr(md: str) -> str:
    m = re.search(r"## TLDR\n\n(.*?)(?:\n---|\n# )", md, re.S)
    return (m.group(1).strip() if m else "").replace("**", "")


def linkedin(md: str) -> str:
    body = tldr(md)
    lines = [
        "We ran a 48-hour shadow of the Hummingbot Orca Cup on SOL-USDC.",
        "SOL fell about 8%. A plain liquidity position lost 6.6%.",
        "The two official Orca drivers lost 0.6% and 1.8% by stepping out of inventory.",
        "",
        "After the fact, on 27 days of real 5-minute data (rules chosen before the Cup):",
        "sit in USDC, and only after a high-volume flush buy SOL and sell the bounce",
        "through a fee-earning Orca band. Replay: +0.4% in the Cup, +7.8% over 27 days",
        "while SOL fell 8%. Seven trades. A research result, not a live claim.",
        "",
        body,
        "",
        f"Full letter: {CANONICAL}",
        "Not investment advice. Past windows are not future results.",
    ]
    text = "\n".join(lines)
    return text[:2900]


def tweets(md: str) -> list[str]:
    bits = [
        "We shadowed the Hummingbot Orca Cup on SOL-USDC. SOL fell ~8% in 48h. Our plain LP lost 6.6% (~$53 on an $800 scale). Fees were about $0.63. Volume is not profit.",
        "Orca's two live drivers lost less on a real $800: Victor −0.59% (leave when vol is extreme) and Hoang −1.82% (trend-shaped range). Same order of volume. They refused inventory. We didn't.",
        "On this pool, fees roughly equal the LP's loss to arbitrage. Tighter bands and faster trend switches did not help: 0 of 3,600 fast-regime variants made money in the Cup window.",
        "What did, with rules frozen before the Cup: sit in USDC. After a ≥3% drop in 6h on ≥2× volume, buy the bounce and sell it through a SOL-only Orca band (+2%) that earns the swap fee.",
        "Replay, not live: +0.41% in the 48h Cup (ahead of both drivers) and +7.8% over 27 days while SOL fell 8.1%. Seven trades. A 2% stop instead of 4% flips the Cup to −1.5%. Small sample.",
        f"Full letter on {CANONICAL}. Orca/Solana only. Not advice. {X_HANDLE}",
    ]
    out = []
    for i, b in enumerate(bits, 1):
        prefix = f"{i}/{len(bits)} "
        chunk = prefix + b
        if len(chunk) > 280:
            raise SystemExit(f"tweet {i} is {len(chunk)} chars")
        out.append(chunk)
    return out


def medium(md: str) -> str:
    return (
        "---\n"
        f"title: {TITLE}\n"
        "tags: [investing, crypto, solana, market-making]\n"
        f"canonicalUrl: {CANONICAL}\n"
        "---\n\n"
        + md
    )


def write_drafts(md: str) -> dict[str, Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "substack": OUT / "substack.md",
        "medium": OUT / "medium.md",
        "linkedin": OUT / "linkedin.txt",
        "x": OUT / "x_thread.txt",
    }
    published = md.replace("](images/", "](../blog/images/")
    files["substack"].write_text(published if published.endswith("\n") else published + "\n", encoding="utf-8")
    files["medium"].write_text(medium(published), encoding="utf-8")
    files["linkedin"].write_text(linkedin(md) + "\n", encoding="utf-8")
    files["x"].write_text("\n\n".join(tweets(md)) + "\n", encoding="utf-8")
    return files


def post_x(thread: list[str]) -> str:
    # OAuth 1.0a signing is intentionally not vendored. Delivery stays manual
    # until a user-context token helper is added; we still fail closed.
    need = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"]
    missing = [k for k in need if not os.environ.get(k)]
    if missing:
        return "skipped (missing " + ", ".join(missing) + ")"
    return "skipped (OAuth1 signer not bundled; drafts are in docs/publish/x_thread.txt)"


def post_linkedin(text: str) -> str:
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    urn = os.environ.get("LINKEDIN_AUTHOR_URN")
    if not token or not urn:
        return "skipped (missing LINKEDIN_ACCESS_TOKEN or LINKEDIN_AUTHOR_URN)"
    body = json.dumps(
        {
            "author": urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
    ).encode()
    req = urllib.request.Request(
        "https://api.linkedin.com/v2/ugcPosts",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return f"posted HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        return f"failed HTTP {e.code}"


def post_medium(md: str) -> str:
    token = os.environ.get("MEDIUM_INTEGRATION_TOKEN")
    if not token:
        return "skipped (missing MEDIUM_INTEGRATION_TOKEN; Medium no longer issues new ones)"
    req = urllib.request.Request(
        "https://api.medium.com/v1/me",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            me = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return f"failed user lookup HTTP {e.code}"
    user_id = me["data"]["id"]
    body = json.dumps(
        {
            "title": TITLE,
            "contentFormat": "markdown",
            "content": md,
            "publishStatus": "draft",
            "canonicalUrl": CANONICAL,
            "tags": ["investing", "crypto", "solana"],
        }
    ).encode()
    req = urllib.request.Request(
        f"https://api.medium.com/v1/users/{user_id}/posts",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return f"drafted HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        return f"failed HTTP {e.code}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true", help="Post where env tokens exist")
    args = ap.parse_args()
    md = load()
    files = write_drafts(md)
    for name, path in files.items():
        print(f"draft {name}: {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")
    print("substack: no official publish API — import docs/publish/substack.md in the Substack editor")
    if not args.post:
        print("delivery: drafts only (pass --post to attempt X / LinkedIn / Medium)")
        return 0
    print("x:", post_x(tweets(md)))
    print("linkedin:", post_linkedin(files["linkedin"].read_text(encoding="utf-8")))
    print("medium:", post_medium(md))
    print("substack: skipped (no publish API)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
