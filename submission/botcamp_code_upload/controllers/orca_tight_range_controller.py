"""Hummingbot V2 controller: tight-range Orca Whirlpool LP.

Drop this file into a current Hummingbot tree at:

    controllers/generic/orca_tight_range/orca_tight_range_controller.py

and copy ``configs/orca_tight_range.yml`` into the client's conf folder.

Until that drop-in is verified on Gateway, the official ``lp_rebalancer``
controller with ``lp_provider: orca/clmm`` plus this YAML is the runnable
fallback. This class adds directional skew, an exhaustion filter, a gas
rate-limit, and a hard drawdown stop on top of the LP executor lifecycle.
"""

from __future__ import annotations

import logging
import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

# Allow ``python controllers/orca_tight_range_controller.py`` smoke imports
# from this repo without Hummingbot installed.
_REPO_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_REPO_SRC) not in sys.path:
    sys.path.insert(0, str(_REPO_SRC))

from orca_tight_range.logic import (  # noqa: E402
    Action,
    Event,
    Params,
    Position,
    Snapshot,
    decide,
)

try:
    from hummingbot.core.data_type.common import MarketDict, TradeType
    from hummingbot.strategy_v2.controllers import ControllerBase, ControllerConfigBase
    from hummingbot.strategy_v2.executors.lp_executor.data_types import LPExecutorConfig
    from hummingbot.strategy_v2.models.executor_actions import CreateExecutorAction, ExecutorAction
    from pydantic import Field

    _HUMMINGBOT_AVAILABLE = True
except ImportError:  # pragma: no cover - expected outside a Hummingbot venv
    _HUMMINGBOT_AVAILABLE = False
    ControllerBase = object  # type: ignore
    ControllerConfigBase = object  # type: ignore
    TradeType = None  # type: ignore


if _HUMMINGBOT_AVAILABLE:

    class OrcaTightRangeConfig(ControllerConfigBase):
        controller_type: str = "generic"
        controller_name: str = "orca_tight_range"
        candles_config: list = []

        connector_name: str = "solana-mainnet-beta"
        lp_provider: str = "orca/clmm"
        trading_pair: str = "SOL-USDC"
        pool_address: str = ""

        total_amount_quote: Decimal = Field(default=Decimal("800"))
        side: TradeType = Field(default=TradeType.RANGE)

        range_width_pct: Decimal = Field(default=Decimal("1.5"))
        skew_bias: Decimal = Field(default=Decimal("0.6"))
        rebalance_trigger_pct: Decimal = Field(default=Decimal("0.8"))
        volatility_exhaustion_window_s: int = 300
        max_rebalances_per_hour: int = 6
        stop_loss_drawdown_pct: Decimal = Field(default=Decimal("15"))

        def to_params(self) -> Params:
            return Params(
                range_width_pct=self.range_width_pct,
                skew_bias=self.skew_bias,
                rebalance_trigger_pct=self.rebalance_trigger_pct,
                volatility_exhaustion_window_s=self.volatility_exhaustion_window_s,
                max_rebalances_per_hour=self.max_rebalances_per_hour,
                capital_allocation_usdc=self.total_amount_quote,
                stop_loss_drawdown_pct=self.stop_loss_drawdown_pct,
            )

        def update_markets(self, markets: MarketDict) -> MarketDict:
            return markets.add_or_update(self.connector_name, self.trading_pair)

    class OrcaTightRangeController(ControllerBase):
        """Policy layer. Execution stays in LPExecutor (deterministic)."""

        _logger = None

        @classmethod
        def logger(cls):
            if cls._logger is None:
                cls._logger = logging.getLogger(__name__)
            return cls._logger

        def __init__(self, config: OrcaTightRangeConfig, *args, **kwargs):
            super().__init__(config, *args, **kwargs)
            self.config: OrcaTightRangeConfig = config
            self._rebalance_timestamps: List[float] = []
            self._opened_equity: Optional[Decimal] = None
            self._position: Optional[Position] = None
            self._halted = False

        def _momentum_sign(self, spot: Decimal) -> int:
            candles = []
            try:
                candles = self.market_data_provider.get_candles_df(
                    connector_name="binance",
                    trading_pair="SOL-USDT",
                    interval="1m",
                    max_records=6,
                )
            except Exception:
                candles = None
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

        def determine_executor_actions(self) -> List[ExecutorAction]:
            if self._halted:
                return []

            try:
                spot = Decimal(str(self.market_data_provider.get_price_by_type(
                    self.config.connector_name, self.config.trading_pair, "MidPrice"
                )))
            except Exception:
                self.logger().warning("No mid price yet; holding")
                return []

            try:
                equity = Decimal(str(self.market_data_provider.get_balance(
                    self.config.connector_name, "USDC"
                )))
            except Exception:
                equity = self.config.total_amount_quote

            now = time.time()
            snap = Snapshot(
                ts=now,
                spot=spot,
                equity_usdc=equity,
                momentum_sign=self._momentum_sign(spot),
                recent_returns=self._recent_returns(),
                rebalance_timestamps=self._rebalance_timestamps,
            )
            decision = decide(self.config.to_params(), snap, self._position)
            self.logger().info("orca_tight_range %s: %s", decision.event.value, decision.reason)

            if decision.action == Action.STOP:
                self._halted = True
                return []

            if decision.action in (Action.OPEN, Action.REBALANCE) and decision.lower and decision.upper:
                if not self.config.pool_address:
                    self.logger().error("pool_address is empty — resolve SOL/USDC Whirlpool before live")
                    return []
                self._position = Position(
                    lower=decision.lower,
                    upper=decision.upper,
                    center=decision.center or ((decision.lower + decision.upper) / 2),
                    opened_at=now,
                    opened_equity=self._opened_equity or equity,
                )
                if self._opened_equity is None:
                    self._opened_equity = equity
                if decision.event == Event.REBALANCE_EXECUTED:
                    self._rebalance_timestamps.append(now)
                half_quote = self.config.total_amount_quote / Decimal("2")
                cfg = LPExecutorConfig(
                    timestamp=now,
                    connector_name=self.config.connector_name,
                    lp_provider=self.config.lp_provider,
                    pool_address=self.config.pool_address,
                    trading_pair=self.config.trading_pair,
                    lower_price=decision.lower,
                    upper_price=decision.upper,
                    base_amount=Decimal("0"),
                    quote_amount=half_quote,
                    side=self.config.side,
                    keep_position=True,
                )
                return [CreateExecutorAction(controller_id=self.config.id, executor_config=cfg)]

            return []

else:

    class OrcaTightRangeConfig:  # type: ignore
        """Stub so this file can be uploaded before Hummingbot is installed."""

        controller_name = "orca_tight_range"


    class OrcaTightRangeController:  # type: ignore
        """Stub. Install Hummingbot v2.16+ to use the live controller."""

        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "Hummingbot is not installed in this interpreter. "
                "See docs/INSTALL_PLAN.md — copy this file into a v2.16 client."
            )


if __name__ == "__main__":
    p = Params()
    snap = Snapshot(ts=0, spot=Decimal("150"), equity_usdc=Decimal("800"), momentum_sign=1)
    print(decide(p, snap, None))
    print("hummingbot_available=", _HUMMINGBOT_AVAILABLE)
