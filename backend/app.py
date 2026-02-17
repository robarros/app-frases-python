import logging
import sys
import os
import httpx

from fastapi import FastAPI, HTTPException
from pythonjsonlogger import jsonlogger

app = FastAPI()

# =========================
# CONFIGURAÇÃO DE LOG JSON
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

logger = logging.getLogger("service2")
logger.setLevel(logging.INFO)

logHandler = logging.StreamHandler(sys.stdout)

formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s "
    "%(dd_trace_id)s %(dd_span_id)s %(dd_service)s %(dd_env)s %(dd_version)s"
)

logHandler.setFormatter(formatter)
logHandler.addFilter(DatadogTraceFilter())
logger.addHandler(logHandler)
logger.propagate = False

QUOTE_URL = os.getenv('QUOTE_URL', 'https://dummyjson.com/quotes/random')
VERSION = os.getenv('VERSION', '1.0.0')


@app.get("/frases")
async def frases():
    try:
        logger.info("GET /frases chamada")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                QUOTE_URL,
                headers={"User-Agent": "service2/1.0"},
            )
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPError:
        logger.exception("Erro ao buscar frase externa")
        raise HTTPException(status_code=502, detail="falha ao buscar frase")

    return {
        "frase": data.get("quote"),
        "autor": data.get("author"),
        "fonte": "dummyjson.com",
        "version": VERSION,
    }
