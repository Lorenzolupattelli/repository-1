"""Caricamento della configurazione COGS (costi prodotto e costi extra)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CogsConfig:
    """Costi usati per il calcolo del P&L."""

    # Mappa nome_prodotto -> costo unitario (COGS per pezzo).
    unit_costs: dict[str, float] = field(default_factory=dict)
    # Alternativa al COGS per-prodotto: percentuale media sui ricavi (0.30 = 30%).
    blended_cogs_rate: float | None = None
    # Costi extra.
    shipping_cost_per_order: float = 0.0
    transaction_fee_rate: float = 0.0  # es. 0.025 = 2,5% sui ricavi
    fixed_daily_cost: float = 0.0

    def cost_for_units(self, units_by_product: dict[str, int]) -> float:
        """COGS totale dato il numero di pezzi venduti per prodotto."""
        total = 0.0
        for name, qty in units_by_product.items():
            total += self.unit_costs.get(name, 0.0) * qty
        return total


def load_cogs(path: str | Path = "cogs.json") -> CogsConfig:
    """Legge cogs.json. Solleva un errore chiaro se il file manca."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"File COGS non trovato: {p}. "
            "Copia cogs.example.json in cogs.json e inserisci i costi reali."
        )
    data = json.loads(p.read_text(encoding="utf-8"))

    unit_costs = {
        prod["name"]: float(prod.get("unit_cost", 0.0))
        for prod in data.get("products", [])
    }
    return CogsConfig(
        unit_costs=unit_costs,
        blended_cogs_rate=data.get("blended_cogs_rate"),
        shipping_cost_per_order=float(data.get("shipping_cost_per_order", 0.0)),
        transaction_fee_rate=float(data.get("transaction_fee_rate", 0.0)),
        fixed_daily_cost=float(data.get("fixed_daily_cost", 0.0)),
    )
