"""
Validación de la firma de los webhooks de Meta (WhatsApp Cloud API).

Meta firma cada POST con HMAC-SHA256 usando el App Secret, en el header
`X-Hub-Signature-256`. Verificar esto es lo que garantiza que el request
realmente viene de Meta y no de un tercero pegándole al endpoint.

Referencia: https://developers.facebook.com/docs/graph-api/webhooks/getting-started#validating-payloads
"""

import hashlib
import hmac

SIGNATURE_PREFIX = "sha256="


def is_valid_signature(payload: bytes, signature_header: str | None, app_secret: str) -> bool:
    """
    Recalcula el HMAC-SHA256 del body crudo con el App Secret y lo compara
    (en tiempo constante) contra el que mandó Meta en el header.
    """
    if not signature_header or not signature_header.startswith(SIGNATURE_PREFIX):
        return False

    expected_signature = signature_header.removeprefix(SIGNATURE_PREFIX)

    computed_signature = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, computed_signature)
