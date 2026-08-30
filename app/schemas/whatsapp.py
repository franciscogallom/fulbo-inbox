"""
Modelos del payload que manda la WhatsApp Cloud API al webhook.

Son intencionalmente permisivos (no todos los campos son obligatorios)
porque Meta manda distintas "shapes" de evento al mismo endpoint:
mensajes de usuarios, actualizaciones de estado (delivered/read), etc.
Acá solo nos interesan los eventos de tipo "messages" con texto.

Referencia: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class WhatsAppText(BaseModel):
    body: str


class WhatsAppMessage(BaseModel):
    id: str
    from_: str = Field(alias="from")
    timestamp: str
    type: str
    text: WhatsAppText | None = None
    # Otros tipos (image, audio, location, interactive, etc.) se reciben pero por ahora no se procesan más allá de reenviarlos tal cual.


class WhatsAppMetadata(BaseModel):
    display_phone_number: str | None = None
    phone_number_id: str


class WhatsAppValue(BaseModel):
    messaging_product: str | None = None
    metadata: WhatsAppMetadata
    messages: list[WhatsAppMessage] | None = None
    statuses: list[dict] | None = None  # delivery/read receipts, se ignoran


class WhatsAppChange(BaseModel):
    value: WhatsAppValue
    field: str


class WhatsAppEntry(BaseModel):
    id: str
    changes: list[WhatsAppChange]


class WhatsAppWebhookPayload(BaseModel):
    object: str
    entry: list[WhatsAppEntry]
