import logging

import httpx
from fastapi import FastAPI, HTTPException
from ddtrace import tracer
import json_log_formatter

app = FastAPI()

formatter = json_log_formatter.JSONFormatter()
json_handler = logging.StreamHandler()
json_handler.setFormatter(formatter)

logger = logging.getLogger("service2")
logger.addHandler(json_handler)
logger.setLevel(logging.INFO)

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
