import logging
import sys
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from datadog import DogStatsd
from fastapi import FastAPI, HTTPException, Request
from pythonjsonlogger import jsonlogger

app = FastAPI()

# =========================
# CONFIGURAÇÃO DOGSTATSD
# =========================
# Em K8s, o agent roda nos nodes e o pod expõe o host via downward API
# ou via variável DD_AGENT_HOST injetada automaticamente pelo Datadog Operator.
statsd = DogStatsd(
    host=os.getenv("DD_AGENT_HOST", "localhost"),
    port=int(os.getenv("DD_DOGSTATSD_PORT", 8125)),
    namespace="api_front",
    constant_tags=[
        f"service:{os.getenv('DD_SERVICE', 'api-front')}",
        f"env:{os.getenv('DD_ENV', 'dev')}",
        f"version:{os.getenv('DD_VERSION', '1.0.0')}",
    ],
)

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
VERSION = os.getenv("VERSION", "1.0.0")
BR_TZ = ZoneInfo("America/Sao_Paulo")


@app.get("/")
def root():
    now = datetime.now(BR_TZ).isoformat()
    logger.info("GET / root chamada")
    return {"mensagem": "ola mundo", "hora_brasil": now, "version": VERSION}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/frases")
async def frases(request: Request):
    start = time.perf_counter()
    status_tag = "status:success"
    try:
        logger.info("GET /frases chamada")

        # Incrementa contador de requisições (usado para calcular rate no Datadog)
        statsd.increment("frases.requests", tags=["endpoint:/frases"])

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(SERVICE2_URL)
            response.raise_for_status()
            result = response.json()
            return result

    except httpx.HTTPError:
        logger.exception("Erro ao buscar frases do service2")
        status_tag = "status:error"
        raise HTTPException(status_code=502, detail="falha ao buscar frases")

    finally:
        # Métrica distribution de latência em milissegundos
        # distribution agrega no agent-side: p50, p75, p90, p95, p99, max, avg
        elapsed_ms = (time.perf_counter() - start) * 1000
        statsd.distribution(
            "frases.latency_ms",
            elapsed_ms,
            tags=["endpoint:/frases", status_tag],
        )


@app.get("/error")
def erro500():
    logger.error("GET /error chamada")
    raise RuntimeError("erro intencional para teste")