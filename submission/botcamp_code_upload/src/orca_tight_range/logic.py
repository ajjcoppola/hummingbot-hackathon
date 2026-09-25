"""Pure decision logic for the Orca tight-range Whirlpool agent.

This module has no Hummingbot, Gateway, or zipline imports so it can be
tested tonight and reused by:

- the V2 controller drop-in
- the zipline / pandas backtest
- the YAML bridge
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Sequence


class Event(str, Enum):
    RANGE_OPENED = "RangeOpened"
    RANGE_EXITED = "RangeExited"
    REBALANCE_EXECUTED = "RebalanceExecuted"
    REBALANCE_DEFERRED = "RebalanceDeferred"
    RATE_LIMITED = "RateLimited"
    STOP_LOSS_TRIGGERED = "StopLossTriggered"
    HOLD = "Hold"


class Action(str, Enum):
    OPEN = "open"
    REBALANCE = "rebalance"
    HOLD = "hold"
    STOP = "stop"


@dataclass(frozen=True)
class Params:
    """Competition defaults from the Perplexity Orca plan + Botcamp $800 cap."""

    range_width_pct: Decimal = Decimal("1.5")
    skew_bias: Decimal = Decimal("0.6")
    rebalance_trigger_pct: Decimal = Decimal("0.8")
    volatility_exhaustion_window_s: int = 300
    max_rebalances_per_hour: int = 6
    capital_allocation_usdc: Decimal = Decimal("800")
    stop_loss_drawdown_pct: Decimal = Decimal("15")
    gas_sol_per_rebalance: Decimal = Decimal("0.01")
    exhaustion_return_z: Decimal = Decimal("3")


@dataclass
class Position:
    lower: Decimal
    upper: Decimal
    center: Decimal
    opened_at: float
    opened_equity: Decimal


@dataclass
class Snapshot:
    """One decision tick."""

    ts: float
    spot: Decimal
    equity_usdc: Decimal
    momentum_sign: int  # -1, 0, +1
    recent_returns: Sequence[Decimal] = field(default_factory=tuple)
    rebalance_timestamps: Sequence[float] = field(default_factory=tuple)


@dataclass
class Decision:
    action: Action
    event: Event
    lower: Optional[Decimal] = None
    upper: Optional[Decimal] = None
    center: Optional[Decimal] = None
    reason: str = ""


def _pct(value: Decimal) -> Decimal:
    return value / Decimal("100")


def compute_range(
    spot: Decimal,
    params: Params,
    momentum_sign: int,
) -> tuple[Decimal, Decimal, Decimal]:
    """Return (lower, upper, center) for a tight CLMM band around spot.

    ``range_width_pct`` is the half-width in percent (1.5 => ±1.5%).
    ``skew_bias`` > 0.5 allocates more of the band to the momentum side so
    the position stays in-range longer if the short-term bet is right.
    """
    if spot <= 0:
        raise ValueError("spot must be positive")
    half = spot * _pct(params.range_width_pct)
    if momentum_sign > 0:
        up_frac = params.skew_bias
    elif momentum_sign < 0:
        up_frac = Decimal("1") - params.skew_bias
    else:
        up_frac = Decimal("0.5")
    down_frac = Decimal("1") - up_frac
    lower = spot - (half * Decimal("2") * down_frac)
    upper = spot + (half * Decimal("2") * up_frac)
    if lower <= 0:
        lower = spot * Decimal("0.0001")
    center = (lower + upper) / Decimal("2")
    return lower, upper, center


def in_range(spot: Decimal, lower: Decimal, upper: Decimal) -> bool:
    return lower <= spot <= upper


def deviation_from_center_pct(spot: Decimal, center: Decimal) -> Decimal:
    if center <= 0:
        return Decimal("0")
    return abs(spot - center) / center * Decimal("100")


def is_exhaustion(returns: Sequence[Decimal], params: Params) -> bool:
    """True when a short-horizon return spike looks like a flush, not a trend.

    Uses a simple z-score on the last return vs the lookback window. A
    genuine trend should keep printing, so we only defer a single violent bar.
    """
    if len(returns) < 4:
        return False
    last = Decimal(str(returns[-1]))
    body = [Decimal(str(x)) for x in returns[:-1]]
    mean = sum(body) / Decimal(len(body))
    var = sum((x - mean) ** 2 for x in body) / Decimal(len(body))
    if var <= 0:
        return abs(last) > _pct(params.range_width_pct)
    std = var.sqrt()
    z = abs(last - mean) / std
    return z >= params.exhaustion_return_z


def rebalances_in_last_hour(now: float, stamps: Sequence[float]) -> int:
    return sum(1 for t in stamps if now - t <= 3600)


def drawdown_pct(equity: Decimal, peak: Decimal) -> Decimal:
    if peak <= 0:
        return Decimal("0")
    return (peak - equity) / peak * Decimal("100")


def decide(params: Params, snap: Snapshot, position: Optional[Position]) -> Decision:
    """Single-tick policy used by live controller and offline backtest."""
    if snap.equity_usdc <= 0 or snap.spot <= 0:
        return Decision(Action.STOP, Event.STOP_LOSS_TRIGGERED, reason="invalid equity or spot")

    if position and drawdown_pct(snap.equity_usdc, position.opened_equity) >= params.stop_loss_drawdown_pct:
        return Decision(
            Action.STOP,
            Event.STOP_LOSS_TRIGGERED,
            reason=f"drawdown >= {params.stop_loss_drawdown_pct}%",
        )

    if position is None:
        lower, upper, center = compute_range(snap.spot, params, snap.momentum_sign)
        return Decision(
            Action.OPEN,
            Event.RANGE_OPENED,
            lower=lower,
            upper=upper,
            center=center,
            reason="no active position",
        )

    if in_range(snap.spot, position.lower, position.upper):
        return Decision(Action.HOLD, Event.HOLD, reason="price still in range")

    exited = Decision(Action.HOLD, Event.RANGE_EXITED, reason="price left tick range")
    if deviation_from_center_pct(snap.spot, position.center) < params.rebalance_trigger_pct:
        return Decision(
            Action.HOLD,
            Event.HOLD,
            reason=f"exited but deviation < {params.rebalance_trigger_pct}% trigger",
        )

    if is_exhaustion(snap.recent_returns, params):
        return Decision(
            Action.HOLD,
            Event.REBALANCE_DEFERRED,
            reason="volatility-exhaustion filter: defer recenter during flush",
        )

    if rebalances_in_last_hour(snap.ts, snap.rebalance_timestamps) >= params.max_rebalances_per_hour:
        return Decision(
            Action.HOLD,
            Event.RATE_LIMITED,
            reason=f"hit max {params.max_rebalances_per_hour} rebalances/hour (gas cap)",
        )

    lower, upper, center = compute_range(snap.spot, params, snap.momentum_sign)
    return Decision(
        Action.REBALANCE,
        Event.REBALANCE_EXECUTED,
        lower=lower,
        upper=upper,
        center=center,
        reason=exited.reason + "; recenter tight band",
    )


def params_to_dict(params: Params) -> dict:
    return {
        "range_width_pct": str(params.range_width_pct),
        "skew_bias": str(params.skew_bias),
        "rebalance_trigger_pct": str(params.rebalance_trigger_pct),
        "volatility_exhaustion_window_s": params.volatility_exhaustion_window_s,
        "max_rebalances_per_hour": params.max_rebalances_per_hour,
        "capital_allocation_usdc": str(params.capital_allocation_usdc),
        "stop_loss_drawdown_pct": str(params.stop_loss_drawdown_pct),
        "gas_sol_per_rebalance": str(params.gas_sol_per_rebalance),
    }


def events_catalog() -> List[str]:
    return [e.value for e in Event]
