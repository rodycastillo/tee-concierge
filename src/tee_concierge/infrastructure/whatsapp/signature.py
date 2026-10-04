import hashlib
import hmac


def sign(app_secret: str, body: bytes) -> str:
    digest = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(app_secret: str, body: bytes, header: str | None) -> bool:
    """Check Meta's `X-Hub-Signature-256` header in constant time."""
    if not app_secret or not header:
        return False
    return hmac.compare_digest(sign(app_secret, body), header)
