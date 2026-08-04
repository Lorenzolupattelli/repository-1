"""Calcolo COGS PRECISO per ordine Firmelià (nessuna media).

I costi sono caricati da ``cogs_firmelia.json`` (facile da aggiornare).

Regola (fornita dal titolare, verificata al centesimo su fatture reali):
  - Base "Sistema di Microinfusione" per numero di pezzi nell'ordine
    (= durata trattamento): 2pz->7.63, 3pz->10.40, 5pz->14.03, 6pz->16.80.
  - Aggiunte lineari: shampoo +3.00, balsamo +3.00, siero +2.50.
  - Tax fissa per ordine: +1.35.
  - Articoli digitali/omaggio (eBook, WhatsApp, Gift-Card): 0.00.
  - Ordine di sola gift-card (nessun prodotto fisico): COGS 0, nessuna tax.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# Parole chiave per riconoscere i prodotti dai titoli delle righe ordine.
MICRO_KW = "microinfusione"
ADDON_KWS = {
    "shampoo": "shampoo",
    "balsamo": "balsamo",
    "siero": "siero",
    "routine": "routine",
    "spazzola": "spazzola",
    "infusore": "infusore",
}


@dataclass(frozen=True)
class CogsRule:
    micro_cost_by_units: dict[int, float | None]
    addons: dict[str, float | None]
    tax_per_order: float
    non_micro_base: float = 0.0
    zero_cost_items: list[str] = field(default_factory=list)

    @staticmethod
    def load(path: str | Path = "cogs_firmelia.json") -> "CogsRule":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return CogsRule(
            micro_cost_by_units={
                int(k): v for k, v in data.get("micro_cost_by_units", {}).items()
            },
            addons=data.get("addons", {}),
            tax_per_order=float(data.get("tax_per_order", 0.0)),
            non_micro_base=float(data.get("non_micro_base", 0.0)),
            zero_cost_items=[s.lower() for s in data.get("zero_cost_items", [])],
        )


@dataclass
class OrderCogs:
    order: str
    micro_units: int
    micro_cost: float
    addon_costs: dict[str, float]
    tax: float
    total_cogs: float
    warnings: list[str]


def compute_order_cogs(
    order_name: str, line_items: list[dict], rule: CogsRule
) -> OrderCogs:
    """Calcola il COGS esatto di un ordine dai suoi line items.

    ``line_items``: lista di dict con almeno ``title`` e ``quantity``.
    """
    micro_units = 0
    addon_units: dict[str, int] = {k: 0 for k in ADDON_KWS}
    warnings: list[str] = []
    physical_present = False

    for item in line_items:
        title = (item.get("title") or "").lower()
        qty = int(item.get("quantity") or 0)
        if MICRO_KW in title:
            micro_units += qty
            physical_present = True
            continue
        matched = False
        for key, kw in ADDON_KWS.items():
            if kw in title:
                addon_units[key] += qty
                physical_present = True
                matched = True
                break
        if matched:
            continue
        # Se non e' un articolo a costo zero noto, segnalalo.
        if not any(z in title for z in rule.zero_cost_items):
            warnings.append(f"articolo non mappato: '{item.get('title')}'")

    # Ordine senza prodotti fisici (es. sola gift-card): COGS 0, no tax.
    if not physical_present:
        return OrderCogs(order_name, 0, 0.0, {}, 0.0, 0.0,
                         warnings + ["nessun prodotto fisico -> COGS 0"])

    # Base microinfusione (o base spedizione se ordine solo-haircare).
    micro_cost = 0.0
    if micro_units:
        val = rule.micro_cost_by_units.get(micro_units)
        if val is None:
            warnings.append(
                f"costo per {micro_units} pezzi microinfusione NON definito"
            )
        else:
            micro_cost = val
    else:
        # Nessuna microinfusione ma prodotti fisici (haircare): base spedizione.
        micro_cost = rule.non_micro_base

    # Aggiunte.
    addon_costs: dict[str, float] = {}
    for key, units in addon_units.items():
        if not units:
            continue
        price = rule.addons.get(key)
        if price is None:
            warnings.append(f"costo aggiunta '{key}' NON definito ({units} pz)")
            continue
        addon_costs[key] = round(price * units, 2)

    tax = rule.tax_per_order
    total = round(micro_cost + sum(addon_costs.values()) + tax, 2)

    return OrderCogs(
        order=order_name,
        micro_units=micro_units,
        micro_cost=micro_cost,
        addon_costs=addon_costs,
        tax=tax,
        total_cogs=total,
        warnings=warnings,
    )
