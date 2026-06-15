#!/usr/bin/env python3
import base64
import hashlib
import hmac


def verify_shopify_hmac(data: bytes, hmac_header: str, secret: str) -> bool:
    digest = hmac.new(
        secret.encode('utf-8'),
        data,
        hashlib.sha256
    ).digest()

    computed_hmac = base64.b64encode(digest).decode('utf-8')

    return hmac.compare_digest(computed_hmac, hmac_header)
