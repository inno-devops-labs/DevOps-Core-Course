# Lab 16 Solution

Kubernetes monitoring and init containers.

Commands:

```bash
cd lab16-solution
docker build -t lab16-app:latest .
kind load docker-image lab16-app:latest
kubectl apply -f k8s/init-containers.yaml
kubectl apply -f k8s/app.yaml
kubectl apply -f k8s/servicemonitor.yaml
.\windows-amd64\helm.exe repo add prometheus-community https://prometheus-community.github.io/helm-charts
.\windows-amd64\helm.exe repo update
.\windows-amd64\helm.exe install monitoring prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace
```