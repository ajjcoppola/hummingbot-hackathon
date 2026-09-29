"""Pure decision layer for the dynamic farmer (no Hummingbot import).

Combines pool_rank.decide_switch with logic.decide for the band. The live
controller and the offline harness call the same tick().
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import Decimal
from typing import Any, Optional, Sequence

from orca_tight_range.logic import (
    Action,
    Decision,
    Event,
    Params,
    Position,
    Snapshot,
    decide,
)
from orca_tight_range.pool_rank import (
    PoolSnapshot,
    RankerState,
    SwitchDecision,
    decide_switch,
    score_table,
)

# Race band: 16% full width => logic half-width 8%; trigger 0.5; no hourly cap.
RACE_FULL_WIDTH_PCT = Decimal("16")
RACE_HALF_WIDTH_PCT = RACE_FULL_WIDTH_PCT / Decimal("2")
RACE_TRIGGER_PCT = Decimal("0.5")
RACE_MAX_REBALS_PER_HOUR = 999
RACE_SKEW = Decimal("0.5")


def race_params(capital: Decimal = Decimal("800")) -> Params:
    return Params(
        range_width_pct=RACE_HALF_WIDTH_PCT,
        skew_bias=RACE_SKEW,
        rebalance_trigger_pct=RACE_TRIGGER_PCT,
        max_rebalances_per_hour=RACE_MAX_REBALS_PER_HOUR,
        capital_allocation_usdc=capital,
    )


@dataclass
class FarmerState:
    ranker: RankerState = field(default_factory=RankerState)
    position: Optional[Position] = None
    rebalance_timestamps: list[float] = field(default_factory=list)
    opened_equity: Optional[Decimal] = None
    halted: bool = False
    switch_count_48h: int = 0
    last_score_table: list[dict[str, Any]] = field(default_factory=list)
    last_ml_shadow: Optional[str] = None
    race_end_ts: Optional[float] = None  # unix; hours_left derived from this


@dataclass(frozen=True)
class FarmerTick:
    """One controller / harness decision."""

    band: Decision
    switch: SwitchDecision
    pool_address: Optional[str]
    score_table: list[dict[str, Any]] = field(default_factory=list)
    ml_shadow_address: Optional[str] = None
    frozen: bool = False
    reason: str = ""


def hours_left(now_ts: float, race_end_ts: Optional[float], default: float = 48.0) -> float:
    if race_end_ts is None:
        return default
    return max(0.0, (race_end_ts - now_ts) / 3600.0)


def tick(
    state: FarmerState,
    *,
    now_ts: float,
    spot: Decimal,
    equity: Decimal,
    momentum_sign: int,
    recent_returns: Sequence[Decimal],
    pools: Sequence[PoolSnapshot] | None,
    scan_error: Optional[str] = None,
    params: Optional[Params] = None,
    ml_shadow_address: Optional[str] = None,
    do_rank: bool = True,
) -> tuple[FarmerTick, FarmerState]:
    """Advance one decision tick.

    When do_rank is False (sub-hourly band ticks), keep the current pool and
    only run decide() for the band. Hourly scans should pass do_rank=True.
    """
    new_state = replace(
        state,
        ranker=replace(
            state.ranker,
            switch_timestamps=list(state.ranker.switch_timestamps),
        ),
        rebalance_timestamps=list(state.rebalance_timestamps),
        last_score_table=list(state.last_score_table),
    )
    new_state.last_ml_shadow = ml_shadow_address
    p = params or race_params(equity if equity > 0 else Decimal("800"))

    if new_state.halted:
        empty_sw = SwitchDecision(
            action="freeze",
            target_address=new_state.ranker.current_address,
            reason="halted",
        )
        return (
            FarmerTick(
                band=Decision(Action.HOLD, Event.HOLD, reason="halted"),
                switch=empty_sw,
                pool_address=new_state.ranker.current_address,
                frozen=True,
                reason="halted",
                ml_shadow_address=ml_shadow_address,
            ),
            new_state,
        )

    switch = SwitchDecision(
        action="hold",
        target_address=new_state.ranker.current_address,
        reason="rank_skipped",
    )
    table: list[dict[str, Any]] = list(new_state.last_score_table)

    if do_rank:
        hl = hours_left(now_ts, new_state.race_end_ts)
        switch, ranker = decide_switch(
            pools,
            new_state.ranker,
            now_ts=now_ts,
            equity=float(equity),
            hours_left=hl,
            scan_error=scan_error,
        )
        new_state.ranker = ranker
        table = score_table(switch.ranked, limit=10)
        new_state.last_score_table = table
        new_state.switch_count_48h = sum(
            1 for t in ranker.switch_timestamps if now_ts - t <= 48 * 3600
        )
        if switch.action == "freeze":
            return (
                FarmerTick(
                    band=Decision(Action.HOLD, Event.HOLD, reason="frozen_on_scan"),
                    switch=switch,
                    pool_address=new_state.ranker.current_address,
                    score_table=table,
                    ml_shadow_address=ml_shadow_address,
                    frozen=True,
                    reason=switch.reason,
                ),
                new_state,
            )
        if switch.action in ("open", "switch"):
            # Force a fresh band open on the new pool; clear old position.
            new_state.position = None

    pool_addr = new_state.ranker.current_address
    snap = Snapshot(
        ts=now_ts,
        spot=spot,
        equity_usdc=equity,
        momentum_sign=momentum_sign,
        recent_returns=recent_returns,
        rebalance_timestamps=new_state.rebalance_timestamps,
    )
    band = decide(p, snap, new_state.position)

    if band.action == Action.STOP:
        new_state.halted = True
    elif band.action in (Action.OPEN, Action.REBALANCE) and band.lower and band.upper:
        new_state.position = Position(
            lower=band.lower,
            upper=band.upper,
            center=band.center or ((band.lower + band.upper) / 2),
            opened_at=now_ts,
            opened_equity=new_state.opened_equity or equity,
        )
        if new_state.opened_equity is None:
            new_state.opened_equity = equity
        if band.action == Action.REBALANCE:
            new_state.rebalance_timestamps.append(now_ts)

    reason = f"switch={switch.action}:{switch.reason}; band={band.action.value}:{band.reason}"
    return (
        FarmerTick(
            band=band,
            switch=switch,
            pool_address=pool_addr,
            score_table=table,
            ml_shadow_address=ml_shadow_address,
            frozen=new_state.ranker.frozen,
            reason=reason,
        ),
        new_state,
    )
