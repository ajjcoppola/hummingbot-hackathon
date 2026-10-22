#!/usr/bin/env python3
"""Render the Orca Cup comparison charts used in the letter.

Reads research/artifacts/r004_summary.json (same series as the Cursor canvas
orca-cup-who-lost-less) and writes PNGs to docs/blog/images/.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "research" / "artifacts" / "r004_summary.json"
OUT = ROOT / "docs" / "blog" / "images"

INK = "#1c1917"
MUTED = "#78716c"
GRID = "#e7e5e4"
GREEN = "#3f6212"
RED = "#9f1239"
BLUE = "#1e3a5f"
AMBER = "#92400e"


def style(ax, title: str, ylabel: str) -> None:
    ax.set_title(title, loc="left", color=INK, fontsize=13, pad=10)
    ax.set_ylabel(ylabel, color=INK)
    ax.tick_params(colors=INK)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def save(fig, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def ending_bar() -> None:
    # Same six bars as the canvas, in the same order.
    names = [
        "Flush & Fade\n(replay)",
        "Hold USDC",
        "Victor Adaptive\n(live $800)",
        "Hoang Trend-Aware\n(live $800)",
        "50/50 hold",
        "Naked 16% LP\n(shadow, scaled)",
    ]
    values = [803.3, 800.0, 795.3, 785.4, 772.3, 746.9]
    colors = [GREEN, MUTED, BLUE, BLUE, MUTED, RED]
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    y = list(range(len(names)))[::-1]
    ax.barh(y, values, color=colors, height=0.62)
    ax.axvline(800, color=INK, linewidth=0.8, linestyle="--")
    ax.set_yticks(y)
    ax.set_yticklabels(names, color=INK)
    ax.set_xlim(730, 820)
    for yi, v in zip(y, values):
        ax.text(v + 1.2, yi, f"${v:.1f}", va="center", color=INK, fontsize=9)
    style(ax, "Ending value of $800 after the Cup window", "USD")
    ax.set_xlabel("Book value at 2026-10-09 02:00Z (USD)", color=INK)
    fig.text(
        0.01,
        -0.02,
        "Canvas: Orca Cup Who Lost Less. Shadow scaled from $158. Replay is not a live fill. Board fetched 2026-10-17.",
        color=MUTED,
        fontsize=8,
    )
    save(fig, "cup-ending-800.png")


def equity() -> None:
    data = json.loads(SUMMARY.read_text())
    w = data["windows"]["all_27d"]
    start = datetime.fromisoformat(w["from"])
    n = len(w["rows"]["flush_fade"]["curve"])
    times = [start + timedelta(hours=3 * i) for i in range(n)]
    px = w["rows"]["sol_px"]
    hodl = [800 * (0.5 + 0.5 * px[i] / px[0]) for i in range(n)]
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    cup0 = datetime(2026, 10, 7, 2, tzinfo=timezone.utc)
    cup1 = datetime(2026, 10, 9, 2, tzinfo=timezone.utc)
    ax.axvspan(cup0, cup1, color="#f5f5f4", zorder=0)
    ax.plot(times, w["rows"]["flush_fade"]["curve"], color=GREEN, linewidth=2.0, label="Flush & Fade")
    ax.plot(times, w["rows"]["naked_16"]["curve"], color=RED, linewidth=1.4, label="Naked 16% LP")
    ax.plot(times, hodl, color=MUTED, linewidth=1.2, label="50/50 SOL/USDC hold")
    ax.axhline(800, color=INK, linewidth=0.6, linestyle="--")
    ax.legend(frameon=False, loc="upper left")
    style(ax, "27-day equity of an $800 book", "USD")
    ax.set_xlabel("UTC, 2026-09-21 to 2026-10-17. Shaded band is the 48h Cup.", color=INK)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    fig.text(
        0.01,
        -0.04,
        "Replay on 5-minute Czfq candles. Fees calibrated from our own pre-Cup LP. Flat stretches of Flush & Fade are USDC.",
        color=MUTED,
        fontsize=8,
    )
    save(fig, "equity-27d.png")


def cup_zoom() -> None:
    data = json.loads(SUMMARY.read_text())
    w = data["windows"]["cup_48h"]
    start = datetime.fromisoformat(w["from"])
    px = w["rows"]["sol_px"]
    times = [start + timedelta(minutes=60 * i) for i in range(len(px))]
    # curve was saved every 12 five-minute bars = 60 minutes
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    ax.plot(times, px, color=BLUE, linewidth=1.6, label="SOL (Czfq)")
    entry = datetime(2026, 10, 8, 15, 40, tzinfo=timezone.utc)
    ax.axvline(entry, color=GREEN, linewidth=1.2, linestyle="--", label="Flush & Fade buys")
    ax.annotate(
        "buy 109.02\nafter the flush",
        xy=(entry, 109.02),
        xytext=(entry - timedelta(hours=18), 114.5),
        color=GREEN,
        fontsize=9,
        arrowprops={"arrowstyle": "->", "color": GREEN},
    )
    style(ax, "Cup window: SOL fell, the rule bought the flush", "SOL price (USD)")
    ax.set_xlabel("UTC, 2026-10-07 02:00Z through 2026-10-09", color=INK)
    ax.legend(frameon=False, loc="upper right")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H"))
    fig.autofmt_xdate()
    save(fig, "cup-sol-and-entry.png")


def same_path() -> None:
    data = json.loads(SUMMARY.read_text())
    rows = data["windows"]["cup_48h"]["rows"]
    labels = [
        "Flush & Fade",
        "Hold USDC",
        "50/50 hold",
        "Hoang-style proxy",
        "Fast trend switch",
        "Victor-style proxy",
        "Naked 16% LP",
    ]
    vals = [
        rows["flush_fade"]["ret_pct"],
        0.0,
        rows["hodl_5050"]["ret_pct"],
        rows["hoang_proxy"]["ret_pct"],
        rows["fast_trend_regime"]["ret_pct"],
        rows["victor_proxy"]["ret_pct"],
        rows["naked_16"]["ret_pct"],
    ]
    colors = [GREEN if v > 0 else (MUTED if v == 0 else RED) for v in vals]
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    y = list(range(len(labels)))[::-1]
    ax.barh(y, vals, color=colors, height=0.62)
    ax.axvline(0, color=INK, linewidth=0.8)
    ax.set_xlim(-8.5, 2.4)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=INK)
    for yi, v in zip(y, vals):
        ax.text(0.12, yi, f"{v:+.2f}%", va="center", ha="left", color=INK, fontsize=9)
    style(ax, "Same 48h candles: what each rule returned", "Return (%)")
    ax.set_xlabel("Cup window replay. Proxies are our code, not Victor's or Hoang's live fills.", color=INK)
    save(fig, "cup-replay-returns.png")


def main() -> None:
    ending_bar()
    equity()
    cup_zoom()
    same_path()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
