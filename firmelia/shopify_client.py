"""Client minimale per l'Admin API di Shopify (GraphQL, con paginazione).

Legge gli ordini in un intervallo di date. Richiede nel .env:
    SHOPIFY_STORE_DOMAIN   es. ep1ukb-rg.myshopify.com  (o www.firmelia.it)
    SHOPIFY_ADMIN_TOKEN    Admin API access token (shpat_...)
    SHOPIFY_API_VERSION    opzionale, default 2025-01
"""

from __future__ import annotations

import os
import time
from typing import Any, Iterator

import requests
from dotenv import load_dotenv

_ORDERS_QUERY = """
query Orders($cursor: String, $q: String!) {
  orders(first: 100, after: $cursor, sortKey: CREATED_AT, query: $q) {
    pageInfo { hasNextPage endCursor }
    edges { node {
      name
      createdAt
      subtotalPriceSet { shopMoney { amount } }
      netPaymentSet { shopMoney { amount } }
      currentSubtotalPriceSet { shopMoney { amount } }
      lineItems(first: 50) { edges { node {
        quantity
        title
        discountedUnitPriceSet { shopMoney { amount } }
      } } }
    } }
  }
}
"""


class ShopifyClient:
    def __init__(self) -> None:
        load_dotenv()
        domain = os.getenv("SHOPIFY_STORE_DOMAIN", "").strip()
        token = os.getenv("SHOPIFY_ADMIN_TOKEN", "").strip()
        version = os.getenv("SHOPIFY_API_VERSION", "2025-01").strip()
        if not domain or not token:
            raise RuntimeError(
                "Config Shopify mancante: SHOPIFY_STORE_DOMAIN e SHOPIFY_ADMIN_TOKEN "
                "(vedi .env.example)."
            )
        if not domain.endswith("myshopify.com"):
            # accetta anche il dominio pubblico, ma l'Admin API vuole *.myshopify.com
            pass
        self.url = f"https://{domain}/admin/api/{version}/graphql.json"
        self.headers = {
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        }

    def _post(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(5):
            r = requests.post(
                self.url,
                json={"query": query, "variables": variables},
                headers=self.headers,
                timeout=30,
            )
            if r.status_code == 429:  # rate limit
                time.sleep(2 * (attempt + 1))
                continue
            r.raise_for_status()
            data = r.json()
            if "errors" in data:
                raise RuntimeError(f"Shopify GraphQL error: {data['errors']}")
            return data["data"]
        raise RuntimeError("Shopify: troppi rate-limit consecutivi")

    def iter_orders(self, since: str, until: str) -> Iterator[dict[str, Any]]:
        """Itera gli ordini creati tra ``since`` e ``until`` (YYYY-MM-DD).

        Restituisce dict semplici: name, created_at, subtotal, net, line_items.
        """
        q = f"created_at:>={since} created_at:<={until}"
        cursor = None
        while True:
            data = self._post(_ORDERS_QUERY, {"cursor": cursor, "q": q})
            conn = data["orders"]
            for edge in conn["edges"]:
                n = edge["node"]
                items = []
                for le in n["lineItems"]["edges"]:
                    ln = le["node"]
                    price = (ln.get("discountedUnitPriceSet") or {}).get("shopMoney", {})
                    items.append({
                        "title": ln["title"],
                        "quantity": ln["quantity"],
                        "price": float(price.get("amount")) if price.get("amount") else None,
                    })
                sub = (n.get("subtotalPriceSet") or {}).get("shopMoney", {}) or {}
                yield {
                    "name": n["name"],
                    "created_at": n["createdAt"][:10],
                    "net_sales": float(sub.get("amount") or 0.0),
                    "line_items": items,
                }
            if not conn["pageInfo"]["hasNextPage"]:
                break
            cursor = conn["pageInfo"]["endCursor"]
