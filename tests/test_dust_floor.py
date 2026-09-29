from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from orca_tight_range.dust_floor import skip_dust_swap  # noqa: E402

CONTROLLER = (
    Path.home()
    / "proj/hummingbot-v216/hummingbot-api/bots/controllers/generic/lp_rebalancer"
)
PRICE = Decimal("118")


def test_skips_the_live_dust_quote_deficit():
    # 2026-09-28 17:21Z: need quote 99.000100, have 99.000026, base in surplus.
    assert skip_dust_swap(Decimal("-0.070305"), Decimal("0.000074"), PRICE) is True


def test_keeps_a_real_base_buy():
    assert skip_dust_swap(Decimal("0.36"), Decimal("-50"), PRICE) is False


def test_skips_both_sides_when_the_sum_is_under_the_floor():
    assert skip_dust_swap(Decimal("0.0001"), Decimal("0.01"), PRICE) is True


def test_no_deficit_is_not_a_dust_skip():
    assert skip_dust_swap(Decimal("-1"), Decimal("-1"), PRICE) is False


def test_bad_price_does_not_skip():
    assert skip_dust_swap(Decimal("0"), Decimal("0.000074"), Decimal("0")) is False


def test_controller_calls_the_floor_and_the_mount_matches():
    mounted = (CONTROLLER / "dust_floor.py").read_text()
    source = (ROOT / "src/orca_tight_range/dust_floor.py").read_text()
    controller = (CONTROLLER / "lp_rebalancer.py").read_text()
    assert mounted == source
    assert "skip_dust_swap" in controller
    assert "opening with balances on hand" in controller
