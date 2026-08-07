"""Caricamento e validazione delle credenziali dall'ambiente (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_API_VERSION = "v21.0"


@dataclass(frozen=True)
class MetaConfig:
    """Credenziali e parametri per la Meta Marketing API."""

    access_token: str
    ad_account_id: str  # sempre normalizzato con il prefisso "act_"
    app_id: str | None = None
    app_secret: str | None = None
    api_version: str = DEFAULT_API_VERSION


def _normalize_account_id(raw: str) -> str:
    """Restituisce l'ad account id nella forma canonica ``act_<numero>``."""
    account_id = raw.strip()
    if not account_id:
        return account_id
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"
    return account_id


def load_config(dotenv_path: str | None = None) -> MetaConfig:
    """Legge le credenziali dal file .env / dalle variabili d'ambiente.

    Solleva ``RuntimeError`` con un messaggio chiaro se manca qualcosa di
    obbligatorio, così l'errore è comprensibile anche senza leggere il codice.
    """
    load_dotenv(dotenv_path=dotenv_path)

    access_token = os.getenv("META_ACCESS_TOKEN", "").strip()
    ad_account_id = _normalize_account_id(os.getenv("META_AD_ACCOUNT_ID", ""))

    missing = []
    if not access_token:
        missing.append("META_ACCESS_TOKEN")
    if not ad_account_id:
        missing.append("META_AD_ACCOUNT_ID")
    if missing:
        raise RuntimeError(
            "Credenziali mancanti: "
            + ", ".join(missing)
            + ".\nCopia .env.example in .env e inserisci i valori "
            "(vedi il README per i dettagli)."
        )

    return MetaConfig(
        access_token=access_token,
        ad_account_id=ad_account_id,
        app_id=os.getenv("META_APP_ID", "").strip() or None,
        app_secret=os.getenv("META_APP_SECRET", "").strip() or None,
        api_version=os.getenv("META_API_VERSION", "").strip() or DEFAULT_API_VERSION,
    )
