# fulbo-inbox

Recibe los webhooks de WhatsApp Cloud API, valida que sean legítimos, descarta
duplicados y publica cada mensaje en una cola (Redis + RQ) para que el
**futbol-tiki-taka** lo procese.

Es el "publisher" dentro de la arquitectura: la puerta de
entrada del sistema. No conoce al agente, no toca la base de datos de
reservas, no le contesta al usuario — su única responsabilidad es recibir
y encolar rápido.

## Estructura del proyecto

```
fulbo-inbox/
├── pyproject.toml          # dependencias (gestionadas con uv)
├── uv.lock
├── .env.example            # variables de entorno documentadas
├── docker-compose.yml       # Redis local, para no instalarlo a mano
└── app/
    ├── main.py              # entrypoint FastAPI + /health
    ├── config.py            # Settings (pydantic-settings), por entorno
    ├── api/
    │   └── webhook.py        # endpoints GET/POST /webhook
    ├── core/
    │   ├── security.py       # validación de firma HMAC (X-Hub-Signature-256)
    │   ├── dedup.py           # deduplicación por message_id (Redis SET NX)
    │   └── redis_client.py    # conexión a Redis compartida
    ├── schemas/
    │   ├── whatsapp.py        # payload crudo de la WhatsApp Cloud API
    │   └── queue_message.py   # contrato interno versionado hacia la cola
    └── services/
        └── publisher.py       # lógica de encolado (RQ), aislada del router
```

`api/` solo conoce HTTP; `core/` tiene las piezas de infraestructura 
(Redis, firma) reutilizables; `services/` tiene la lógica de negocio 
del publisher (encolar); `schemas/` separa el formato de Meta del 
contrato propio que consume el consumer.

## Cómo correrlo

### Levantar Redis local

```bash
docker compose up -d
```

### Levantar el servidor

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Probar que responde:

```bash
curl http://localhost:8000/health
```

## Configuración por entorno

Todo se controla por variables de entorno (ver `.env.example`), leídas por
`app/config.py` vía `pydantic-settings`. Lo único que cambia entre local y
producción es `REDIS_URL`:

```bash
# Local
REDIS_URL=redis://localhost:6379/0

# Productivo (ejemplo Upstash, con TLS)
REDIS_URL=rediss://default:<password>@<host>:<port>
```

En producción no se usa el archivo `.env` — las variables se cargan
directamente desde el proveedor de hosting, y
`ENVIRONMENT=production` habilita el flag `settings.is_production`.

## Exponer el webhook para probarlo con Meta (desarrollo)

Meta necesita una URL pública HTTPS para poder pegarle a tu webhook. En
local, se puede usar algo como `ngrok`:

```bash
ngrok http 8000
```

Y usar la URL que te da (`https://xxxx.ngrok-free.app/webhook`) al
configurar el webhook en el panel de Meta, junto con el mismo
`WHATSAPP_VERIFY_TOKEN` del `.env`.

## El contrato con el consumer

El publisher no importa código del consumer — solo referencia el nombre
del job por string (`CONSUMER_JOB_PATH`, default `worker.procesar_mensaje`)
al encolar. El consumer expone una función con ese path, que RQ resuelve
del lado del worker. Ambos repos deben acordar:

1. El mismo `QUEUE_NAME` / conexión a Redis.
2. El schema de `QueueMessage` (`app/schemas/queue_message.py`), incluyendo
   `schema_version` para poder evolucionarlo sin romper al consumer.
