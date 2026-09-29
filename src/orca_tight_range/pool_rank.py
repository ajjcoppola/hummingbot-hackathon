"""SOL-USDC Orca fee-tier ranker for the dynamic farmer.

Score = min(intensity_24h, intensity_7d) where intensity = (volume / tvl) * fee.
Switch only when a candidate clears a 1.5x two-scan hysteresis AND an expected-fee
gain beats switch cost. Cap switches. Hold on any scan error.
Never invent a pool_address — addresses come verbatim from the Orca API payload.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

# Defaults from the Sherlock race plan.
MIN_TVL_USD = 500_000.0
MAX_FEE_PCT = 1.0  # percent units (1.0 = 1%)
MIN_POOL_AGE_DAYS = 30.0
HYSTERESIS_MULT = 1.5
MAX_SWITCHES_48H = 3
SWITCH_FIXED_USD = 2.0
SWITCH_SLIP_FRAC = 0.001  # 0.1% of equity
DEFAULT_LOOKBACK_S = 48 * 3600


@dataclass(frozen=True)
class PoolSnapshot:
    address: str
    fee_pct: float  # percent, e.g. 0.04
    tvl_usd: float
    volume_24h: float
    volume_7d: float
    has_warning: bool = False
    adaptive_fee: bool = False
    created_at: Optional[str] = None  # ISO8601 if known
    pair: str = "SOL-USDC"
    price: Optional[float] = None
    source_ts: Optional[float] = None

    @property
    def intensity_24h(self) -> float:
        if self.tvl_usd <= 0:
            return 0.0
        return (self.volume_24h / self.tvl_usd) * (self.fee_pct / 100.0)

    @property
    def intensity_7d(self) -> float:
        if self.tvl_usd <= 0:
            return 0.0
        # Normalize 7d volume to a daily rate so it is comparable to 24h.
        daily = self.volume_7d / 7.0
        return (daily / self.tvl_usd) * (self.fee_pct / 100.0)

    @property
    def score(self) -> float:
        return min(self.intensity_24h, self.intensity_7d)


@dataclass
class RankerState:
    current_address: Optional[str] = None
    pending_address: Optional[str] = None
    pending_streak: int = 0
    switch_timestamps: list[float] = field(default_factory=list)
    last_error: Optional[str] = None
    last_scan_ts: Optional[float] = None
    frozen: bool = False


@dataclass(frozen=True)
class SwitchDecision:
    action: str  # "hold" | "open" | "switch" | "freeze"
    target_address: Optional[str]
    reason: str
    ranked: tuple[PoolSnapshot, ...] = ()
    current_score: float = 0.0
    candidate_score: float = 0.0
    switch_cost_usd: float = 0.0
    expected_gain_usd: float = 0.0


def fee_rate_to_pct(fee_rate: Any) -> float:
    """Orca feeRate is hundredths of a bip (400 => 0.04%)."""
    try:
        fr = float(fee_rate)
    except (TypeError, ValueError):
        return 0.0
    if fr > 10:
        return fr / 10_000.0
    if fr > 1:
        return fr / 100.0
    return fr * 100.0  # already a fraction like 0.0004


def _age_days(created_at: Optional[str], now_ts: float) -> Optional[float]:
    if not created_at:
        return None
    try:
        # Accept trailing Z
        s = created_at.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        # Orca sometimes returns the Unix epoch placeholder — treat as unknown.
        if dt.year <= 1971:
            return None
        return max(0.0, (now_ts - dt.timestamp()) / 86400.0)
    except (TypeError, ValueError):
        return None


def passes_hard_filters(
    pool: PoolSnapshot,
    *,
    now_ts: float,
    min_tvl: float = MIN_TVL_USD,
    max_fee_pct: float = MAX_FEE_PCT,
    min_age_days: float = MIN_POOL_AGE_DAYS,
) -> tuple[bool, str]:
    if not pool.address:
        return False, "missing_address"
    if pool.has_warning:
        return False, "hasWarning"
    if pool.tvl_usd < min_tvl:
        return False, f"tvl<{min_tvl:g}"
    if pool.fee_pct <= 0 or pool.fee_pct > max_fee_pct:
        return False, f"fee_pct={pool.fee_pct}"
    age = _age_days(pool.created_at, now_ts)
    if age is not None and age < min_age_days:
        return False, f"age_days<{min_age_days:g}"
    # If age unknown, allow (API often omits createdAt); TVL/fee/warning already gate.
    return True, "ok"


def snapshot_from_orca_row(row: dict[str, Any], *, source_ts: Optional[float] = None) -> PoolSnapshot:
    stats = row.get("stats") or {}
    s24 = stats.get("24h") or {}
    s7 = stats.get("7d") or {}
    token_a = row.get("tokenA") or {}
    token_b = row.get("tokenB") or {}
    pair = f"{token_a.get('symbol', '?')}-{token_b.get('symbol', '?')}"
    created = row.get("poolCreatedAt") or row.get("createdAt") or row.get("tradeEnableTimestamp")
    price = row.get("price")
    try:
        price_f = float(price) if price is not None else None
    except (TypeError, ValueError):
        price_f = None
    return PoolSnapshot(
        address=str(row.get("address") or ""),
        fee_pct=fee_rate_to_pct(row.get("feeRate")),
        tvl_usd=float(row.get("tvlUsdc") or 0.0),
        volume_24h=float(s24.get("volume") or 0.0),
        volume_7d=float(s7.get("volume") or 0.0),
        has_warning=bool(row.get("hasWarning")),
        adaptive_fee=bool(row.get("adaptiveFeeEnabled")),
        created_at=str(created) if created else None,
        pair=pair,
        price=price_f,
        source_ts=source_ts,
    )


def filter_and_rank(
    pools: Sequence[PoolSnapshot],
    *,
    now_ts: float,
    min_tvl: float = MIN_TVL_USD,
    max_fee_pct: float = MAX_FEE_PCT,
    min_age_days: float = MIN_POOL_AGE_DAYS,
) -> list[PoolSnapshot]:
    kept: list[PoolSnapshot] = []
    for p in pools:
        ok, _ = passes_hard_filters(
            p, now_ts=now_ts, min_tvl=min_tvl, max_fee_pct=max_fee_pct, min_age_days=min_age_days
        )
        if ok:
            kept.append(p)
    kept.sort(key=lambda p: p.score, reverse=True)
    return kept


def switch_cost_usd(equity: float) -> float:
    return SWITCH_FIXED_USD + SWITCH_SLIP_FRAC * max(equity, 0.0)


def expected_gain_usd(
    candidate_score: float,
    current_score: float,
    equity: float,
    hours_left: float,
) -> float:
    """Rough expected fee delta over remaining hours if intensity holds."""
    if hours_left <= 0 or equity <= 0:
        return 0.0
    return (candidate_score - current_score) * equity * (hours_left / 24.0)


def switches_in_window(
    state: RankerState,
    now_ts: float,
    lookback_s: float = DEFAULT_LOOKBACK_S,
) -> int:
    return sum(1 for t in state.switch_timestamps if now_ts - t <= lookback_s)


def decide_switch(
    pools: Sequence[PoolSnapshot] | None,
    state: RankerState,
    *,
    now_ts: float,
    equity: float,
    hours_left: float,
    scan_error: Optional[str] = None,
    hysteresis_mult: float = HYSTERESIS_MULT,
    max_switches: int = MAX_SWITCHES_48H,
) -> tuple[SwitchDecision, RankerState]:
    """Pure switch decision. Mutates a copy of state; returns new state."""
    new_state = replace(
        state,
        switch_timestamps=list(state.switch_timestamps),
    )
    new_state.last_scan_ts = now_ts

    if scan_error:
        new_state.last_error = scan_error
        new_state.frozen = True
        new_state.pending_address = None
        new_state.pending_streak = 0
        return (
            SwitchDecision(
                action="freeze",
                target_address=new_state.current_address,
                reason=f"scan_error: {scan_error}",
            ),
            new_state,
        )

    if pools is None:
        new_state.last_error = "pools_none"
        new_state.frozen = True
        return (
            SwitchDecision(
                action="freeze",
                target_address=new_state.current_address,
                reason="pools_none",
            ),
            new_state,
        )

    new_state.last_error = None
    ranked = filter_and_rank(pools, now_ts=now_ts)
    if not ranked:
        new_state.frozen = True
        return (
            SwitchDecision(
                action="freeze",
                target_address=new_state.current_address,
                reason="no_pools_pass_filters",
                ranked=(),
            ),
            new_state,
        )

    top = ranked[0]
    ranked_t = tuple(ranked)

    # First open: take top score.
    if not new_state.current_address:
        new_state.current_address = top.address
        new_state.pending_address = None
        new_state.pending_streak = 0
        new_state.frozen = False
        new_state.switch_timestamps.append(now_ts)
        return (
            SwitchDecision(
                action="open",
                target_address=top.address,
                reason=f"initial_open score={top.score:.6f}",
                ranked=ranked_t,
                candidate_score=top.score,
            ),
            new_state,
        )

    current = next((p for p in ranked if p.address == new_state.current_address), None)
    current_score = current.score if current else 0.0
    cost = switch_cost_usd(equity)

    if top.address == new_state.current_address:
        new_state.pending_address = None
        new_state.pending_streak = 0
        new_state.frozen = False
        return (
            SwitchDecision(
                action="hold",
                target_address=new_state.current_address,
                reason="top_is_current",
                ranked=ranked_t,
                current_score=current_score,
                candidate_score=top.score,
                switch_cost_usd=cost,
            ),
            new_state,
        )

    # Hysteresis: need 1.5x over current on two consecutive scans of the SAME address.
    clears = top.score >= hysteresis_mult * current_score if current_score > 0 else top.score > 0
    if not clears:
        new_state.pending_address = None
        new_state.pending_streak = 0
        return (
            SwitchDecision(
                action="hold",
                target_address=new_state.current_address,
                reason=(
                    f"hysteresis_fail top={top.score:.6f} "
                    f"need>={hysteresis_mult * current_score:.6f}"
                ),
                ranked=ranked_t,
                current_score=current_score,
                candidate_score=top.score,
                switch_cost_usd=cost,
            ),
            new_state,
        )

    if new_state.pending_address == top.address:
        new_state.pending_streak += 1
    else:
        new_state.pending_address = top.address
        new_state.pending_streak = 1

    if new_state.pending_streak < 2:
        return (
            SwitchDecision(
                action="hold",
                target_address=new_state.current_address,
                reason=f"pending_streak={new_state.pending_streak}/2 addr={top.address[:8]}",
                ranked=ranked_t,
                current_score=current_score,
                candidate_score=top.score,
                switch_cost_usd=cost,
            ),
            new_state,
        )

    gain = expected_gain_usd(top.score, current_score, equity, hours_left)
    if gain <= cost:
        return (
            SwitchDecision(
                action="hold",
                target_address=new_state.current_address,
                reason=f"cost_gate gain={gain:.4f} <= cost={cost:.4f}",
                ranked=ranked_t,
                current_score=current_score,
                candidate_score=top.score,
                switch_cost_usd=cost,
                expected_gain_usd=gain,
            ),
            new_state,
        )

    if switches_in_window(new_state, now_ts) >= max_switches:
        return (
            SwitchDecision(
                action="hold",
                target_address=new_state.current_address,
                reason=f"switch_cap>={max_switches}",
                ranked=ranked_t,
                current_score=current_score,
                candidate_score=top.score,
                switch_cost_usd=cost,
                expected_gain_usd=gain,
            ),
            new_state,
        )

    # Commit switch.
    new_state.current_address = top.address
    new_state.pending_address = None
    new_state.pending_streak = 0
    new_state.switch_timestamps.append(now_ts)
    new_state.frozen = False
    return (
        SwitchDecision(
            action="switch",
            target_address=top.address,
            reason=f"switch_to score={top.score:.6f} gain={gain:.4f}",
            ranked=ranked_t,
            current_score=current_score,
            candidate_score=top.score,
            switch_cost_usd=cost,
            expected_gain_usd=gain,
        ),
        new_state,
    )


def score_table(ranked: Sequence[PoolSnapshot], limit: int = 10) -> list[dict[str, Any]]:
    rows = []
    for p in ranked[:limit]:
        rows.append(
            {
                "address": p.address,
                "pair": p.pair,
                "fee_pct": p.fee_pct,
                "tvl": round(p.tvl_usd, 2),
                "vol24": round(p.volume_24h, 2),
                "vol7d": round(p.volume_7d, 2),
                "int24": round(p.intensity_24h, 6),
                "int7d": round(p.intensity_7d, 6),
                "score": round(p.score, 6),
            }
        )
    return rows
