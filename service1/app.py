import os
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI()

SERVICE2_URL = os.getenv("SERVICE2_URL", "http://service2:8080/frases")
BR_TZ = ZoneInfo("America/Sao_Paulo")


@app.get("/")
def root():
    now = datetime.now(BR_TZ).isoformat()
    return {"mensagem": "ola mundo", "hora_brasil": now}


@app.get("/frases")
async def frases():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(SERVICE2_URL)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="falha ao buscar frases") from exc
