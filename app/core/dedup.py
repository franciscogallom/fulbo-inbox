"""
Deduplicación de mensajes entrantes.

Meta reintenta el envío de un webhook si no recibe el 200 a tiempo (o ante
errores transitorios). Sin este chequeo, el mismo mensaje podría procesarse
dos veces.

Se usa Redis con SET ... NX (set-if-not-exists) + TTL: es atómico, no
requiere lógica de lectura-luego-escritura, y el TTL evita que la clave
quede para siempre.
"""

from redis import Redis

DEDUP_KEY_PREFIX = "dedup:wsp_message:"


def is_duplicate_message(redis_conn: Redis, message_id: str, ttl_seconds: int) -> bool:
    """
    Devuelve True si este message_id ya fue visto (es un duplicado).
    Devuelve False y lo marca como visto si es la primera vez.
    """
    key = f"{DEDUP_KEY_PREFIX}{message_id}"

    # nx=True -> solo setea si la clave no existe. Devuelve None si ya existía.
    was_set = redis_conn.set(key, "1", nx=True, ex=ttl_seconds)

    return was_set is None
