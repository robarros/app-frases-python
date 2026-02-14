import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI, HTTPException
from ddtrace import tracer
import json_log_formatter

app = FastAPI()

formatter = json_log_formatter.JSONFormatter()
json_handler = logging.StreamHandler()
json_handler.setFormatter(formatter)

logger = logging.getLogger("api-front")
logger.addHandler(json_handler)
logger.setLevel(logging.INFO)

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
    except httpx.HTTPError as exc:
        logger.exception("Erro ao buscar frases do service2", exc_info=exc)
        raise HTTPException(status_code=502, detail="falha ao buscar frases") from exc


@app.get("/error")
def erro500():
    logger.error("GET /error chamada")
    raise RuntimeError("erro intencional para teste")
