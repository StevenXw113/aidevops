"""Dynamic cloud regions and availability zones for IaC stacks.

When a live cloud credential (non-demo) is configured for a provider, regions
and availability zones are fetched in real time from the cloud provider API.
Otherwise the static ``PROVIDER_CATALOG`` definitions are returned as a
fallback so IaC can still render without live credentials.
"""

from __future__ import annotations

from multicloud.models import CloudCredential
from multicloud.sdk_adapters import get_cloud_adapter

from .terraform import PROVIDER_CATALOG


def _static_provider_regions(provider: str) -> dict:
    meta = PROVIDER_CATALOG.get(provider) or {}
    regions = meta.get('regions') or []
    zones = meta.get('zone_options') or {}
    return {
        'regions': [{'value': r.get('value'), 'label': r.get('label') or r.get('value')} for r in regions],
        'zones': zones,
        'source': 'static',
    }


def get_provider_regions(provider: str, prefer_live: bool = True, credential_id: int | None = None) -> dict:
    """Return regions and availability zones for a provider.

    Args:
        provider: cloud provider id (aliyun / tencent / huaweicloud / aws).
        prefer_live: whether to try the live cloud API first.
        credential_id: optional cloud credential id to use for the live call.

    Returns:
        Dict with ``regions``, ``zones`` and ``source`` (``live`` or ``static``).
    """
    if prefer_live:
        live = _live_provider_regions(provider, credential_id=credential_id)
        if live:
            return live
    return _static_provider_regions(provider)


def regions_for_all_providers(prefer_live: bool = True) -> dict:
    """Return regions for every supported IaC provider.

    Args:
        prefer_live: whether to try the live cloud API for each provider.

    Returns:
        Mapping of provider -> regions payload.
    """
    return {
        provider: get_provider_regions(provider, prefer_live=prefer_live)
        for provider in PROVIDER_CATALOG
    }


def _live_provider_regions(provider: str, credential_id: int | None = None) -> dict | None:
    queryset = CloudCredential.objects.filter(
        provider=provider,
        demo_mode=False,
    ).exclude(auth_mode='demo').exclude(access_key_id='').exclude(access_key_secret='')
    if credential_id:
        queryset = queryset.filter(id=credential_id)
    credential = queryset.order_by('id').first()
    if not credential:
        return None
    adapter = get_cloud_adapter(credential)
    if not adapter:
        return None
    try:
        result = adapter.fetch_regions()
        if not result.get('regions'):
            return None
        result['source'] = 'live'
        result['account_name'] = credential.name
        return result
    except Exception:
        return None
