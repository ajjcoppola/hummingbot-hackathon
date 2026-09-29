from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

from cup_clmm_engine import napkin, rejects_200x_only  # noqa: E402


def test_napkin_numbers():
    n = napkin()
    assert n.turnover > 5.0
    assert 0.002 < n.fee_intensity_full_liquidity < 0.01
    # $800 share of pool fee stream ≈ vol*fee*(800/reserve) ≈ $2–3/day ceiling at 1x
    assert 1.0 < n.fee_usd_per_day_at_1x < 5.0
    assert n.fee_usd_per_day_at_20x == n.fee_usd_per_day_at_1x * 20


def test_rejects_200x_only():
    assert rejects_200x_only(False, False, True) is True
    assert rejects_200x_only(True, False, True) is False
    assert rejects_200x_only(False, True, True) is False
