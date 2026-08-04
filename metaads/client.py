"""Client di alto livello sopra l'SDK ufficiale ``facebook-business``.

Espone metodi semplici per:
  - verificare il collegamento all'ad account;
  - leggere gli insight (spese, impression, click, ecc.);
  - creare campagne/adset in modo sicuro (default in stato PAUSED).
"""

from __future__ import annotations

from typing import Any

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.api import FacebookAdsApi

from .config import MetaConfig, load_config

# Campi insight richiesti di default. Modificabili passando ``fields`` esplicito.
DEFAULT_INSIGHT_FIELDS = [
    "campaign_name",
    "impressions",
    "clicks",
    "spend",
    "ctr",
    "cpc",
    "reach",
]


class MetaAdsClient:
    """Wrapper attorno a un singolo ad account Meta."""

    def __init__(self, config: MetaConfig | None = None) -> None:
        self.config = config or load_config()
        FacebookAdsApi.init(
            app_id=self.config.app_id,
            app_secret=self.config.app_secret,
            access_token=self.config.access_token,
            api_version=self.config.api_version,
        )
        self.account = AdAccount(self.config.ad_account_id)

    # ---------------------------------------------------------------- lettura
    def get_account_info(self) -> dict[str, Any]:
        """Restituisce i dati base dell'account: serve a validare il token."""
        fields = ["name", "account_status", "currency", "timezone_name", "amount_spent"]
        account = self.account.api_get(fields=fields)
        return dict(account)

    def get_insights(
        self,
        level: str = "campaign",
        date_preset: str = "last_30d",
        fields: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Scarica gli insight dell'account.

        :param level: ``account`` | ``campaign`` | ``adset`` | ``ad``
        :param date_preset: es. ``today``, ``last_7d``, ``last_30d``, ``this_month``
        :param fields: elenco di metriche; se ``None`` usa DEFAULT_INSIGHT_FIELDS
        """
        params = {"level": level, "date_preset": date_preset}
        insights = self.account.get_insights(
            fields=fields or DEFAULT_INSIGHT_FIELDS,
            params=params,
        )
        return [dict(row) for row in insights]

    def list_campaigns(self, limit: int = 50) -> list[dict[str, Any]]:
        """Elenca le campagne dell'account."""
        fields = ["name", "objective", "status", "daily_budget", "created_time"]
        campaigns = self.account.get_campaigns(fields=fields, params={"limit": limit})
        return [dict(c) for c in campaigns]

    # -------------------------------------------------------------- scrittura
    def create_campaign(
        self,
        name: str,
        objective: str = "OUTCOME_TRAFFIC",
        status: str = "PAUSED",
        special_ad_categories: list[str] | None = None,
        daily_budget_cents: int | None = None,
    ) -> str:
        """Crea una campagna e restituisce il suo ID.

        Per sicurezza il default è ``status="PAUSED"``: la campagna viene creata
        ma NON parte finché non la attivi esplicitamente. ``daily_budget_cents``
        è nella valuta minore dell'account (es. centesimi di euro: 1000 = 10 €).
        """
        params: dict[str, Any] = {
            "name": name,
            "objective": objective,
            "status": status,
            "special_ad_categories": special_ad_categories or [],
        }
        if daily_budget_cents is not None:
            params["daily_budget"] = daily_budget_cents

        campaign = self.account.create_campaign(params=params)
        return campaign[Campaign.Field.id]
