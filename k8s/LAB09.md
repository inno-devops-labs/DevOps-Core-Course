# Kubernetes Lab 9 Report

## 1. Architecture Overview

### Logical architecture

```text
+-----------------------+
| Client (Browser/curl) |
+-----------------------+
            |
            v
+----------------------------------------------+
| NodePort Service: devops-info-service        |
| Service port 80 -> targetPort 5000           |
+----------------------------------------------+
            |
            v
+----------------------------------------------+
| Deployment: devops-info-service              |
| replicas: 3                                  |
+----------------------------------------------+
            |
            v
+----------------------------------------------+
| Pods (label: app=devops-info-service)        |
+----------------------------------------------+
```

### Bonus architecture (Ingress + TLS + second app)

```text
+----------------------------------+
| User -> https://local.example.com|
+----------------------------------+
                 |
                 v
+------------------------------------------------+
| Ingress NGINX (TLS termination)                |
| host: local.example.com                        |
+------------------------------------------------+
        | /app1                          | /app2
        v                                v
+-------------------------------+   +-----------------------+
| Service: devops-info-service  |   | Service: hello-app    |
| port 80 -> targetPort 5000    |   | port 80 -> target 80  |
+-------------------------------+   +-----------------------+
        |                                |
        v                                v
+-------------------------------+   +-----------------------+
| Deployment app1 (3 replicas)  |   | Deployment app2 (2)   |
+-------------------------------+   +-----------------------+
```

### Resource allocation strategy

- App 1 (`devops-info-service`): request `100m CPU / 128Mi`, limit `250m CPU / 256Mi`.
- App 2 (`hello-app`): request `50m CPU / 64Mi`, limit `200m CPU / 128Mi`.
- Health probes configured for both apps to support self-healing and safe rollouts.

---

## 2. Manifest Files

### Core task manifests

- `deployment.yml`
  - Deployment `devops-info-service` with 3 replicas.
  - Image `graymansion/devops-info-service:lab02`.
  - RollingUpdate strategy with `maxSurge: 1` and `maxUnavailable: 0`.
  - `livenessProbe`, `readinessProbe`, and `startupProbe` on `/health`.
  - Resource requests/limits and container hardening.

- `service.yml`
  - NodePort Service `devops-info-service`.
  - Service port `80` to target port `5000`.
  - Fixed `nodePort: 30080`.

### Bonus manifests

- `deployment-app2.yml`: second app deployment (`hello-app`).
- `service-app2.yml`: second app service (`ClusterIP`).
- `ingress.yml`: path-based routing + TLS (`/app1` and `/app2`).

### Why these values

- 3 replicas for availability and rolling updates.
- Conservative requests/limits for stable local scheduling.
- Zero-downtime rolling update settings.
- NodePort for simple local external access.

---

## 3. Deployment Evidence

### Tool and cluster setup

```bash
$ ./.tools/bin/kind version
kind v0.29.0 go1.24.2 linux/amd64

$ sudo ./.tools/bin/kind create cluster --name lab9
Creating cluster "lab9" ...
 ✓ Ensuring node image (kindest/node:v1.33.1) 🖼
 ✓ Preparing nodes 📦
 ✓ Writing configuration 📜
 ✓ Starting control-plane 🕹️
 ✓ Installing CNI 🔌
 ✓ Installing StorageClass 💾
Set kubectl context to "kind-lab9"

$ sudo ./.tools/bin/kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:40751
CoreDNS is running at https://127.0.0.1:40751/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ sudo ./.tools/bin/kubectl get nodes
NAME                 STATUS   ROLES           AGE   VERSION
lab9-control-plane   Ready    control-plane   55s   v1.33.1

$ ./.tools/bin/kubectl version --client
Client Version: v1.33.1
Kustomize Version: v5.6.0
```

### Core deployment evidence

```bash
$ sudo ./.tools/bin/kubectl apply -f k8s/deployment.yml
deployment.apps/devops-info-service created

$ sudo ./.tools/bin/kubectl apply -f k8s/service.yml
service/devops-info-service created

$ sudo ./.tools/bin/kubectl get all
NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-6b96c9584-8jw7q   1/1     Running   0          59s
pod/devops-info-service-6b96c9584-c7g6p   1/1     Running   0          53s
pod/devops-info-service-6b96c9584-mqpcj   1/1     Running   0          40s

NAME                          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort    10.96.58.156   <none>        80:30080/TCP   16m
service/kubernetes            ClusterIP   10.96.0.1      <none>        443/TCP        40m

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   3/3     3            3           16m

$ sudo ./.tools/bin/kubectl get pods,svc -o wide
NAME                                      READY   STATUS    RESTARTS   AGE   IP            NODE                 NOMINATED NODE   READINESS GATES
pod/devops-info-service-6b96c9584-8jw7q   1/1     Running   0          59s   10.244.0.10   lab9-control-plane   <none>           <none>
pod/devops-info-service-6b96c9584-c7g6p   1/1     Running   0          53s   10.244.0.11   lab9-control-plane   <none>           <none>
pod/devops-info-service-6b96c9584-mqpcj   1/1     Running   0          40s   10.244.0.12   lab9-control-plane   <none>           <none>

NAME                          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/devops-info-service   NodePort    10.96.58.156   <none>        80:30080/TCP   16m   app=devops-info-service
service/kubernetes            ClusterIP   10.96.0.1      <none>        443/TCP        40m   <none>

$ sudo ./.tools/bin/kubectl describe deployment devops-info-service
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
```

