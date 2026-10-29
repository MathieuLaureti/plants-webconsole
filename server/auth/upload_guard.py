import ipaddress

from fastapi import HTTPException, Request, status

from auth.config import (
    PUBLIC_API_HOSTS,
    UPLOAD_ALLOWED_CIDRS,
    UPLOAD_FORBIDDEN_CLIENT_IPS,
)


def _parse_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _host_matches_public(host_header: str | None) -> bool:
    if not host_header:
        return False
    host = host_header.split(":")[0].strip().lower()
    public_hosts = {h.lower() for h in _parse_csv(PUBLIC_API_HOSTS)}
    return host in public_hosts


def _client_ip(request: Request) -> str:
    if request.client is None:
        return ""
    return request.client.host


def _ip_allowed(client_ip: str) -> bool:
    if not client_ip:
        return False
    try:
        addr = ipaddress.ip_address(client_ip)
    except ValueError:
        return False
    for cidr in _parse_csv(UPLOAD_ALLOWED_CIDRS):
        try:
            if addr in ipaddress.ip_network(cidr, strict=False):
                return True
        except ValueError:
            continue
    return False


def require_lan_upload(request: Request) -> None:
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if _host_matches_public(host):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Upload not available on public host",
        )

    client_ip = _client_ip(request)
    forbidden = set(_parse_csv(UPLOAD_FORBIDDEN_CLIENT_IPS))
    if client_ip in forbidden:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Upload not allowed from this client",
        )

    if not _ip_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Upload allowed from LAN clients only",
        )
