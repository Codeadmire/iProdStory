"""
SSRF (Server-Side Request Forgery) protection.

Validates crawl target URLs to ensure we only crawl legitimate
public web pages — not internal services, metadata endpoints, or
private network addresses.
"""
import ipaddress
import socket
from urllib.parse import urlparse
from fastapi import HTTPException, status

# Known dangerous internal hostnames / cloud metadata endpoints
_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "169.254.169.254",  # AWS/GCP/Azure metadata
    "instance-data",
}

# RFC-1918 + loopback + link-local + CGNAT private ranges
_PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _is_private_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return any(addr in net for net in _PRIVATE_RANGES)
    except ValueError:
        return False


def validate_crawl_url(url: str) -> str:
    """
    Validate and normalise a URL before passing it to the crawler.
    Raises HTTPException 422 on any violation.
    Returns the normalised URL on success.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Malformed URL")

    # 1. Allow only http/https
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only http and https URLs are supported",
        )

    hostname = parsed.hostname or ""
    if not hostname:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="URL must include a hostname")

    # 2. Block known dangerous hostnames
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="URL targets a blocked hostname")

    # 3. Resolve and check for private IPs
    try:
        resolved_ips = [r[4][0] for r in socket.getaddrinfo(hostname, None)]
    except socket.gaierror:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Could not resolve hostname: {hostname}")

    for ip in resolved_ips:
        if _is_private_ip(ip):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="URL resolves to a private/internal IP address",
            )

    # Return a clean URL (no fragment, no credentials)
    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if parsed.query:
        clean += f"?{parsed.query}"
    return clean
