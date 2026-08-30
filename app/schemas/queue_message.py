"""
Contrato interno que viaja por la cola, entre el publisher y el consumer.

Es intencionalmente distinto (y más simple) que el payload crudo de Meta:
el consumer no debería conocer el formato de la WhatsApp Cloud API, solo
este contrato propio. Si el payload de Meta cambia, solo se toca el
publisher (donde se arma este objeto), no el consumer.

Versionado: si en el futuro se necesitan más campos (ej. soporte de
imágenes), se sube `schema_version` y el consumer decide cómo manejar
versiones viejas.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel


class QueueMessage(BaseModel):
    schema_version: int = 1

    message_id: str
    complejo_phone_number_id: str
    from_phone_number: str
    received_at: datetime
    message_type: str
    text: str | None = None

    def to_job_kwargs(self) -> dict:
        """Representación serializable para pasarle al job de RQ."""
        return self.model_dump(mode="json")


def build_queue_message(
    *,
    message_id: str,
    complejo_phone_number_id: str,
    from_phone_number: str,
    message_type: str,
    text: str | None,
) -> QueueMessage:
    return QueueMessage(
        message_id=message_id,
        complejo_phone_number_id=complejo_phone_number_id,
        from_phone_number=from_phone_number,
        received_at=datetime.now(UTC),
        message_type=message_type,
        text=text,
    )
