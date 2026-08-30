"""
Entrypoint de la app.

Responsabilidad de fulbo-inbox:
    - Recibir los webhooks de WhatsApp Cloud API.
    - Validar que vienen de Meta.
    - Descartar duplicados.
    - Publicarlos en la cola.
    - Responder rápido (200 OK).

"""

import logging

from fastapi import FastAPI

from app.api.webhook import router as webhook_router
from app.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="fulbo-inbox",
    description="Recibe webhooks de WhatsApp Cloud API y los publica en la cola.",
    version="0.1.0",
)

app.include_router(webhook_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}
