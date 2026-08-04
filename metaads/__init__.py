"""Integrazione con la Meta Marketing API (Facebook / Instagram Ads)."""

from .client import MetaAdsClient
from .config import MetaConfig, load_config

__all__ = ["MetaAdsClient", "MetaConfig", "load_config"]
