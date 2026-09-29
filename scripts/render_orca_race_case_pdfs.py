#!/usr/bin/env python3
"""Regenerate submission/orca_race_case/pdf from canvas series (no network).

Usage:
  MPLCONFIGDIR=$PWD/.mplconfig python3 scripts/render_orca_race_case_pdfs.py
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT  # noqa: F401
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

PDF_DIR = ROOT / "submission" / "orca_race_case" / "pdf"

DAYS = [
    "Sep 7", "Sep 8", "Sep 9", "Sep 10", "Sep 11", "Sep 12", "Sep 13",
    "Sep 14", "Sep 15", "Sep 16", "Sep 17", "Sep 18", "Sep 19", "Sep 20",
    "Sep 21", "Sep 22", "Sep 23", "Sep 24", "Sep 25", "Sep 26", "Sep 27", "Sep 28",
]
BASELINE_LP = [
    792.6, 729.0, 673.9, 586.2, 551.6, 514.5, 482.7, 425.4, 391.9, 381.2, 368.6,
    363.6, 344.2, 329.9, 321.0, 304.7, 285.4, 276.1, 270.2, 259.1, 252.6, 242.8,
]
HODL = [
    796.7, 794.4, 787.3, 778.7, 793.0, 790.1, 780.4, 793.1, 771.5, 778.9, 789.5,
    831.6, 826.6, 826.0, 854.2, 854.5, 841.0, 847.3, 868.5, 863.7, 866.6, 857.7,
]
SIT_WIDE = [
    796.8, 795.3, 787.7, 775.7, 798.1, 795.0, 781.5, 800.6, 768.2, 783.1, 799.9,
    828.2, 828.4, 829.4, 830.5, 830.5, 830.5, 830.6, 830.6, 830.6, 830.6, 830.6,
]
PROMOTED = [
    796.8, 795.3, 787.7, 743.1, 763.6, 760.8, 748.6, 732.5, 705.8, 718.4, 732.4,
    755.3, 752.0, 752.4, 769.8, 771.4, 768.2, 772.5, 780.0, 777.1, 780.6, 774.8,
]


def main() -> int:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    chart_png = PDF_DIR / "cup-800-sim-chart.png"

    with PdfPages(PDF_DIR / "cup-800-sim.pdf") as pdf:
        fig, ax = plt.subplots(figsize=(11, 6.5))
        ax.plot(DAYS, BASELINE_LP, color="#c0392b", lw=2.2, label="Baseline live 1% (20x share)")
        ax.plot(DAYS, SIT_WIDE, color="#2980b9", lw=2.2, label="Sit-wide 16% (1x)")
        ax.plot(DAYS, PROMOTED, color="#27ae60", lw=2.2, label="Promoted 16%/0.5 (1x)")
        ax.plot(DAYS, HODL, color="#7f8c8d", lw=1.8, ls="--", label="Hold opening mix")
        ax.axhline(800, color="#bdc3c7", lw=1, ls=":")
        ax.set_title("Cup money search — USD 800 Czfq3xZZ (R002 offline)")
        ax.set_xlabel("UTC date (2026)")
        ax.set_ylabel("Mark-to-market equity (USDC)")
        ax.legend(loc="upper right", frameon=False)
        ax.set_ylim(200, 900)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.text(
            0.01,
            0.01,
            "Source: GeckoTerminal hourly OHLCV · research/cup_money_search.py · Simulation only",
            fontsize=8,
            color="#666",
        )
        fig.tight_layout(rect=[0, 0.03, 1, 1])
        fig.savefig(chart_png, dpi=160)
        pdf.savefig(fig)
        plt.close(fig)

        fig2, axes = plt.subplots(2, 2, figsize=(11, 8.5))
        fig2.suptitle("cup-800-sim canvas — key stats", fontsize=14)
        stats = [
            ("USD 243", "Baseline end\n1% band, 20x", "#c0392b"),
            ("USD 831", "Sit-wide 16%\nend (1x)", "#2980b9"),
            ("USD 775", "Promoted 16%/0.5\nend (1x) full span", "#27ae60"),
            ("USD 858", "Hold opening mix", "#7f8c8d"),
        ]
        for ax, (val, lab, c) in zip(axes.flat, stats):
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            ax.text(0.5, 0.55, val, ha="center", va="center", fontsize=26, color=c, fontweight="bold")
            ax.text(0.5, 0.25, lab, ha="center", va="center", fontsize=11, color="#333")
        fig2.text(
            0.08,
            0.08,
            "No-loss gate (absolute >= USD 800): sit_wide 16% PASS train +29 / hold +25.\n"
            "Race YAML 16%/0.5 holdout PASS +24. Tight 1%/0.05 NO-GO -557.\n"
            "R003: only Czfq clears TVL>=500k among true SOL-USDC (tokensBothOf).",
            fontsize=10,
            family="monospace",
        )
        fig2.tight_layout(rect=[0, 0.14, 1, 0.95])
        pdf.savefig(fig2)
        plt.close(fig2)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="H", parent=styles["Heading1"], fontSize=18, spaceAfter=10))
    styles.add(ParagraphStyle(name="H2c", parent=styles["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name="Body", parent=styles["Normal"], fontSize=10, leading=13, spaceAfter=6))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.grey))

    doc = SimpleDocTemplate(
        str(PDF_DIR / "orca-race-case.pdf"),
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    story = []
    story.append(Paragraph("Orca race case — Beta Checkpoint", styles["H"]))
    story.append(
        Paragraph(
            "Agent Builders Cup · Hummingbot · Deadline EOD 2026-09-30 · "
            "Entry freeze 2026-10-01 · Race 2026-10-06",
            styles["Small"],
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "<b>Ask:</b> Select us to race for <b>Orca</b> with a wide-band SOL/USDC Whirlpool LP "
            "(16% width / 0.5 threshold on <font face='Courier'>Czfq3xZZ…</font>). "
            "Official Hummingbot <font face='Courier'>lp_rebalancer</font> + Gateway. "
            "Deterministic. LLM does not trade.",
            styles["Body"],
        )
    )
    story.append(Paragraph("Simulation no-loss gate (hard)", styles["H2c"]))
    gate_data = [
        ["Config", "Holdout end", "PnL vs $800", "Verdict"],
        ["Tight 1.0 / 0.05 (old)", "$243", "−$557", "NO-GO"],
        ["sit_wide 16% (open once)", "$825", "+$25 (train +$29)", "PASS both windows"],
        ["Race 16% / 0.5", "$824", "+$24", "Holdout PASS"],
        ["R003 Czfq holdout", "$830", "+$30 (+$9 vs HODL)", "PASS*"],
    ]
    t = Table(gate_data, colWidths=[2.2 * inch, 1.2 * inch, 1.6 * inch, 1.6 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#ccc")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#fdecea")),
                ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#eafaf1")),
                ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#eafaf1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t)
    story.append(Paragraph("* R003 fees use constant-TVL approximation.", styles["Small"]))
    story.append(Spacer(1, 6))
    story.append(Image(str(chart_png), width=7.0 * inch, height=4.1 * inch))
    story.append(PageBreak())
    story.append(Paragraph("Collateral index: submission/orca_race_case/", styles["H2c"]))
    story.append(
        Paragraph(
            "See README.md in this folder. Regenerate with scripts/render_orca_race_case_pdfs.py",
            styles["Body"],
        )
    )
    doc.build(story)
    print("wrote", PDF_DIR / "cup-800-sim.pdf")
    print("wrote", PDF_DIR / "orca-race-case.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
