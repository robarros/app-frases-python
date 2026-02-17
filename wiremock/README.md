# WireMock - Mock de API de Frases

Este diretório contém a configuração do WireMock para mockar a API externa `dummyjson.com/quotes`.

## Estrutura

```
wiremock/
├── mappings/
│   └── quotes-random.json    # Mock da resposta de frases (referência)
├── Dockerfile                 # Imagem Docker do WireMock
├── k8s.yaml                   # ConfigMap + Deployment + Service
└── README.md                  # Esta documentação
```

## Arquitetura

Os mappings do WireMock são fornecidos via **ConfigMap do Kubernetes**, permitindo:
- ✅ Alterar mocks sem rebuildar a imagem Docker
- ✅ Versionamento junto com os manifestos K8s
- ✅ Facilidade para gerenciar múltiplos ambientes

## Mock Configurado

**Endpoint:** `GET /quotes/random`

**Resposta:**
```json
{
  "id": 42,
  "quote": "A jornada de mil milhas começa com um único passo.",
  "author": "Lao Tzu"
}
```

## Build da Imagem Docker

A imagem usa a versão oficial do WireMock e não precisa incluir os mappings:

```bash
cd wiremock
docker build -t wiremock:latest .
```

**Nota:** Com ConfigMaps, você pode usar diretamente a imagem oficial sem build:
```yaml
image: wiremock/wiremock:3.3.1-alpine
```

## Teste Local com Docker

Para testar localmente com os mappings do diretório `mappings/`:

```bash
docker run -it --rm \
  -p 8080:8080 \
  -v $PWD/mappings:/home/wiremock/mappings \
  wiremock/wiremock:3.3.1-alpine
```

Teste o endpoint:
```bash
curl http://localhost:8080/quotes/random
```

## Deploy no Kubernetes

O manifesto `k8s.yaml` contém:
1. **ConfigMap** com os mappings do WireMock
2. **Deployment** que monta o ConfigMap como volume
3. **Service** para acesso interno no cluster

### Deploy

```bash
kubectl apply -f k8s.yaml
```

Verifique o status:
```bash
kubectl get pods -l app=wiremock
kubectl get svc wiremock
kubectl get configmap wiremock-mappings
```

### Deploy via ArgoCD

```bash
kubectl apply -f argocd/apps/wiremock.yaml
```

### Alterando os Mocks

Para modificar os mocks sem rebuildar a imagem:

1. Edite o ConfigMap no `k8s.yaml`
2. Aplique as mudanças:
   ```bash
   kubectl apply -f k8s.yaml
   ```
3. Reinicie os pods para carregar os novos mappings:
   ```bash
   kubectl rollout restart deployment/wiremock
   ```

Ou edite o ConfigMap diretamente no cluster:
```bash
kubectl edit configmap wiremock-mappings
kubectl rollout restart deployment/wiremock
```

## Adicionando Novos Mocks

Para adicionar novos endpoints mockados, edite o ConfigMap em `k8s.yaml` e adicione um novo arquivo:
   ```yaml
   data:
     quotes-random.json: |
       { ... }
     novo-endpoint.json: |
       {
         "request": {
           "method": "GET",
           "urlPath": "/seu/endpoint"
         },
         "response": {
           "status": 200,
           "headers": {
             "Content-Type": "application/json"
           },
           "jsonBody": {
             "sua": "resposta"
           }
         }
       }
   ```

2. Aplique e reinicie:
   ```bash
   kubectl apply -f k8s.yaml
   kubectl rollout restart deployment/wiremock
   ```

**Veja também:** [k8s-multi-mappings-example.yaml](k8s-multi-mappings-example.yaml) para exemplos de múltiplos endpoints, delays e erros simulados.

## Usando o WireMock no Backend

Para usar o WireMock ao invés da API real, altere a variável `QUOTE_URL` no backend:

```python
# backend/app.py
QUOTE_URL = "http://wiremock:8080/quotes/random"
```

Ou configure via variável de ambiente no Kubernetes:

```yaml
env:
- name: QUOTE_URL
  value: "http://wiremock:8080/quotes/random"
```

## Admin API

O WireMock expõe uma API admin em `/__admin/` para gerenciamento:

- Health check: `GET /__admin/health`
- Listar mappings: `GET /__admin/mappings`
- Reset: `POST /__admin/reset`

## Documentação Oficial

https://wiremock.org/docs/
