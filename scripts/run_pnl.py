#!/usr/bin/env python3
"""P&L giornaliero completo, tutto in locale sul tuo PC.

Un solo comando: legge gli ordini Shopify, calcola il COGS con la regola
Firmelià, legge la spesa ADV da Meta, e stampa il P&L giorno per giorno
(Ricavi - COGS - ADV = Profit). Salva anche un CSV.

Uso:
    python scripts/run_pnl.py 2026-04-06 2026-08-06 [output.csv]

Richiede nel .env: SHOPIFY_* e META_* (vedi .env.example).
Se le credenziali Meta mancano, la spesa ADV viene messa a 0 (P&L lordo).
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict

from firmelia.shopify_client import ShopifyClient
from pnl.firmelia_cogs import CogsRule, compute_order_cogs


def main() -> int:
    if len(sys.argv) < 3:
        print("Uso: python scripts/run_pnl.py <since> <until> [output.csv]")
        return 2
    since, until = sys.argv[1], sys.argv[2]
    out_csv = sys.argv[3] if len(sys.argv) > 3 else "pnl.csv"

    rule = CogsRule.load("cogs_firmelia.json")

    # 1) Ricavi + COGS da Shopify
    print(f"Leggo gli ordini Shopify {since} .. {until} ...")
    rev = defaultdict(float)
    cogs = defaultdict(float)
    orders = defaultdict(int)
    reconcile: list[str] = []
    n = 0
    for o in ShopifyClient().iter_orders(since, until):
        n += 1
        day = o["created_at"]
        rev[day] += o["net_sales"]
        c = compute_order_cogs(o["name"], o["line_items"], rule)
        cogs[day] += c.total_cogs
        orders[day] += 1
        if c.warnings:
            reconcile.append(f"{o['name']}: {'; '.join(c.warnings)}")
    print(f"  {n} ordini letti.")

    # 2) Spesa ADV da Meta (se configurata)
    adspend: dict[str, float] = {}
    try:
        from metaads import MetaAdsClient
        print("Leggo la spesa ADV da Meta ...")
        adspend = MetaAdsClient().get_daily_spend(since, until)
        print(f"  spesa Meta totale: EUR {sum(adspend.values()):.2f}")
    except Exception as exc:  # noqa: BLE001
        print(f"  (Meta non disponibile: {exc}) -> ADV = 0")

    # 3) Aggrega e stampa
    days = sorted(set(rev) | set(adspend))
    rows = []
    tr = tc = ta = 0.0
    print(f"\n{'Data':<12}{'Ord':>5}{'Ricavi':>11}{'COGS':>10}{'ADV':>10}{'Profit':>11}{'Marg%':>7}")
    print("-" * 66)
    for d in days:
        r, cg, ad = rev[d], cogs[d], adspend.get(d, 0.0)
        p = r - cg - ad
        m = (p / r * 100) if r else 0.0
        tr += r; tc += cg; ta += ad
        print(f"{d:<12}{orders[d]:>5}{r:>11.2f}{cg:>10.2f}{ad:>10.2f}{p:>11.2f}{m:>6.1f}%")
        rows.append({"data": d, "ordini": orders[d], "ricavi": round(r, 2),
                     "cogs": round(cg, 2), "adv": round(ad, 2), "profit": round(p, 2),
                     "margine_pct": round(m, 1)})
    tp = tr - tc - ta
    print("-" * 66)
    print(f"{'TOTALE':<12}{n:>5}{tr:>11.2f}{tc:>10.2f}{ta:>10.2f}{tp:>11.2f}"
          f"{(tp/tr*100 if tr else 0):>6.1f}%")

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["data", "ordini", "ricavi", "cogs", "adv", "profit", "margine_pct"])
        w.writeheader(); w.writerows(rows)
    print(f"\nCSV salvato: {out_csv}")

    if reconcile:
        print(f"\n⚠️  {len(reconcile)} ordini da riconciliare con la fattura (upsell/bundle):")
        for line in reconcile[:30]:
            print("   " + line)
        if len(reconcile) > 30:
            print(f"   ... e altri {len(reconcile) - 30}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
