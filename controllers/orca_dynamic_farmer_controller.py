"""Hummingbot V2 controller: dynamic SOL-USDC fee-tier farmer (race entry).

Hourly: fetch Orca API SOL-USDC tiers, score with pool_rank, log the table.
Band: decide() at 16% full width / 0.5 trigger (half-width 8% in Params).
On switch: stop current executor, wait flat, open on new pool with autoswap.
Freeze on API failure. Hard cap 3 switches / 48h. ML ranker shadows only.

Drop into a Hummingbot tree under controllers/generic/orca_dynamic_farmer/.
Until verified, configs/lp_rebalancer_race_800.yml is the emergency fallback.
"""

from __future__ import annotations

import json
import logging
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

_REPO = Path(__file__).resolve().parents[1]
_REPO_SRC = _REPO / "src"
if str(_REPO_SRC) not in sys.path:
    sys.path.insert(0, str(_REPO_SRC))

from orca_tight_range.dynamic_farmer import (  # noqa: E402
    FarmerState,
    race_params,
    tick,
)
from orca_tight_range.logic import Action, Event  # noqa: E402
from orca_tight_range.ml_intensity import shadow_from_log  # noqa: E402
from orca_tight_range.pool_rank import snapshot_from_orca_row  # noqa: E402

ORCA_POOLS = "https://api.orca.so/v2/solana/pools"
SOL_MINT = "So11111111111111111111111111111111111111112"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SNAPSHOT_LOG = _REPO / "data" / "pool_snapshots.jsonl"

try:
    from hummingbot.core.data_type.common import MarketDict, TradeType
    from hummingbot.strategy_v2.controllers import ControllerBase, ControllerConfigBase
    from hummingbot.strategy_v2.executors.lp_executor.data_types import LPExecutorConfig
    from hummingbot.strategy_v2.models.executor_actions import (
        CreateExecutorAction,
        ExecutorAction,
        StopExecutorAction,
    )
    from pydantic import Field

    _HUMMINGBOT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _HUMMINGBOT_AVAILABLE = False
    ControllerBase = object  # type: ignore
    ControllerConfigBase = object  # type: ignore
    TradeType = None  # type: ignore


def fetch_sol_usdc_tiers(size: int = 50) -> list:
    params = {
        "size": str(size),
        "sortBy": "volume24h",
        "sortDirection": "desc",
        "stats": "24h,7d",
        # tokensBothOf = AND (true SOL-USDC). Do NOT use tokens=SOL,USDC (OR).
        "tokensBothOf": f"{SOL_MINT},{USDC_MINT}",
    }
    url = f"{ORCA_POOLS}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "orca-dynamic-farmer/1.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        payload = json.loads(resp.read().decode())
    data = payload.get("data")
    if isinstance(data, dict):
        return list(data.get("pools") or data.get("data") or [])
    if isinstance(data, list):
        return data
    return list(payload.get("pools") or [])


