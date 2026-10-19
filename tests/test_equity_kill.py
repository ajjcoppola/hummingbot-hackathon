"""Unit tests for dump-protected −3% equity kill trigger."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from equity_kill import should_kill  # noqa: E402


def test_kill_triggers_at_minus_three_pct():
    open_eq = 158.08
    assert should_kill(open_eq * 0.97, open_eq, 0.03) is True
    assert should_kill(open_eq * 0.969, open_eq, 0.03) is True


def test_no_kill_above_threshold():
    open_eq = 158.08
    assert should_kill(open_eq * 0.971, open_eq, 0.03) is False
    assert should_kill(open_eq, open_eq, 0.03) is False


def test_synthetic_series_first_cross():
    open_eq = 100.0
    series = [100.0, 99.0, 98.0, 97.0, 96.5, 96.0]
    hits = [i for i, e in enumerate(series) if should_kill(e, open_eq, 0.03)]
    assert hits[0] == 3  # 97.0 is exactly −3%
    assert 4 in hits and 5 in hits


def test_bad_open_never_kills():
    assert should_kill(50.0, 0.0, 0.03) is False
    assert should_kill(-1.0, 100.0, 0.03) is False
