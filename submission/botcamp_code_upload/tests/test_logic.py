from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from orca_tight_range.logic import (
    Action,
    Event,
    Params,
    Position,
    Snapshot,
    compute_range,
    decide,
    is_exhaustion,
)


def test_symmetric_range():
    lower, upper, center = compute_range(Decimal("100"), Params(skew_bias=Decimal("0.5")), 0)
    assert lower == Decimal("98.5")
    assert upper == Decimal("101.5")
    assert center == Decimal("100")


def test_up_skew_extends_above():
    lower, upper, _ = compute_range(Decimal("100"), Params(), 1)
    assert upper - Decimal("100") > Decimal("100") - lower


def test_opens_when_flat():
    d = decide(
        Params(),
        Snapshot(ts=0, spot=Decimal("150"), equity_usdc=Decimal("800"), momentum_sign=0),
        None,
    )
    assert d.action == Action.OPEN
    assert d.event == Event.RANGE_OPENED


def test_holds_in_range():
    pos = Position(
        lower=Decimal("148"),
        upper=Decimal("152"),
        center=Decimal("150"),
        opened_at=0,
        opened_equity=Decimal("800"),
    )
    d = decide(
        Params(),
        Snapshot(ts=1, spot=Decimal("150.2"), equity_usdc=Decimal("800"), momentum_sign=0),
        pos,
    )
    assert d.action == Action.HOLD
    assert d.event == Event.HOLD


def test_stop_loss():
    pos = Position(
        lower=Decimal("148"),
        upper=Decimal("152"),
        center=Decimal("150"),
        opened_at=0,
        opened_equity=Decimal("800"),
    )
    d = decide(
        Params(),
        Snapshot(ts=1, spot=Decimal("150"), equity_usdc=Decimal("600"), momentum_sign=0),
        pos,
    )
    assert d.action == Action.STOP
    assert d.event == Event.STOP_LOSS_TRIGGERED


def test_exhaustion_defers_rebalance():
    pos = Position(
        lower=Decimal("148"),
        upper=Decimal("152"),
        center=Decimal("150"),
        opened_at=0,
        opened_equity=Decimal("800"),
    )
    quiet = [Decimal("0.001")] * 8
    flush = quiet + [Decimal("-0.04")]
    assert is_exhaustion(flush, Params())
    d = decide(
        Params(),
        Snapshot(
            ts=10,
            spot=Decimal("140"),
            equity_usdc=Decimal("800"),
            momentum_sign=-1,
            recent_returns=flush,
        ),
        pos,
    )
    assert d.event == Event.REBALANCE_DEFERRED


def test_rate_limit():
    pos = Position(
        lower=Decimal("148"),
        upper=Decimal("152"),
        center=Decimal("150"),
        opened_at=0,
        opened_equity=Decimal("800"),
    )
    stamps = [1000.0 + i * 60 for i in range(6)]
    d = decide(
        Params(),
        Snapshot(
            ts=1000.0 + 6 * 60,
            spot=Decimal("140"),
            equity_usdc=Decimal("800"),
            momentum_sign=-1,
            recent_returns=[Decimal("0.001")] * 8,
            rebalance_timestamps=stamps,
        ),
        pos,
    )
    assert d.event == Event.RATE_LIMITED
