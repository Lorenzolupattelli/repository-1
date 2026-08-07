"""Motore di calcolo del P&L giornaliero.

Formula:
    net_profit = net_sales
               - COGS
               - ad_spend
               - shipping
               - transaction_fees
               - fixed_daily_cost
"""

from __future__ import annotations

from dataclasses import dataclass

from .cogs import CogsConfig


@dataclass(frozen=True)
class PnLInputs:
    """Dati di un singolo giorno."""

    date: str
    net_sales: float          # ricavi (Shopify, dopo sconti)
    ad_spend: float           # spesa pubblicitaria (Meta)
    orders: int = 0
    units_by_product: dict[str, int] | None = None  # pezzi venduti per prodotto


@dataclass(frozen=True)
class DayPnL:
    """Risultato del P&L di un giorno."""

    date: str
    net_sales: float
    cogs: float
    ad_spend: float
    shipping: float
    transaction_fees: float
    fixed_cost: float
    net_profit: float
    margin_pct: float  # net_profit / net_sales * 100


def compute_day_pnl(inputs: PnLInputs, cogs_cfg: CogsConfig) -> DayPnL:
    """Calcola il P&L di un giorno a partire dai ricavi, spesa ADV e COGS."""
    # 1. COGS: per-prodotto se disponibile, altrimenti percentuale media.
    if inputs.units_by_product and any(cogs_cfg.unit_costs.values()):
        cogs = cogs_cfg.cost_for_units(inputs.units_by_product)
    elif cogs_cfg.blended_cogs_rate is not None:
        cogs = inputs.net_sales * cogs_cfg.blended_cogs_rate
    else:
        cogs = 0.0

    # 2. Costi extra.
    shipping = cogs_cfg.shipping_cost_per_order * inputs.orders
    transaction_fees = inputs.net_sales * cogs_cfg.transaction_fee_rate
    fixed_cost = cogs_cfg.fixed_daily_cost

    # 3. Profitto netto.
    net_profit = (
        inputs.net_sales
        - cogs
        - inputs.ad_spend
        - shipping
        - transaction_fees
        - fixed_cost
    )
    margin = (net_profit / inputs.net_sales * 100.0) if inputs.net_sales else 0.0

    return DayPnL(
        date=inputs.date,
        net_sales=round(inputs.net_sales, 2),
        cogs=round(cogs, 2),
        ad_spend=round(inputs.ad_spend, 2),
        shipping=round(shipping, 2),
        transaction_fees=round(transaction_fees, 2),
        fixed_cost=round(fixed_cost, 2),
        net_profit=round(net_profit, 2),
        margin_pct=round(margin, 1),
    )
