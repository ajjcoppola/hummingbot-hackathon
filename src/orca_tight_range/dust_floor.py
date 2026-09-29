"""Skip Jupiter autoswaps that are too small to route.

Official lp_rebalancer swaps any positive deficit. A quote gap of ~$0.000074
becomes SELL 0.000000 SOL and Jupiter NO_ROUTE_FOUND, which retries forever
and never opens the LP. Copied onto the bind-mounted controller by
scripts/t016_cutover.py before a live restart.
"""

from __future__ import annotations

from decimal import Decimal

# Below this, Jupiter ExactIn on SOL-USDC quantizes to zero and returns NO_ROUTE_FOUND.
MIN_SWAP_QUOTE_USDC = Decimal("0.05")


def positive_deficit_quote(
    base_deficit: Decimal,
    quote_deficit: Decimal,
    price: Decimal,
) -> Decimal:
    """USDC value of every positive deficit. Surpluses (negative deficits) add nothing."""
    total = Decimal("0")
    if base_deficit > 0 and price > 0:
        total += base_deficit * price
    if quote_deficit > 0:
        total += quote_deficit
    return total


def skip_dust_swap(
    base_deficit: Decimal,
    quote_deficit: Decimal,
    price: Decimal,
    min_quote: Decimal = MIN_SWAP_QUOTE_USDC,
) -> bool:
    """True when a swap would be dust and the caller should open with balances on hand.

    A real inventory gap (sum of positive deficits >= min_quote) still swaps.
    Both-sides dust under the floor is skipped too. No deficit returns False so
    the controller's existing 'balances sufficient' path stays unchanged.
    """
    if price <= 0:
        return False
    total = positive_deficit_quote(base_deficit, quote_deficit, price)
    if total <= 0:
        return False
    return total < min_quote
