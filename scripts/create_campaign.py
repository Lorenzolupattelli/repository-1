#!/usr/bin/env python3
"""Crea una campagna di test in stato PAUSED (non parte finché non la attivi).

Uso:
    python scripts/create_campaign.py "Nome campagna" [objective]

Esempi:
    python scripts/create_campaign.py "Test traffico"
    python scripts/create_campaign.py "Promo estate" OUTCOME_SALES

Objective validi più comuni:
    OUTCOME_TRAFFIC, OUTCOME_SALES, OUTCOME_LEADS,
    OUTCOME_ENGAGEMENT, OUTCOME_AWARENESS, OUTCOME_APP_PROMOTION
"""

from __future__ import annotations

import sys

from metaads import MetaAdsClient


def main() -> int:
    if len(sys.argv) < 2:
        print('Uso: python scripts/create_campaign.py "Nome campagna" [objective]')
        return 2

    name = sys.argv[1]
    objective = sys.argv[2] if len(sys.argv) > 2 else "OUTCOME_TRAFFIC"

    try:
        client = MetaAdsClient()
        campaign_id = client.create_campaign(
            name=name,
            objective=objective,
            status="PAUSED",  # sicurezza: creata ma in pausa
        )
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Errore nella creazione della campagna: {exc}", file=sys.stderr)
        return 1

    print("✅ Campagna creata (in stato PAUSED — non è ancora attiva).")
    print(f"   ID:        {campaign_id}")
    print(f"   Nome:      {name}")
    print(f"   Objective: {objective}")
    print("\n👉 Attivala da Gestione Inserzioni quando sei pronto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
