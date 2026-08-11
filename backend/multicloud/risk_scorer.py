"""Risk scoring for cloud assets discovered from live SDK adapters.

Automatically assesses a risk level (normal / warning / critical) for each
cloud resource based on its real attributes (public IP exposure, open ports,
certificate expiry, resource specifications, tags, etc.).

The scorer only overrides resources whose risk level is still ``normal`` so
that explicit levels set by demo templates or operators are preserved.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

CRITICAL_PORTS = {22, 3389, 6379, 9200, 3306}
WARNING_PORTS = {80, 443, 8080, 8000, 27017}
HIGH_RISK_ENV_PORTS = {22, 3389, 6379, 9200}

CERT_EXPIRE_DAYS_WARNING = 45
CERT_EXPIRE_DAYS_CRITICAL = 10

DEFAULT_LEVELS = {'normal', 'warning', 'critical'}


def _safe_int(value: Any, default: int = 0) -> int:
    if value in (None, '', '0'):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _ports_of(metadata: dict | None, tags: dict | None) -> set[int]:
    ports: set[int] = set()
    for source in (metadata, tags):
        if not isinstance(source, dict):
            continue
        for value in (source.get('open_ports'), source.get('ports')):
            if isinstance(value, list):
                for p in value:
                    if isinstance(p, int):
                        ports.add(p)
                    elif isinstance(p, str) and p.isdigit():
                        ports.add(int(p))
    return ports


def _cert_days_until_expiry(metadata: dict | None, tags: dict | None) -> int | None:
    for source in (metadata, tags):
        if not isinstance(source, dict):
            continue
        for key in ('cert_expire_days', 'cert_expires_in_days', 'ssl_expire_days'):
            value = source.get(key)
            if value in (None, ''):
                continue
            days = _safe_int(value)
            return days if days > 0 else None
        for key in ('cert_expire_at', 'cert_expiry_date'):
            value = source.get(key)
            if not value:
                continue
            try:
                dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
                return (dt.date() - date.today()).days
            except (ValueError, TypeError):
                continue
    return None


def _exposed_public_ports(item: dict[str, Any]) -> bool:
    public_ip = item.get('public_ip') or item.get('public_ip_address') or ''
    ports = _ports_of(item.get('metadata'), item.get('tags'))
    return bool(public_ip and ports)


def assess_asset_risk(item: dict[str, Any], environment: Any) -> tuple[str, str]:
    """Return ``(risk_level, risk_reason)`` for a single cloud asset.

    Current ``risk_level`` in ``item`` is preserved if it is not ``normal``.

    Args:
        item: asset dict produced by a cloud SDK adapter.
        environment: CloudEnvironment instance (used for env type).

    Returns:
        Tuple of ``(risk_level, reason)``.
    """
    current = (item.get('risk_level') or 'normal')
    if current not in DEFAULT_LEVELS or current != 'normal':
        return current, item.get('risk_reason') or ''

    metadata = item.get('metadata') or {}
    tags = item.get('tags') or {}
    is_prod = bool(environment and getattr(environment, 'environment_type', None) == 'prod')
    ports = _ports_of(metadata, tags)

    reasons: list[str] = []

    if ports & CRITICAL_PORTS:
        reasons.append(f'高危端口 {sorted(ports & CRITICAL_PORTS)} 暴露')
    if _exposed_public_ports(item) and ports & HIGH_RISK_ENV_PORTS:
        reasons.append(f'公网 IP 暴露高危端口 {sorted(ports & HIGH_RISK_ENV_PORTS)}')

    cert_days = _cert_days_until_expiry(metadata, tags)
    if cert_days is not None:
        if cert_days <= CERT_EXPIRE_DAYS_CRITICAL:
            reasons.append(f'证书 {cert_days} 天后到期')
        elif cert_days <= CERT_EXPIRE_DAYS_WARNING:
            reasons.append(f'证书 {cert_days} 天后即将到期')

    public_ip = item.get('public_ip') or ''
    if public_ip and is_prod:
        reasons.append('生产环境公网暴露')

    if reasons:
        return 'critical' if any(r.startswith('高危') or '到期' in r and '即将' not in r for r in reasons) else 'warning', '；'.join(reasons)

    return 'normal', ''
