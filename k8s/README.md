# Lab 9 — Kubernetes (report)

## 1. Architecture overview

- **Workloads:** `devops-info-service` Deployment: **3** Pods (FastAPI :5000). Bonus: `app2-nginx` Deployment: **1** Pod (nginx :80).
- **Networking:** Service `devops-info-service` **NodePort** (80 → container 5000). Bonus: Ingress `apps-ingress`, host `local.lab09.local`, TLS Secret `tls-secret`; path rewrite so `/app1/health` reaches `/health`.
- **Resources / strategy:** As in `deployment.yml` and `kubectl describe deployment` below (`RollingUpdate`, `0 max unavailable`, `1 max surge`).

```text
Client → NodePort or Ingress → Service → Pods
```

---

## 2. Manifest files

| File | Role |
|------|------|
| `deployment.yml` | 3 replicas, probes `/health`, resources, RollingUpdate |
| `service.yml` | NodePort, selector `app: devops-info-service` |
| `kustomization.yaml` | Image `mclavrushka/devops-info-service:latest` |
| `app2.yml`, `ingress.yml` | Bonus: nginx + Ingress + TLS |
| `app_python/scripts/build-push-multiarch.sh` | Multi-arch image for Docker Hub |

Non-root: **`app_python/Dockerfile`** (`USER appuser`).

---

## 3. Deployment evidence

### 3.1 Verbatim terminal output (from saved log)

**Ingress addon (CLI reported timeout; controller still came up — see next command)**

```text
minikube addons enable ingress
❌  Exiting due to MK_ADDON_ENABLE: enable failed: ... context deadline exceeded
```

**Ingress controller namespace**

```text
kubectl get pods -n ingress-nginx -o wide
NAME                                        READY   STATUS      RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
ingress-nginx-admission-create-24nzr        0/1     Completed   0          36m   10.244.0.14   minikube   <none>           <none>
ingress-nginx-admission-patch-tkjbh         0/1     Completed   1          36m   10.244.0.15   minikube   <none>           <none>
ingress-nginx-controller-596f8778bc-flqcv   1/1     Running     0          36m   10.244.0.16   minikube   <none>           <none>
```

**TLS + bonus manifests**

```text
./k8s/scripts/gen-tls.sh local.lab09.local
kubectl apply -f k8s/app2.yml -f k8s/ingress.yml
secret/tls-secret created
Secret tls-secret applied in namespace 'default' for host local.lab09.local
configmap/app2-html created
deployment.apps/app2-nginx created
service/app2-service created
ingress.networking.k8s.io/apps-ingress created
```

**`minikube tunnel` (sudo for 80/443; session stopped)**

```text
minikube tunnel
❗  The service/ingress apps-ingress requires privileged ports to be exposed: [80 443]
🔑  sudo permission will be asked for it.
...
✋  Stopped tunnel for service apps-ingress.
```

**Hosts**

```text
echo '127.0.0.1  local.lab09.local' | sudo tee -a /etc/hosts
127.0.0.1  local.lab09.local
```

**HTTPS before Ingress regex fix** (two curls in one line; first response is root JSON because path was rewritten to `/`; then HTML from app2)

```text
curl -k https://local.lab09.local/app1/health
curl -k https://local.lab09.local/app2/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-6f8f65789f-m8n6p","platform":"Linux","platform_version":"#1 SMP Thu Mar 20 16:32:56 UTC 2025","architecture":"aarch64","cpu_count":4,"python_version":"3.13.12"},"runtime":{"uptime_seconds":4814,"uptime_human":"1 hours, 20 minutes","current_time":"2026-03-25T14:18:10.581091+00:00","timezone":"UTC"},"request":{"client_ip":"10.244.0.16","user_agent":"curl/8.7.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><title>App 2</title></head>
<body><h1>Второе приложение (Lab 9 bonus)</h1><p>nginx + ConfigMap</p></body>
</html>
```

**After `kubectl apply -f k8s/ingress.yml` (rewrite fix)**

```text
kubectl apply -f k8s/ingress.yml
ingress.networking.k8s.io/apps-ingress configured

curl -k -s https://local.lab09.local/app1/health | head -c 300
{"status":"healthy","timestamp":"2026-03-25T14:21:05.644188+00:00","uptime_seconds":4997}
```

**Deployment status**

