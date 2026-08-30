"""
Lógica de publicación en la cola.
"""

from redis import Redis
from rq import Queue

from app.config import Settings
from app.schemas.queue_message import QueueMessage


def get_queue(redis_conn: Redis, settings: Settings) -> Queue:
    return Queue(settings.queue_name, connection=redis_conn)


def publish_message(queue: Queue, settings: Settings, message: QueueMessage) -> str:
    """
    Encola el mensaje para que el consumer lo procese.

    Devuelve el id del job encolado (útil para logging/trazabilidad).
    """
    job = queue.enqueue(
        settings.consumer_job_path,
        message.to_job_kwargs(),
        retry=None,  # los reintentos ante fallos se configuran del lado worker
    )
    return job.id
