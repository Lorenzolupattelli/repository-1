#!/usr/bin/env python3
"""Esporta la spesa ADV Meta giornaliera in CSV (data,spesa) per il P&L.

Uso:
    python scripts/export_meta_spend.py 2026-04-06 2026-08-06 > adspend.csv

Poi:
    python scripts/pnl_report.py 2026-04-06 2026-08-06 adspend.csv
"""

from __future__ import annotations

import sys

from metaads import MetaAdsClient


def main() -> int:
    if len(sys.argv) < 3:
        print("Uso: python scripts/export_meta_spend.py <since> <until>", file=sys.stderr)
        return 2
    since, until = sys.argv[1], sys.argv[2]
    try:
        client = MetaAdsClient()
        spend = client.get_daily_spend(since, until)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Errore lettura spesa Meta: {exc}", file=sys.stderr)
        return 1

    total = 0.0
    for day in sorted(spend):
        print(f"{day},{spend[day]:.2f}")
        total += spend[day]
    print(f"# Spesa Meta totale {since}..{until}: EUR {total:.2f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
