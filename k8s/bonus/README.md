# Bonus: Ingress with TLS

1. Enable ingress controller

- Minikube:
  - minikube addons enable ingress
- kind:
  - kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

2. Deploy second app and cluster services

- kubectl apply -f k8s/bonus/deployment-app2.yml
- kubectl apply -f k8s/bonus/service-app1.yml
- kubectl apply -f k8s/bonus/service-app2.yml

3. Generate TLS secret manifest

- cd k8s/bonus
- chmod +x generate-tls.sh
- ./generate-tls.sh
- kubectl apply -f tls-secret.yml

4. Apply ingress

- kubectl apply -f k8s/bonus/ingress.yml

5. Add hosts entry

- map local.example.com to your cluster ingress IP

6. Verify

- curl -k https://local.example.com/app1/health
- curl -k https://local.example.com/app2/health
