#!/usr/bin/env python3
"""Verifica che il collegamento all'ad account Meta funzioni.

Uso:
    python scripts/check_connection.py

Stampa i dati base dell'account se il token e l'ID sono corretti.
"""

from __future__ import annotations

import sys

from metaads import MetaAdsClient


def main() -> int:
    try:
        client = MetaAdsClient()
        info = client.get_account_info()
    except Exception as exc:  # noqa: BLE001 - messaggio amichevole per l'utente
        print(f"❌ Collegamento fallito: {exc}", file=sys.stderr)
        return 1

    print("✅ Collegamento riuscito! Account trovato:\n")
    print(f"  Nome:      {info.get('name')}")
    print(f"  ID:        {info.get('id')}")
    print(f"  Stato:     {info.get('account_status')}  (1 = attivo)")
    print(f"  Valuta:    {info.get('currency')}")
    print(f"  Fuso:      {info.get('timezone_name')}")
    print(f"  Speso tot: {info.get('amount_spent')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
