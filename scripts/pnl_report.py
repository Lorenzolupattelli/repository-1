#!/usr/bin/env python3
"""Report P&L giornaliero: Ricavi (Shopify) - COGS (regola) - ADV (Meta).

Processa TUTTI gli ordini di un intervallo (paginati), calcola il COGS esatto
per ordine con la regola Firmelià, e aggrega per giorno. Segnala gli ordini da
riconciliare con la fattura (upsell / bundle multipli).

Uso:
    python scripts/pnl_report.py 2026-04-06 2026-08-06 [adspend.csv]

adspend.csv opzionale: righe "YYYY-MM-DD,importo" con la spesa Meta giornaliera.
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict

from firmelia.shopify_client import ShopifyClient
from pnl.firmelia_cogs import CogsRule, compute_order_cogs


def load_adspend(path: str | None) -> dict[str, float]:
    spend: dict[str, float] = {}
    if not path:
        return spend
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) >= 2 and row[0].strip():
                try:
                    spend[row[0].strip()] = float(row[1])
                except ValueError:
                    continue
    return spend


def main() -> int:
    if len(sys.argv) < 3:
        print("Uso: python scripts/pnl_report.py <since> <until> [adspend.csv]")
        return 2
    since, until = sys.argv[1], sys.argv[2]
    adspend = load_adspend(sys.argv[3] if len(sys.argv) > 3 else None)

    rule = CogsRule.load("cogs_firmelia.json")
    client = ShopifyClient()

    # aggregati per giorno
    rev = defaultdict(float)
    cogs = defaultdict(float)
    orders = defaultdict(int)
    to_reconcile: list[str] = []
    n = 0

    for o in client.iter_orders(since, until):
        n += 1
        day = o["created_at"]
        rev[day] += o["net_sales"]
        c = compute_order_cogs(o["name"], o["line_items"], rule)
        cogs[day] += c.total_cogs
        orders[day] += 1
        if c.warnings:
            to_reconcile.append(f"{o['name']}: {'; '.join(c.warnings)}")

    days = sorted(set(rev) | set(cogs) | set(adspend))
    tot_rev = tot_cogs = tot_adv = 0.0
    print(f"{'Data':<12}{'Ord':>5}{'Ricavi':>11}{'COGS':>10}{'ADV':>10}{'Profit':>11}{'Marg%':>7}")
    print("-" * 66)
    for d in days:
        r, cg, ad = rev[d], cogs[d], adspend.get(d, 0.0)
        profit = r - cg - ad
        marg = (profit / r * 100) if r else 0.0
        tot_rev += r; tot_cogs += cg; tot_adv += ad
        print(f"{d:<12}{orders[d]:>5}{r:>11.2f}{cg:>10.2f}{ad:>10.2f}{profit:>11.2f}{marg:>6.1f}%")
    tot_profit = tot_rev - tot_cogs - tot_adv
    print("-" * 66)
    print(f"{'TOTALE':<12}{n:>5}{tot_rev:>11.2f}{tot_cogs:>10.2f}{tot_adv:>10.2f}{tot_profit:>11.2f}"
          f"{(tot_profit/tot_rev*100 if tot_rev else 0):>6.1f}%")

    if to_reconcile:
        print(f"\n⚠️  {len(to_reconcile)} ordini da riconciliare con la fattura:")
        for line in to_reconcile[:50]:
            print("   " + line)
        if len(to_reconcile) > 50:
            print(f"   ... e altri {len(to_reconcile) - 50}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