```text
kubectl get deployment devops-info-service
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
devops-info-service   3/3     3            3           102m
```

**`kubectl get all` (default namespace)**

```text
kubectl get all
NAME                                       READY   STATUS    RESTARTS   AGE
pod/app2-nginx-788f88c48f-zvgtm            1/1     Running   0          13m
pod/devops-info-service-6f8f65789f-m8n6p   1/1     Running   0          90m
pod/devops-info-service-6f8f65789f-nljww   1/1     Running   0          90m
pod/devops-info-service-6f8f65789f-x92vj   1/1     Running   0          90m

NAME                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/app2-service          ClusterIP   10.110.48.143    <none>        80/TCP         13m
service/devops-info-service   NodePort    10.102.209.180   <none>        80:32601/TCP   104m
service/kubernetes            ClusterIP   10.96.0.1        <none>        443/TCP        5h18m

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/app2-nginx            1/1     1            1           13m
deployment.apps/devops-info-service   3/3     3            3           104m

NAME                                             DESIRED   CURRENT   READY   AGE
replicaset.apps/app2-nginx-788f88c48f            1         1         1       13m
replicaset.apps/devops-info-service-6f8f65789f   3         3         3       104m
replicaset.apps/devops-info-service-7987f6bcc7   0         0         0       92m
```

**`kubectl get pods`**

```text
kubectl get pods
NAME                                   READY   STATUS    RESTARTS   AGE
app2-nginx-788f88c48f-zvgtm            1/1     Running   0          13m
devops-info-service-6f8f65789f-m8n6p   1/1     Running   0          91m
devops-info-service-6f8f65789f-nljww   1/1     Running   0          90m
devops-info-service-6f8f65789f-x92vj   1/1     Running   0          91m
```

**`kubectl get svc`**

```text
kubectl get svc
NAME                  TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
app2-service          ClusterIP   10.110.48.143    <none>        80/TCP         13m
devops-info-service   NodePort    10.102.209.180   <none>        80:32601/TCP   105m
kubernetes            ClusterIP   10.96.0.1        <none>        443/TCP        5h19m
```

**`kubectl describe deployment` — `devops-info-service` (excerpt: replicas and strategy)**

```text
Name:                   devops-info-service
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
...
   devops-info-service:
    Image:      mclavrushka/devops-info-service:latest
...
    Liveness:   http-get http://:http/health delay=10s timeout=3s period=10s #success=1 #failure=3
    Readiness:  http-get http://:http/health delay=5s timeout=2s period=5s #success=1 #failure=3
```

(Full `kubectl describe deployment` in the log also includes `app2-nginx`.)

---

### 3.2 Task 1 — cluster, redeploy, Task 4 — scale / rollout / Service (verbatim)

**Why minikube:** Local single-node cluster on macOS with the Docker driver; matches course docs (`minikube service`, `minikube addons enable ingress`). No separate cloud account required.

**`kubectl cluster-info`**

```text
Kubernetes control plane is running at https://127.0.0.1:54698
CoreDNS is running at https://127.0.0.1:54698/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```

**`kubectl get nodes`**

```text
NAME       STATUS   ROLES           AGE     VERSION
minikube   Ready    control-plane   5h27m   v1.35.1
```

**`kubectl apply -k k8s/`** (idempotent apply)

```text
service/devops-info-service unchanged
deployment.apps/devops-info-service unchanged
```

**Scale to 5 replicas**

```text
kubectl scale deployment/devops-info-service --replicas=5
deployment.apps/devops-info-service scaled
```

**`kubectl get pods -l app=devops-info-service`**

```text
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-6f8f65789f-2m4x7   1/1     Running   0          8s
devops-info-service-6f8f65789f-m8n6p   1/1     Running   0          100m
devops-info-service-6f8f65789f-nljww   1/1     Running   0          100m
devops-info-service-6f8f65789f-thrkf   1/1     Running   0          8s
devops-info-service-6f8f65789f-x92vj   1/1     Running   0          100m
```

**`kubectl rollout status deployment/devops-info-service`**

```text
deployment "devops-info-service" successfully rolled out
```

**`kubectl rollout history deployment/devops-info-service`** (before undo)

```text
deployment.apps/devops-info-service 
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
```

**`kubectl rollout undo deployment/devops-info-service`**

```text
deployment.apps/devops-info-service rolled back
```

