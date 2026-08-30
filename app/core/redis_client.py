"""
Conexión a Redis, compartida por el resto de la app (dedup y cola).

Se crea una única instancia por proceso (patrón singleton simple).
redis-py maneja pooling de conexiones internamente. No hace
falta abrir/cerrar conexiones a mano en cada request.
"""

from functools import lru_cache

from redis import Redis

from app.config import get_settings


@lru_cache
def get_redis() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)
