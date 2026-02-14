import logging
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

logger = logging.getLogger("service2")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

QUOTE_URL = "https://dummyjson.com/quotes/random"


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
    except httpx.HTTPError as exc:
        logger.exception("Erro ao buscar frase externa", exc_info=exc)
        raise HTTPException(status_code=502, detail="falha ao buscar frase") from exc

    return {
        "frase": data.get("quote"),
        "autor": data.get("author"),
        "fonte": "dummyjson.com",
    }
