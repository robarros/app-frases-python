import logging
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI, HTTPException
from pythonjsonlogger import jsonlogger

app = FastAPI()

# =========================
# CONFIGURAÇÃO LOG JSON
# =========================

# Filtro customizado para injeção de trace do Datadog
class DatadogTraceFilter(logging.Filter):
    def filter(self, record):
        try:
            from ddtrace import tracer
            span = tracer.current_span()
            if span:
                record.dd_trace_id = span.trace_id
                record.dd_span_id = span.span_id
                record.dd_service = os.getenv('DD_SERVICE', '')
                record.dd_env = os.getenv('DD_ENV', '')
                record.dd_version = os.getenv('DD_VERSION', '')
            else:
                record.dd_trace_id = 0
                record.dd_span_id = 0
                record.dd_service = os.getenv('DD_SERVICE', '')
                record.dd_env = os.getenv('DD_ENV', '')
                record.dd_version = os.getenv('DD_VERSION', '')
        except Exception:
            record.dd_trace_id = 0
            record.dd_span_id = 0
            record.dd_service = os.getenv('DD_SERVICE', '')
            record.dd_env = os.getenv('DD_ENV', '')
            record.dd_version = os.getenv('DD_VERSION', '')
        return True

logger = logging.getLogger("api-front")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)

formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s "
    "%(filename)s %(lineno)d %(dd_trace_id)s %(dd_span_id)s %(dd_service)s %(dd_env)s %(dd_version)s"
)

handler.setFormatter(formatter)
handler.addFilter(DatadogTraceFilter())
logger.addHandler(handler)
logger.propagate = False

# =========================

SERVICE2_URL = os.getenv("SERVICE2_URL", "http://service2:8080/frases")
BR_TZ = ZoneInfo("America/Sao_Paulo")


@app.get("/")
def root():
    now = datetime.now(BR_TZ).isoformat()
    logger.info("GET / root chamada")
    return {"mensagem": "ola mundo", "hora_brasil": now}


@app.get("/frases")
async def frases():
    try:
        logger.info("GET /frases chamada")

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(SERVICE2_URL)
            response.raise_for_status()
            return response.json()

    except httpx.HTTPError:
        logger.exception("Erro ao buscar frases do service2")
        raise HTTPException(status_code=502, detail="falha ao buscar frases")


@app.get("/error")
def erro500():
    logger.error("GET /error chamada")
    raise RuntimeError("erro intencional para teste")