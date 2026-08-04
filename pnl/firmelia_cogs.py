"""Calcolo COGS per ordine Firmelià, ricavato dal confronto fatture <-> Shopify.

Il costo dipende dal PIANO di trattamento (valore del bundle), NON dal numero
di pezzi. I valori sono in ``cogs_firmelia.json``.

Struttura verificata sui dati reali:
  - Bundle principale microinfusione per pezzi della riga @~99.99:
      2pz -> 7.63 (2 mesi) | 3pz -> 10.40 (4 mesi) | 5pz -> 14.03 (6 mesi)
  - Upsell "+1 micro a 20 euro" (riga micro scontata <= 50): +6.40 a unita.
  - Add-on (con micro presente): shampoo 3, balsamo 3, siero 2.5, routine 8.5.
  - Ordine senza micro (solo haircare): base spedizione 3.50 + add-on.
    (=> shampoo da solo 6.50, routine da sola 12.00).
  - Digitali/omaggio/test: 0. Tax fissa 1.35 per ordine.

Casi NON deterministici (bundle multipli pieni, billing incoerente del
fornitore): il calcolo li segnala con un warning -> usare il costo di fattura.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

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
    micro_base_by_main_units: dict[int, float]
    micro_upsell_cost: float
    micro_upsell_max_price: float
    addons: dict[str, float | None]
    tax_per_order: float
    non_micro_base: float = 0.0
    zero_cost_items: list[str] = field(default_factory=list)

    @staticmethod
    def load(path: str | Path = "cogs_firmelia.json") -> "CogsRule":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        return CogsRule(
            micro_base_by_main_units={
                int(k): float(v) for k, v in d.get("micro_base_by_main_units", {}).items()
            },
            micro_upsell_cost=float(d.get("micro_upsell_cost", 0.0)),
            micro_upsell_max_price=float(d.get("micro_upsell_max_price", 50.0)),
            addons=d.get("addons", {}),
            tax_per_order=float(d.get("tax_per_order", 0.0)),
            non_micro_base=float(d.get("non_micro_base", 0.0)),
            zero_cost_items=[s.lower() for s in d.get("zero_cost_items", [])],
        )


@dataclass
class OrderCogs:
    order: str
    micro_main_units: int
    micro_base: float
    upsell_units: int
    upsell_cost: float
    addon_costs: dict[str, float]
    non_micro_base: float
    tax: float
    total_cogs: float
    warnings: list[str]


def compute_order_cogs(
    order_name: str, line_items: list[dict], rule: CogsRule
) -> OrderCogs:
    """COGS di un ordine dai line items.

    Ogni line item: dict con ``title``, ``quantity`` e opzionale ``price``
    (prezzo unitario scontato, usato per distinguere l'upsell dal bundle pieno).
    """
    main_units = 0
    upsell_units = 0
    addon_units: dict[str, int] = {k: 0 for k in ADDON_KWS}
    warnings: list[str] = []
    physical_present = False

    for item in line_items:
        title = (item.get("title") or "").lower()
        qty = int(item.get("quantity") or 0)
        price = item.get("price")
        if MICRO_KW in title:
            physical_present = True
            # Upsell = riga micro con prezzo scontato basso (es. 20 euro).
            if price is not None and 0 < float(price) <= rule.micro_upsell_max_price:
                upsell_units += qty
            else:
                main_units += qty
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
        if not any(z in title for z in rule.zero_cost_items):
            warnings.append(f"articolo non mappato: '{item.get('title')}'")

    # Ordine senza prodotti fisici (es. sola gift-card): COGS 0, no tax.
    if not physical_present:
        return OrderCogs(order_name, 0, 0.0, 0, 0.0, {}, 0.0, 0.0, 0.0,
                         warnings + ["nessun prodotto fisico -> COGS 0"])

    # Base microinfusione (bundle principale).
    micro_base = 0.0
    non_micro_base = 0.0
    if main_units:
        val = rule.micro_base_by_main_units.get(main_units)
        if val is None:
            warnings.append(
                f"bundle micro da {main_units} pezzi NON in tabella "
                "(bundle multiplo?) -> usare costo di fattura"
            )
        else:
            micro_base = val
    elif upsell_units == 0:
        # Nessuna microinfusione: base spedizione per ordine solo-haircare.
        non_micro_base = rule.non_micro_base

    upsell_cost = round(upsell_units * rule.micro_upsell_cost, 2)
    if upsell_units:
        warnings.append(
            "ordine con upsell: il fornitore ottimizza il pacco (consolida) -> "
            "stima approssimata, riconciliare con il costo di fattura"
        )

    addon_costs: dict[str, float] = {}
    for key, units in addon_units.items():
        if not units:
            continue
        price = rule.addons.get(key)
        if price is None:
            warnings.append(f"costo add-on '{key}' NON definito ({units} pz)")
            continue
        addon_costs[key] = round(price * units, 2)

    tax = rule.tax_per_order
    total = round(
        micro_base + upsell_cost + non_micro_base + sum(addon_costs.values()) + tax, 2
    )

    return OrderCogs(
        order=order_name,
        micro_main_units=main_units,
        micro_base=micro_base,
        upsell_units=upsell_units,
        upsell_cost=upsell_cost,
        addon_costs=addon_costs,
        non_micro_base=non_micro_base,
        tax=tax,
        total_cogs=total,
        warnings=warnings,
    )
