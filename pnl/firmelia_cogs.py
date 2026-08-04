"""Calcolo COGS PRECISO per ordine Firmelià (nessuna media).

Regola (fornita dal titolare, verificata sugli ordini reali):

  Base "Sistema di Microinfusione" per numero di pezzi nell'ordine
  (= durata del trattamento):
      2 pezzi (2 mesi) -> 7.63
      3 pezzi (4 mesi) -> 10.40
      5 pezzi (6 mesi) -> 14.03
      6 pezzi          -> 16.80
  Aggiunte:
      Shampoo -> +3.00   Balsamo -> +3.00   Siero -> +2.50
  Tax fissa per ordine -> +1.35
  Articoli digitali (eBook, Supporto WhatsApp, Gift-Card) -> 0.00
"""

from __future__ import annotations

from dataclasses import dataclass

# Costo base della microinfusione per numero di pezzi nell'ordine.
# Estendibile man mano che compaiono nuove combinazioni (es. 4 pezzi).
MICRO_COST_BY_UNITS: dict[int, float] = {
    2: 7.63,
    3: 10.40,
    5: 14.03,
    6: 16.80,
}

SHAMPOO_COST = 3.00
BALSAMO_COST = 3.00
SIERO_COST = 2.50
TAX_PER_ORDER = 1.35

# Parole chiave per riconoscere i prodotti dai titoli delle righe ordine.
MICRO_KW = "microinfusione"
SHAMPOO_KW = "shampoo"
BALSAMO_KW = "balsamo"
SIERO_KW = "siero"


@dataclass
class OrderCogs:
    """Dettaglio COGS di un singolo ordine."""

    order: str
    micro_units: int
    micro_cost: float
    shampoo_cost: float
    balsamo_cost: float
    siero_cost: float
    tax: float
    total_cogs: float
    unknown_micro_tier: bool  # True se i pezzi microinfusione non sono in tabella


def compute_order_cogs(order_name: str, line_items: list[dict]) -> OrderCogs:
    """Calcola il COGS esatto di un ordine dai suoi line items.

    :param line_items: lista di dict con almeno ``title`` e ``quantity``.
    """
    micro_units = 0
    shampoo_units = 0
    balsamo_units = 0
    siero_units = 0

    for item in line_items:
        title = (item.get("title") or "").lower()
        qty = int(item.get("quantity") or 0)
        if MICRO_KW in title:
            micro_units += qty
        elif SHAMPOO_KW in title:
            shampoo_units += qty
        elif BALSAMO_KW in title:
            balsamo_units += qty
        elif SIERO_KW in title:
            siero_units += qty
        # tutto il resto (eBook, WhatsApp, Gift-Card, ...) = costo 0

    unknown = micro_units not in MICRO_COST_BY_UNITS and micro_units > 0
    micro_cost = MICRO_COST_BY_UNITS.get(micro_units, 0.0)

    shampoo_cost = shampoo_units * SHAMPOO_COST
    balsamo_cost = balsamo_units * BALSAMO_COST
    siero_cost = siero_units * SIERO_COST
    tax = TAX_PER_ORDER

    total = round(micro_cost + shampoo_cost + balsamo_cost + siero_cost + tax, 2)

    return OrderCogs(
        order=order_name,
        micro_units=micro_units,
        micro_cost=micro_cost,
        shampoo_cost=round(shampoo_cost, 2),
        balsamo_cost=round(balsamo_cost, 2),
        siero_cost=round(siero_cost, 2),
        tax=tax,
        total_cogs=total,
        unknown_micro_tier=unknown,
    )