if _HUMMINGBOT_AVAILABLE:

    class OrcaDynamicFarmerConfig(ControllerConfigBase):
        controller_type: str = "generic"
        controller_name: str = "orca_dynamic_farmer"
        candles_config: list = []

        connector_name: str = "solana-mainnet-beta"
        lp_provider: str = "orca/clmm"
        trading_pair: str = "SOL-USDC"
        # Initial pool left empty — ranker picks from API on first open.
        pool_address: str = ""

        total_amount_quote: Decimal = Field(default=Decimal("800"))
        side: TradeType = Field(default=TradeType.RANGE)

        # Full-width semantics documented; Params uses half-width via race_params().
        position_width_pct: Decimal = Field(default=Decimal("16"))
        rebalance_threshold_pct: Decimal = Field(default=Decimal("0.5"))
        autoswap: bool = True
        rank_interval_s: int = 3600
        race_hours: float = 48.0
        ml_shadow: bool = True
        snapshot_log_path: str = str(SNAPSHOT_LOG)

        def update_markets(self, markets: MarketDict) -> MarketDict:
            return markets.add_or_update(self.connector_name, self.trading_pair)

    class OrcaDynamicFarmerController(ControllerBase):
        _logger = None

        @classmethod
        def logger(cls):
            if cls._logger is None:
                cls._logger = logging.getLogger(__name__)
            return cls._logger

        def __init__(self, config: OrcaDynamicFarmerConfig, *args, **kwargs):
            super().__init__(config, *args, **kwargs)
            self.config: OrcaDynamicFarmerConfig = config
            self._farmer = FarmerState(race_end_ts=time.time() + config.race_hours * 3600)
            self._last_rank_ts: float = 0.0
            self._active_executor_id: Optional[str] = None
            self._pending_close: bool = False
            self._params = race_params(config.total_amount_quote)

        def _momentum_sign(self, spot: Decimal) -> int:
            try:
                candles = self.market_data_provider.get_candles_df(
                    connector_name="binance",
                    trading_pair="SOL-USDT",
                    interval="1m",
                    max_records=6,
                )
            except Exception:
                return 0
            if candles is None or getattr(candles, "empty", True):
                return 0
            closes = list(candles["close"].astype(float).tail(5))
            if len(closes) < 2:
                return 0
            delta = closes[-1] - closes[0]
            if abs(delta) / closes[0] < 0.001:
                return 0
            return 1 if delta > 0 else -1

        def _recent_returns(self) -> list:
            try:
                candles = self.market_data_provider.get_candles_df(
                    connector_name="binance",
                    trading_pair="SOL-USDT",
                    interval="1m",
                    max_records=12,
                )
            except Exception:
                return []
            if candles is None or getattr(candles, "empty", True):
                return []
            closes = [Decimal(str(x)) for x in candles["close"].astype(float).tolist()]
            return [(closes[i] / closes[i - 1]) - 1 for i in range(1, len(closes))]

        def _scan_pools(self):
            now = time.time()
            try:
                rows = fetch_sol_usdc_tiers()
                pools = [snapshot_from_orca_row(r, source_ts=now) for r in rows]
                return pools, None
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
                return None, str(e)[:300]

        def _ml_shadow(self) -> Optional[str]:
            if not self.config.ml_shadow:
                return None
            try:
                pick = shadow_from_log(Path(self.config.snapshot_log_path))
                self.logger().info(
                    "ml_shadow rule=%s ml=%s promote=%s %s",
                    (pick.rule_address or "")[:12],
                    (pick.ml_address or "")[:12],
                    pick.promote_ready,
                    pick.note,
                )
                # Acting promotion is gated offline; live always shadows.
                return pick.ml_address
            except Exception as e:
                self.logger().warning("ml_shadow failed: %s", e)
                return None

        def determine_executor_actions(self) -> List[ExecutorAction]:
            if self._farmer.halted:
                return []

            try:
                spot = Decimal(
                    str(
                        self.market_data_provider.get_price_by_type(
                            self.config.connector_name, self.config.trading_pair, "MidPrice"
                        )
                    )
                )
            except Exception:
                self.logger().warning("No mid price yet; holding")
                return []

            try:
                equity = Decimal(
                    str(self.market_data_provider.get_balance(self.config.connector_name, "USDC"))
                )
            except Exception:
                equity = self.config.total_amount_quote

            now = time.time()
            do_rank = (now - self._last_rank_ts) >= self.config.rank_interval_s or not self._farmer.ranker.current_address
            pools = None
            scan_error = None
            ml_addr = None
            if do_rank:
                pools, scan_error = self._scan_pools()
                self._last_rank_ts = now
                ml_addr = self._ml_shadow()
                if pools:
                    self.logger().info(
                        "orca_dynamic_farmer scan n=%s error=%s",
                        len(pools),
                        scan_error,
                    )

            result, self._farmer = tick(
                self._farmer,
                now_ts=now,
                spot=spot,
                equity=equity,
                momentum_sign=self._momentum_sign(spot),
                recent_returns=self._recent_returns(),
                pools=pools,
                scan_error=scan_error,
                params=self._params,
                ml_shadow_address=ml_addr,
                do_rank=do_rank,
            )

            if result.score_table:
                self.logger().info(
                    "score_table %s",
                    json.dumps(result.score_table[:5]),
                )
            self.logger().info(
                "orca_dynamic_farmer %s pool=%s switches_48h=%s ml=%s",
                result.reason,
                (result.pool_address or "")[:12],
                self._farmer.switch_count_48h,
                (result.ml_shadow_address or "")[:12],
            )

            if result.frozen and result.switch.action == "freeze":
                return []

            actions: List[ExecutorAction] = []

            # Switch / initial open path
            if result.switch.action in ("open", "switch"):
                if result.switch.action == "switch" and self._active_executor_id:
                    actions.append(
                        StopExecutorAction(
                            controller_id=self.config.id,
                            executor_id=self._active_executor_id,
                        )
                    )
                    self._pending_close = True
                    self._active_executor_id = None
                    # Defer open until next cycle after close confirms flat.
                    return actions
                self._pending_close = False

            if self._pending_close:
                # Wait for flat; reopen once band says OPEN.
                if result.band.action != Action.OPEN:
                    return actions

            if result.band.action in (Action.OPEN, Action.REBALANCE) and result.band.lower and result.band.upper:
                pool = result.pool_address or self.config.pool_address
                if not pool:
                    self.logger().error("no pool_address from ranker — freeze")
                    return []
                half_quote = self.config.total_amount_quote / Decimal("2")
                cfg = LPExecutorConfig(
                    timestamp=now,
                    connector_name=self.config.connector_name,
                    lp_provider=self.config.lp_provider,
                    pool_address=pool,
                    trading_pair=self.config.trading_pair,
                    lower_price=result.band.lower,
                    upper_price=result.band.upper,
                    base_amount=Decimal("0"),
                    quote_amount=half_quote,
                    side=self.config.side,
                    keep_position=True,
                )
                actions.append(CreateExecutorAction(controller_id=self.config.id, executor_config=cfg))
                self._pending_close = False
                # Executor id is assigned by the engine; track via last create.
                self._active_executor_id = f"pending-{int(now)}"

            return actions

else:

    class OrcaDynamicFarmerConfig:  # type: ignore
        controller_name = "orca_dynamic_farmer"

    class OrcaDynamicFarmerController:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "Hummingbot is not installed in this interpreter. "
                "See docs/INSTALL_PLAN.md — copy this file into a v2.16+ client. "
                "Offline harness: tests/test_dynamic_farmer_harness.py"
            )


if __name__ == "__main__":
    from orca_tight_range.pool_rank import PoolSnapshot, RankerState

    st = FarmerState()
    pools = [
        PoolSnapshot("AAA", 0.04, 2e6, 1e7, 7e7, created_at="2023-01-01T00:00:00Z"),
        PoolSnapshot("BBB", 0.16, 2e6, 3e7, 1.4e8, created_at="2023-01-01T00:00:00Z"),
    ]
    t, st = tick(
        st,
        now_ts=time.time(),
        spot=Decimal("150"),
        equity=Decimal("800"),
        momentum_sign=0,
        recent_returns=(),
        pools=pools,
        do_rank=True,
    )
    print(t.reason, t.pool_address, "hb=", _HUMMINGBOT_AVAILABLE)
