"""Calcolo del Profit & Loss (P&L) giornaliero del brand.

Combina:
  - Ricavi   -> net sales da Shopify
  - Spesa ADV -> Meta Marketing API (vedi package metaads)
  - COGS      -> costi prodotto da cogs.json (non presenti su Shopify)
"""

from .calculator import DayPnL, PnLInputs, compute_day_pnl
from .cogs import CogsConfig, load_cogs

__all__ = ["DayPnL", "PnLInputs", "compute_day_pnl", "CogsConfig", "load_cogs"]
