# Deploy no Kubernetes

## Build das imagens

```bash
# Service 1
docker build -t service1:latest ./service1

# Service 2
docker build -t service2:latest ./service2
```

## Carregar imagens no cluster (se usando kind ou minikube)

### Para kind:
```bash
kind load docker-image service1:latest
kind load docker-image service2:latest
```

### Para minikube:
```bash
minikube image load service1:latest
minikube image load service2:latest
```

## Deploy no cluster

```bash
# Deploy service2 primeiro (dependência)
kubectl apply -f service2/k8s.yaml

# Deploy service1
kubectl apply -f service1/k8s.yaml
```

## Verificar status

```bash
kubectl get pods
kubectl get services
```

## Acessar o serviço

### Se usando LoadBalancer (cloud):
```bash
kubectl get service service1
# Use o EXTERNAL-IP mostrado
curl http://<EXTERNAL-IP>:8080/
curl http://<EXTERNAL-IP>:8080/frases
```

### Se usando minikube:
```bash
minikube service service1 --url
# Use a URL retornada
```

### Se usando kind com port-forward:
```bash
kubectl port-forward service/service1 8080:8080
curl http://localhost:8080/
curl http://localhost:8080/frases
```

## Logs

```bash
kubectl logs -l app=service1 --tail=50 -f
kubectl logs -l app=service2 --tail=50 -f
```

## Remover do cluster

```bash
kubectl delete -f service1/k8s.yaml
kubectl delete -f service2/k8s.yaml
```
[![App Status](https://argocd.virtualti.net/api/badge?name=app-frases-python&revision=true&showAppName=true)](https://argocd.virtualti.net/applications/app-frases-python)