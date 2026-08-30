"""
Router del webhook de WhatsApp Cloud API.

Dos endpoints, ambos exigidos por Meta:

- GET  /webhook : usado una única vez al configurar el webhook en el panel de Meta, para verificar el endpoint.
- POST /webhook : acá llega cada evento real (mensajes, estados, etc).
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.core.dedup import is_duplicate_message
from app.core.redis_client import get_redis
from app.core.security import is_valid_signature
from app.schemas.queue_message import build_queue_message
from app.schemas.whatsapp import WhatsAppWebhookPayload
from app.services.publisher import get_queue, publish_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.get("")
def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
    settings: Settings = Depends(get_settings),
):
    """
    Handshake de verificación que exige Meta al dar de alta el webhook.
    Ver: https://developers.facebook.com/docs/graph-api/webhooks/getting-started
    """
    if hub_mode != "subscribe" or hub_verify_token != settings.whatsapp_verify_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token de verificación inválido")

    # Meta espera el challenge devuelto tal cual, como texto plano.
    return int(hub_challenge)


@router.post("", status_code=status.HTTP_200_OK)
async def receive_webhook_event(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
):
    settings = get_settings()
    raw_body = await request.body()

    if not is_valid_signature(raw_body, x_hub_signature_256, settings.whatsapp_app_secret):
        logger.warning("Firma inválida en request entrante al webhook")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Firma inválida")

    try:
        payload = WhatsAppWebhookPayload.model_validate_json(raw_body)
    except ValidationError:
        logger.exception("Payload de webhook con formato inesperado")
        # Devolvemos 200 igual: Meta reintentaría un payload malformado indefinidamente sin ningún beneficio.
        return {"status": "ignored", "reason": "payload_no_reconocido"}

    redis_conn = get_redis()
    queue = get_queue(redis_conn, settings)

    published_count = 0

    for entry in payload.entry:
        for change in entry.changes:
            if not change.value.messages:
                continue  # ej. delivery/read receipts, no nos interesan

            phone_number_id = change.value.metadata.phone_number_id

            for wa_message in change.value.messages:
                if is_duplicate_message(redis_conn, wa_message.id, settings.dedup_ttl_seconds):
                    logger.info("Mensaje duplicado descartado: %s", wa_message.id)
                    continue

                queue_message = build_queue_message(
                    message_id=wa_message.id,
                    complejo_phone_number_id=phone_number_id,
                    from_phone_number=wa_message.from_,
                    message_type=wa_message.type,
                    text=wa_message.text.body if wa_message.text else None,
                )

                job_id = publish_message(queue, settings, queue_message)
                logger.info(
                    "Mensaje %s publicado en la cola (job=%s, complejo=%s)",
                    wa_message.id,
                    job_id,
                    phone_number_id,
                )
                published_count += 1

    return {"status": "ok", "published": published_count}