### Image source fix used

```bash
$ sudo ./.tools/bin/kind load docker-image devops-info-service:lab02 --name lab9
Image: "devops-info-service:lab02" ... loading...

$ sudo ./.tools/bin/kubectl set image deployment/devops-info-service \
  devops-info-service=devops-info-service:lab02
deployment.apps/devops-info-service image updated

$ sudo ./.tools/bin/kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out
```

### App accessibility evidence

```bash
$ sudo ./.tools/bin/kubectl port-forward service/devops-info-service 8080:80
Forwarding from 127.0.0.1:8080 -> 5000

$ curl -s http://127.0.0.1:8080/health
{"status":"healthy","timestamp":"2026-03-26T12:19:31.786Z","uptime_seconds":286}

$ curl -s http://127.0.0.1:8080/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-6b96c9584-8jw7q","platform":"Linux","platform_version":"Debian GNU/Linux 13 (trixie)","architecture":"x86_64","cpu_count":20,"python_version":"3.13.12"},"runtime":{"uptime_seconds":301,"uptime_human":"0 hours, 5 minutes","current_time":"2026-03-26T12:19:47.085Z","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.19.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}
```

---

## 4. Operations Performed

### Deploy

```bash
$ sudo ./.tools/bin/kubectl apply -f k8s/deployment.yml
deployment.apps/devops-info-service configured

$ sudo ./.tools/bin/kubectl apply -f k8s/service.yml
service/devops-info-service unchanged

$ sudo ./.tools/bin/kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out
```

### Scale to 5 replicas

```bash
$ sudo ./.tools/bin/kubectl scale deployment/devops-info-service --replicas=5
deployment.apps/devops-info-service scaled

$ sudo ./.tools/bin/kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out

$ sudo ./.tools/bin/kubectl get pods -l app=devops-info-service
NAME                                  READY   STATUS    RESTARTS   AGE
devops-info-service-6b96c9584-8jw7q   1/1     Running   0          8m58s
devops-info-service-6b96c9584-c7g6p   1/1     Running   0          8m52s
devops-info-service-6b96c9584-mjbrc   1/1     Running   0          23s
devops-info-service-6b96c9584-mqpcj   1/1     Running   0          8m39s
devops-info-service-6b96c9584-qwncg   1/1     Running   0          23s
```

### Rolling update

```bash
$ sudo ./.tools/bin/kind load docker-image devops-info-service:lab02 --name lab9
Image: "devops-info-service:lab02" ... loading...

$ sudo ./.tools/bin/kubectl set image deployment/devops-info-service \
  devops-info-service=devops-info-service:lab02
deployment.apps/devops-info-service image updated

$ sudo ./.tools/bin/kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out

$ sudo ./.tools/bin/kubectl rollout history deployment/devops-info-service
deployment.apps/devops-info-service
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
```

### Rollback

```bash
$ sudo ./.tools/bin/kubectl rollout undo deployment/devops-info-service
deployment.apps/devops-info-service rolled back

$ sudo ./.tools/bin/kubectl rollout status deployment/devops-info-service
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out

$ sudo ./.tools/bin/kubectl rollout history deployment/devops-info-service
deployment.apps/devops-info-service
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
```

### Service access and verification

```bash
$ sudo ./.tools/bin/kubectl get svc devops-info-service
NAME                  TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
devops-info-service   NodePort   10.96.58.156   <none>        80:30080/TCP   16m

$ sudo ./.tools/bin/kubectl get endpoints devops-info-service
NAME                  ENDPOINTS                                             AGE
devops-info-service   10.244.0.10:5000,10.244.0.11:5000,10.244.0.12:5000   16m

$ curl -s http://127.0.0.1:8080/health
{"status":"healthy","timestamp":"2026-03-26T12:19:31.786Z","uptime_seconds":286}
```

---

## 5. Production Considerations

### Health checks rationale

- `startupProbe` protects slow starts.
- `readinessProbe` gates traffic only to ready Pods.
- `livenessProbe` restarts unhealthy containers automatically.

### Resource limits rationale

- Requests reserve scheduler minimums.
- Limits prevent noisy-neighbor issues.

### Production improvements

- Add HPA and PodDisruptionBudget.
- Add ConfigMap/Secret separation.
- Add NetworkPolicy.
- Pin image digests.
- Add dedicated readiness checks for dependencies.

### Monitoring and observability strategy

- Prometheus scrapes `/metrics`.
- Grafana dashboards for latency, errors, throughput, and saturation.
- Loki/Promtail for centralized logs.
- Alerting for restart spikes, probe failures, and elevated 5xx.

---

## 6. Challenges and Learnings

### Challenge 1: probe tuning

- Initial values were adjusted so startup/readiness remain stable during pod restarts.

### Challenge 2: ingress path routing

- Regex-based rewrite was used to preserve correct backend paths (`/app1`, `/app2`).

### What was learned

- Kubernetes controllers continuously reconcile desired state.
- Deployments + probes + resources provide a solid production baseline.
- Rollout/rollback workflows are fast and safe when manifests are declarative.

---
