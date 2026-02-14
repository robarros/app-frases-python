# Instrumentação Datadog com Admission Controller

## O que foi configurado

Os deployments do Kubernetes foram instrumentados para usar o **Datadog Admission Controller**, que injeta automaticamente a biblioteca de tracing do Python (`ddtrace`) nos containers sem modificar o código-fonte.

### Annotations adicionadas:
- `admission.datadoghq.com/enabled: "true"` - Habilita a injeção automática
- `admission.datadoghq.com/python-lib.version: "latest"` - Versão da biblioteca dd-trace-py

### Labels adicionadas (Unified Service Tagging):
- `tags.datadoghq.com/env: "production"`
- `tags.datadoghq.com/service: "service1"` / `"service2"`
- `tags.datadoghq.com/version: "1.0.0"`

### Variáveis de ambiente configuradas:
- `DD_SERVICE` - Nome do serviço
- `DD_ENV` - Ambiente (production, staging, etc)
- `DD_VERSION` - Versão da aplicação
- `DD_LOGS_INJECTION` - Correlação de logs com traces
- `DD_TRACE_SAMPLE_RATE` - Taxa de amostragem (1 = 100%)
- `DD_PROFILING_ENABLED` - Habilita profiling contínuo
- `DD_RUNTIME_METRICS_ENABLED` - Coleta métricas de runtime do Python
- `DD_AGENT_HOST` - IP do host onde o Datadog Agent está rodando

## Pré-requisitos

### 1. Datadog Agent instalado no cluster

Instale o Datadog Agent via Helm:

```bash
helm repo add datadog https://helm.datadoghq.com
helm repo update

helm install datadog-agent datadog/datadog \
  --set datadog.apiKey=<SUA_API_KEY> \
  --set datadog.site=datadoghq.com \
  --set datadog.apm.enabled=true \
  --set datadog.logs.enabled=true \
  --set datadog.logs.containerCollectAll=true \
  --namespace datadog \
  --create-namespace
```

### 2. Admission Controller habilitado

O Admission Controller já vem habilitado por padrão quando você instala o Datadog Agent via Helm (versão >= 2.35.0).

Para verificar se está rodando:

```bash
kubectl get pods -n datadog | grep admission
```

### 3. Verificar configuração

Após o deploy, verifique se a injeção funcionou:

```bash
# Verificar pods
kubectl get pods

# Verificar se a lib foi injetada nos logs de inicialização
kubectl logs -l app=service1 | grep -i datadog
kubectl logs -l app=service2 | grep -i datadog

# Verificar variáveis de ambiente
kubectl exec -it <pod-name> -- env | grep DD_
```

## Como funciona

1. Quando você faz `kubectl apply` do deployment, o Admission Controller intercepta a requisição
2. Ele detecta as annotations `admission.datadoghq.com/*`
3. Automaticamente modifica o pod spec para:
   - Adicionar um init container que copia a biblioteca `ddtrace`
   - Modificar o comando do container para usar `ddtrace-run python`
   - Configurar variáveis de ambiente necessárias

4. O resultado é que sua aplicação Python inicia com tracing automático, sem modificar uma linha de código!

## Recursos monitorados

Com essa configuração, você terá no Datadog automaticamente:

- ✅ **APM Traces**: Requisições HTTP, chamadas de banco, etc
- ✅ **Distributed Tracing**: Entre service1 → service2
- ✅ **Profiling**: CPU, memória, threads
- ✅ **Runtime Metrics**: GC, heap, etc
- ✅ **Log Correlation**: Logs linkados aos traces
- ✅ **Service Map**: Visualização da arquitetura

## Customizar ambiente

Para mudar o ambiente (dev, staging, production):

```bash
# Editar os arquivos k8s.yaml e mudar:
tags.datadoghq.com/env: "staging"
DD_ENV: "staging"
```

## Troubleshooting

### Injeção não está funcionando

```bash
# Verificar logs do admission controller
kubectl logs -n datadog -l app=datadog-admission-controller

# Verificar configuração do webhook
kubectl get mutatingwebhookconfigurations | grep datadog
```

### Traces não aparecem no Datadog

```bash
# Verificar conectividade com o Agent
kubectl exec -it <pod-name> -- curl http://$DD_AGENT_HOST:8126/info

# Verificar se o tracer foi injetado
kubectl logs <pod-name> | grep -i "ddtrace"
```

## Referências

- [Datadog Admission Controller](https://docs.datadoghq.com/containers/cluster_agent/admission_controller/)
- [Library Injection](https://docs.datadoghq.com/tracing/trace_collection/library_injection_local/)
- [Unified Service Tagging](https://docs.datadoghq.com/getting_started/tagging/unified_service_tagging/)
