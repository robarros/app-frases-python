FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]


# docker buildx build --platform linux/arm64 -t robarros/api-front:v14 --push .


# docker buildx build --platform linux/amd64,linux/arm64 -t robarros/api-front:v14 --push .