**`kubectl rollout history`** (no resource name — expected error)

```text
error: required resource not specified
```

**`kubectl rollout history deployment/devops-info-service`** (after undo)

```text
deployment.apps/devops-info-service 
REVISION  CHANGE-CAUSE
3         <none>
4         <none>
```

**Scale back to 3 replicas**

```text
kubectl scale deployment/devops-info-service --replicas=3
deployment.apps/devops-info-service scaled
```

**`kubectl get all -l app=devops-info-service`** (transient mix of ReplicaSets during rollout)

```text
NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-6f8f65789f-m8n6p   1/1     Running   0          100m
pod/devops-info-service-7987f6bcc7-gbgjc   0/1     Running   0          6s
pod/devops-info-service-7987f6bcc7-ls8rn   1/1     Running   0          23s
pod/devops-info-service-7987f6bcc7-ns5vp   1/1     Running   0          16s

NAME                          TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort   10.102.209.180   <none>        80:32601/TCP   114m

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service   3/3     3            3           114m

NAME                                             DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-6f8f65789f   1         1         1       114m
replicaset.apps/devops-info-service-7987f6bcc7   3         3         2       102m
```

**`kubectl get pods,svc -l app=devops-info-service -o wide`** (steady — three Pods on rolled-back RS)

```text
NAME                                       READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
pod/devops-info-service-7987f6bcc7-gbgjc   1/1     Running   0          11s   10.244.0.23   minikube   <none>           <none>
pod/devops-info-service-7987f6bcc7-ls8rn   1/1     Running   0          28s   10.244.0.20   minikube   <none>           <none>
pod/devops-info-service-7987f6bcc7-ns5vp   1/1     Running   0          21s   10.244.0.21   minikube   <none>           <none>

NAME                          TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE    SELECTOR
service/devops-info-service   NodePort   10.102.209.180   <none>        80:32601/TCP   115m   app=devops-info-service
```

**`kubectl describe svc devops-info-service`**

```text
Name:                     devops-info-service
Namespace:                default
Selector:                 app=devops-info-service
Type:                     NodePort
IP:                       10.102.209.180
Port:                     http  80/TCP
TargetPort:               http/TCP
NodePort:                 http  32601/TCP
Endpoints:                10.244.0.20:5000,10.244.0.21:5000,10.244.0.23:5000
```

**`kubectl get endpoints devops-info-service`**

```text
Warning: v1 Endpoints is deprecated in v1.33+; use discovery.k8s.io/v1 EndpointSlice
NAME                  ENDPOINTS                                            AGE
devops-info-service   10.244.0.20:5000,10.244.0.21:5000,10.244.0.23:5000   115m
```

**`minikube service devops-info-service --url`**

```text
http://127.0.0.1:52883
❗  Because you are using a Docker driver on darwin, the terminal needs to be open to run it.
```

---

## 4. Operations performed

Covered in §3: `kubectl apply -k k8s/`, scale to 5 / rollout status / history / undo / scale to 3, Service and Endpoints checks, NodePort URL, plus §3.1 (Ingress, TLS, curl, `get all` / `get pods` / `get svc`, `describe deployment`).

---

## 5. Production considerations

- Probes on `/health`; resource requests/limits set; improve with Namespace, PDB, HPA, cert-manager, Vault, NetworkPolicies.
- Observability: `GET /metrics` for Prometheus.

---

## 6. Challenges and solutions

| Issue | What we did |
|-------|-------------|
| ARM Mac vs single-arch image on Hub | Multi-arch push (`build-push-multiarch.sh`). |
| `minikube addons enable ingress` timeout | Controller image pulled slowly; `ingress-nginx-controller` reached **Running** anyway. |
| `minikube tunnel` / sudo | Privileged ports 80/443; use sudo or port-forward / NodePort on high ports. |
| Wrong path behind Ingress | Updated `ingress.yml` with regex + `rewrite-target: /$2`. |
| `rollout undo` with one revision | Need ≥2 revisions before undo (patch or new image). |

---

## Bonus — Ingress vs NodePort

Ingress provides L7 routing and TLS on one hostname; NodePort exposes one Service per port. Evidence: §3.1 (`curl -k`, Ingress apply, `tls-secret`).

---

*Image: `mclavrushka/devops-info-service:latest`. Non-root: `app_python/Dockerfile`.*
