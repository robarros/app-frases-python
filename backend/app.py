import logging
import sys
import httpx

from fastapi import FastAPI, HTTPException
from pythonjsonlogger import jsonlogger

app = FastAPI()

# =========================
# CONFIGURAÇÃO DE LOG JSON
# =========================

logger = logging.getLogger("service2")
logger.setLevel(logging.INFO)

logHandler = logging.StreamHandler(sys.stdout)

formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s "
    "%(dd.trace_id)s %(dd.span_id)s %(dd.service)s %(dd.env)s %(dd.version)s"
)

logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
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

    except httpx.HTTPError:
        logger.exception("Erro ao buscar frase externa")
        raise HTTPException(status_code=502, detail="falha ao buscar frase")

    return {
        "frase": data.get("quote"),
        "autor": data.get("author"),
        "fonte": "dummyjson.com",
    }