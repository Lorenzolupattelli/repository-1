#!/usr/bin/env python3
"""Legge e stampa gli insight dell'ad account (spese, click, impression...).

Uso:
    python scripts/read_insights.py [date_preset] [level]

Esempi:
    python scripts/read_insights.py                 # last_30d, per campagna
    python scripts/read_insights.py last_7d         # ultimi 7 giorni
    python scripts/read_insights.py this_month adset # questo mese, per adset
"""

from __future__ import annotations

import sys

from metaads import MetaAdsClient


def main() -> int:
    date_preset = sys.argv[1] if len(sys.argv) > 1 else "last_30d"
    level = sys.argv[2] if len(sys.argv) > 2 else "campaign"

    try:
        client = MetaAdsClient()
        rows = client.get_insights(level=level, date_preset=date_preset)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Errore nella lettura degli insight: {exc}", file=sys.stderr)
        return 1

    if not rows:
        print(f"Nessun dato per '{date_preset}' (level={level}).")
        return 0

    print(f"📊 Insight — periodo: {date_preset}, livello: {level}\n")
    for row in rows:
        name = row.get("campaign_name", "(account)")
        print(f"• {name}")
        print(f"    impression: {row.get('impressions', 0)}")
        print(f"    click:      {row.get('clicks', 0)}")
        print(f"    spesa:      {row.get('spend', 0)}")
        print(f"    CTR:        {row.get('ctr', 0)}")
        print(f"    CPC:        {row.get('cpc', 0)}")
        print(f"    reach:      {row.get('reach', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
