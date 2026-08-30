"""
Configuración de la aplicación.

Todo lo que cambia entre entornos (local, staging, producción) vive acá,
leído desde variables de entorno. 

En local se puede usar un archivo `.env`; en producción, las variables 
se inyectan directamente desde el proveedor de hosting.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Entorno ---
    environment: Literal["local", "staging", "production"] = "local"
    log_level: str = "INFO"

    # --- Servidor ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- WhatsApp Cloud API ---
    # Token que se elige y configura en el panel de Meta para la
    # verificación inicial del webhook (GET /webhook).
    whatsapp_verify_token: str
    # App Secret de la app de Meta, usado para validar la firma
    # X-Hub-Signature-256 de cada request entrante (POST /webhook).
    whatsapp_app_secret: str

    # --- Redis / Cola ---
    # Ejemplo local:        redis://localhost:6379/0
    # Ejemplo productivo:   rediss://default:<password>@<host>:<port>/0
    redis_url: str = "redis://localhost:6379/0"
    queue_name: str = "wsp_messages"

    # Nombre del job (path importable) que fulbo-tiki-taka (consumer) expone
    # para procesar cada mensaje.
    consumer_job_path: str = "worker.procesar_mensaje"

    # --- Deduplicación de mensajes ---
    # Tiempo que se recuerda un message_id ya procesado, para descartar
    # reintentos de Meta del mismo evento.
    dedup_ttl_seconds: int = 60 * 60 * 24  # 24hs

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Settings cacheados (se leen una sola vez por proceso)."""
    return Settings()
