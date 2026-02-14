import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import json

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI()

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Captura trace_id e span_id injetados pelo ddtrace
        if hasattr(record, 'dd.trace_id'):
            log_record['dd.trace_id'] = str(getattr(record, 'dd.trace_id'))
        if hasattr(record, 'dd.span_id'):
            log_record['dd.span_id'] = str(getattr(record, 'dd.span_id'))
        if hasattr(record, 'dd.service'):
            log_record['dd.service'] = getattr(record, 'dd.service')
        if hasattr(record, 'dd.env'):
            log_record['dd.env'] = getattr(record, 'dd.env')
        if hasattr(record, 'dd.version'):
            log_record['dd.version'] = getattr(record, 'dd.version')
        return json.dumps(log_record)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())

logger = logging.getLogger("api-front")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

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
