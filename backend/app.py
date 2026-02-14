import logging

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("service2")

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
