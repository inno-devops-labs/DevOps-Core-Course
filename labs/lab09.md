# Lab 9 — Kubernetes Fundamentals

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Kubernetes-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Kubernetes%201.36-informational)

> Stand up a local Kubernetes cluster and deploy **two** services side by side: your own Python app from Lab 2 and a course-provided Go `echo` service. Wire them together with `Service` + kube-DNS and prove they can talk to each other.

## Overview

Through Lab 8 you ran a **single** service with `docker compose up`. That worked — so why bother with Kubernetes? Because the moment you have **more than one** service, you need self-healing, stable network identity, and service discovery that you no longer want to wire by hand.

Lab 9 is where that becomes concrete. You will run **two pods**:

- **`web`** — your containerized Python service from Lab 2 (you build & deploy this)
- **`echo`** — a tiny Go companion service shipped by the course as plumbing (you only deploy it)

The payoff task is **cross-service networking**: from inside the `web` pod you will `curl http://echo:80/ping` and get back `pong`. That single round-trip exercises `Service`, label selectors, and kube-DNS all at once — the whole point of the K8s networking model, which never made sense with only one service.

**What You'll Learn:**
- Kubernetes core concepts and the control-plane / worker-node architecture
- Writing production-ready `Deployment` and `Service` manifests by hand
- Label/selector binding — the glue between every K8s resource
- Service discovery via kube-DNS and inter-pod networking
- Health checks (liveness / readiness probes), resource requests/limits, scaling and rolling updates

**Tech Stack:** Kubernetes **1.36 "Haru"** | kubectl 1.36 | **k3d 5.7+** (k3s-in-Docker) | plain YAML manifests

> 📚 This lab pairs with **Lecture 9 — Kubernetes Fundamentals**. Re-read slides 7–11 (Pod, Deployment, Service, kube-DNS, labels) before you start.

---

## Tasks

Main tasks total **10 pts**. The bonus adds **2 pts**.

### Task 1 — Local Kubernetes Setup (2 pts)

**Objective:** Set up a local multi-node Kubernetes cluster running version 1.36 with **k3d** and confirm it is healthy.

**Requirements:**

1. **Install tools**
   - Install `kubectl` (pin **v1.36** to match the cluster)
   - Install **k3d (5.7+)** — it runs k3s (lightweight, CNCF-certified Kubernetes) inside Docker containers. Requires Docker.

2. **Create a 1.36 cluster**
   - One server + two agents, with the loadbalancer ports mapped to your host (you'll need them for the Ingress bonus).

3. **Verify the cluster**
   - Run `kubectl version`, `kubectl cluster-info`, and `kubectl get nodes -o wide`
   - Confirm the server version reports `v1.36.x` and you see **3 nodes** (1 server + 2 agents)

<details>
<summary>💡 Cluster Bring-Up Commands</summary>

```bash
k3d cluster create devops \
  --image rancher/k3s:v1.36.1-k3s1 \
  --agents 2 \
  -p "8080:80@loadbalancer" \
  -p "8443:443@loadbalancer"
# k3d sets your kube-context to k3d-devops automatically
kubectl config use-context k3d-devops
```

> k3s image tags append `-k3s1` to the Kubernetes version (e.g. `v1.36.1-k3s1`). Use the newest `v1.36.x-k3s1` tag on the `rancher/k3s` repo.

**Sanity checks (output below is illustrative):**
```bash
kubectl get nodes -o wide
# NAME                 STATUS   ROLES                  AGE   VERSION
# k3d-devops-server-0  Ready    control-plane,master   30s   v1.36.1+k3s1  ...
# k3d-devops-agent-0   Ready    <none>                 25s   v1.36.1+k3s1  ...
# k3d-devops-agent-1   Ready    <none>                 25s   v1.36.1+k3s1  ...
```

Tear it down any time with `k3d cluster delete devops`.

</details>

<details>
<summary>💡 Why k3d?</summary>

k3d wraps **k3s** (Rancher's lightweight Kubernetes) in Docker containers. You get:
- **Fast, throwaway clusters** — create or delete in seconds
- **Free multi-node** — `--agents N` adds worker containers, so you can watch pods schedule across nodes
- **Batteries included** — a built-in **Traefik** ingress controller and **klipper** LoadBalancer, so `type: LoadBalancer` and `Ingress` work with no extra install (you'll use both in the bonus)

Do **not** use Docker Desktop's bundled Kubernetes — it lags upstream.

</details>

**Documentation required:**
- Output of `kubectl version` and `kubectl get nodes -o wide` (server version must be 1.36.x, 3 nodes total)

---

### Task 2 — Deploy Your Web Service (3 pts)

**Objective:** Deploy your Lab 2 Python image as a `Deployment` fronted by a `Service`. You write the YAML — that is the skill being assessed.

**Requirements:**

1. **`k8s/web-deployment.yaml`** — a `Deployment` named `web` that:
   - Uses **your own** Lab 2 image (the one you pushed to Docker Hub / GHCR in Lab 2)
   - Runs **3 replicas**
   - Carries the label `app: web` (on the Deployment, the selector, and the pod template — they must match)
   - Declares resource **requests and limits** for CPU and memory
   - Wires a **liveness** probe and a **readiness** probe to your app's `/health` endpoint (added back in Lab 1)

2. **`k8s/web-service.yaml`** — a `Service` named `web` that:
   - Selects `app: web`
   - Is type `NodePort` so you can reach it from your laptop
   - Maps service `port: 80` → your container's `targetPort`

3. **Apply and verify** the Deployment reaches 3/3 ready and the Service has endpoints.

**Skeletons — fill in every `YOUR-TASK` marker yourself:**

```yaml
# k8s/web-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  labels:
    app: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: YOUR-TASK      # your Lab 2 image, e.g. docker.io/<you>/devops-info:v1
          ports:
            - containerPort: YOUR-TASK   # the port your app listens on
          resources:
            requests:
              cpu: YOUR-TASK
              memory: YOUR-TASK
            limits:
              cpu: YOUR-TASK
              memory: YOUR-TASK
          livenessProbe:
            httpGet:
              path: YOUR-TASK    # /health
              port: YOUR-TASK
            initialDelaySeconds: YOUR-TASK
            periodSeconds: YOUR-TASK
          readinessProbe:
            httpGet:
              path: YOUR-TASK
              port: YOUR-TASK
            periodSeconds: YOUR-TASK
```

```yaml
# k8s/web-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: NodePort
  selector:
    app: YOUR-TASK     # must match the Deployment's pod labels
  ports:
    - port: 80
      targetPort: YOUR-TASK   # your container's port
```

<details>
<summary>💡 Apply, Inspect, Reach It</summary>

# If your Lab 2 image is pushed to a public registry (Docker Hub / GHCR), k3d pulls it
# normally. If you only built it locally, import it into the cluster's containerd first:
```bash
k3d image import <your-image>:tag --cluster devops   # only needed for locally-built images
```

```bash
kubectl apply -f k8s/web-deployment.yaml
kubectl apply -f k8s/web-service.yaml

kubectl get deploy web
kubectl get pods -l app=web
kubectl get svc web
kubectl get endpoints web        # should list 3 pod IPs once readiness passes
```

Reach the service from your laptop with `port-forward` (works for any Service type):
```bash
kubectl port-forward svc/web 8080:80
curl -s localhost:8080/health
```

</details>

<details>
<summary>💡 Probes & Resources — Rules of Thumb</summary>

- **Liveness** = "should I be killed and restarted?" Point it at a cheap, in-process signal like `/health`, not a heavy endpoint.
- **Readiness** = "should traffic come to me yet?" If it fails, the pod is pulled out of the Service rotation without a restart.
- Always set **requests** (the scheduler reserves them). Set a **memory limit** (OOMKill protection). CPU is throttled, not killed, past its limit.

```yaml
resources:
  requests: {cpu: 100m, memory: 64Mi}
  limits:   {cpu: 500m, memory: 256Mi}
```

</details>

**Documentation required:**
- `kubectl get deploy,pods,svc -l app=web` output (illustrative or real — label real cluster output as such)
- A note explaining your replica count, resource values, and probe choices

---

### Task 3 — Deploy the `echo` Service (2 pts)

**Objective:** Add the course-provided **second** service. This is what makes `Service` + kube-DNS meaningful.

`echo` is a tiny Go HTTP service maintained by the course as plumbing in `plumbing/echo/` — **you do not build or modify it.** A pre-built image is published by the course CI. It listens on **port 8081** and exposes:

| Path | Behaviour |
|------|-----------|
| `GET /ping` | Returns `pong` — minimal smoke test |
| `* /echo` | JSON with body, headers, hostname, version, uptime, and a request counter (useful for spotting load balancing across replicas) |
| `GET /healthz` | Returns `ok` (200) — wire into probes |
| `GET /metrics` | Prometheus text format |

**Requirements:**

1. **`k8s/echo-deployment.yaml`** — a `Deployment` named `echo` that:
   - Uses the provided image **`ghcr.io/inno-devops-labs/echo:v1`** (do not build your own)
   - Runs **2 replicas** (so the Service has something to load-balance)
   - Carries the label `app: echo`
   - Wires liveness/readiness probes to `/healthz` on port `8081`

2. **`k8s/echo-service.yaml`** — a `Service` named `echo` that:
   - Selects `app: echo`
   - Is type `ClusterIP` (internal only — no external access needed)
   - Maps service `port: 80` → `targetPort: 8081`

**Skeletons — fill in every `YOUR-TASK` marker:**

```yaml
# k8s/echo-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echo
  labels:
    app: echo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: echo
  template:
    metadata:
      labels:
        app: echo
    spec:
      containers:
        - name: echo
          image: ghcr.io/inno-devops-labs/echo:v1   # provided — do not change
          ports:
            - containerPort: 8081
          readinessProbe:
            httpGet:
              path: YOUR-TASK    # /healthz
              port: 8081
            periodSeconds: YOUR-TASK
          livenessProbe:
            httpGet:
              path: YOUR-TASK
              port: 8081
            initialDelaySeconds: YOUR-TASK
            periodSeconds: YOUR-TASK
```

```yaml
# k8s/echo-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: echo
spec:
  type: ClusterIP
  selector:
    app: YOUR-TASK     # must match the echo pod labels
  ports:
    - port: 80
      targetPort: YOUR-TASK   # echo listens on 8081
```

<details>
<summary>💡 Apply & Verify echo Is Up</summary>

```bash
kubectl apply -f k8s/echo-deployment.yaml
kubectl apply -f k8s/echo-service.yaml

kubectl get pods -l app=echo       # expect 2 pods Running/Ready
kubectl get svc echo
kubectl get endpoints echo         # expect 2 pod IPs
```

Quick smoke test through a port-forward (output illustrative):
```bash
kubectl port-forward svc/echo 8088:80
curl -s localhost:8088/ping
# pong
```

</details>

**Documentation required:**
- `kubectl get pods,svc,endpoints -l app=echo` output
- Confirmation that 2 `echo` pods are Ready and the Service has 2 endpoints

---

### Task 4 — Cross-Service Networking, Scaling & Updates (2 pts)

**Objective:** Prove the two services can discover and reach each other through kube-DNS, then exercise scaling and rolling updates. **This is the pedagogical core of the lab.**

**Requirements:**

1. **Cross-service call (the key deliverable).** From **inside a `web` pod**, call the `echo` Service by its DNS name and capture `pong`:
   ```bash
   WEB_POD=$(kubectl get pod -l app=web -o jsonpath='{.items[0].metadata.name}')
   kubectl exec "$WEB_POD" -- curl -s http://echo:80/ping
   # expected: pong
   ```
   This works only because `echo` resolves via kube-DNS (`echo.default.svc.cluster.local`), the Service load-balances to a healthy `echo` pod, and the label selector binds them. Capture this output — it is the proof the networking model works.

2. **Observe load balancing.** Hit `/echo` a few times and watch the `hostname` field change across the 2 backing pods:
   ```bash
   kubectl exec "$WEB_POD" -- sh -c 'for i in 1 2 3 4; do curl -s http://echo:80/echo -d hi; echo; done'
   ```

3. **Scale** the `web` Deployment to **5 replicas** and confirm all become Ready.

4. **Rolling update.** Change the `web` image tag (or a label/env) and re-apply; watch the rollout proceed with zero downtime, then view rollout history.

5. **Rollback** to the previous revision and confirm.

<details>
<summary>💡 If <code>curl</code> Is Missing in Your Image</summary>

Your slim Python image may not ship `curl`. Options:
- Add `curl` (or use `wget -qO-`) in your Lab 2 image, **or**
- Run a throwaway client pod in the cluster:
  ```bash
  kubectl run tmp --rm -it --image=curlimages/curl:8.11.0 --restart=Never -- \
    curl -s http://echo:80/ping
  ```
Either way, the call must go **pod → Service DNS name → echo**, not a port-forward from your laptop.

</details>

<details>
<summary>💡 Scaling, Rollout & Rollback Commands</summary>

```bash
# Scale (declarative: edit replicas in the manifest and re-apply, or imperative:)
kubectl scale deployment/web --replicas=5
kubectl get pods -l app=web -w

# Rolling update
kubectl set image deployment/web web=docker.io/<you>/devops-info:v2
kubectl rollout status deployment/web
kubectl rollout history deployment/web

# Rollback
kubectl rollout undo deployment/web
kubectl rollout status deployment/web
```

A `RollingUpdate` strategy with `maxUnavailable: 0` guarantees zero downtime during the update.

</details>

**Documentation required:**
- The `kubectl exec ... curl http://echo:80/ping` command **and its `pong` output** (this is the headline evidence)
- `/echo` output showing the hostname rotating across echo pods (load balancing)
- Scaling to 5 replicas, rollout status, and rollback evidence (illustrative or real, labelled)

---

### Task 5 — Documentation (1 pt)

**Objective:** Capture what you built in `k8s/README.md`.

Create `k8s/README.md` with these sections:

1. **Architecture** — a short description or diagram: the `web` Deployment (3 pods) behind a NodePort Service, the `echo` Deployment (2 pods) behind a ClusterIP Service, and the `web → echo` call path through kube-DNS.
2. **Manifests** — one line per file (`web-deployment.yaml`, `web-service.yaml`, `echo-deployment.yaml`, `echo-service.yaml`) and the key choices you made (replicas, resources, probe paths, Service types).
3. **Cross-service evidence** — the `curl http://echo:80/ping` → `pong` output and a sentence explaining *why* the DNS name resolves.
4. **Operations** — the commands used to deploy, scale, roll out, and roll back.
5. **Challenges & learnings** — what broke, how you debugged it (`kubectl describe`, `kubectl logs`, `kubectl get events`), and what clicked about the K8s networking model.

---

## Bonus Task — Ingress with TLS (2 pts)

**Objective:** Put an L7 HTTP router in front of both services and terminate TLS.

You already have two Services (`web` and `echo`). Route to them through a single Ingress over HTTPS.

**Requirements:**

1. **Ingress controller** — none to install. k3d ships **Traefik** built in, already reachable on the `8080`/`8443` host ports you mapped at `k3d cluster create`. Confirm it's running: `kubectl get pods -n kube-system | grep traefik`.

2. **Self-signed TLS cert + Secret** covering the two hostnames you'll route (the `*.localhost` TLD resolves to 127.0.0.1 automatically — no `/etc/hosts` edits needed):
   ```bash
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout tls.key -out tls.crt \
     -subj "/CN=web.localhost" -addext "subjectAltName=DNS:web.localhost,DNS:echo.localhost"
   kubectl create secret tls apps-tls --key tls.key --cert tls.crt
   ```

3. **`k8s/ingress.yaml`** — host-based routing over TLS through Traefik:
   - `web.localhost` → `web` Service
   - `echo.localhost` → `echo` Service
   - `ingressClassName: traefik` and a `tls:` block referencing the `apps-tls` Secret

4. **Verify** over the mapped HTTPS port: `curl -k https://echo.localhost:8443/ping` → `pong`.

<details>
<summary>💡 Ingress Skeleton</summary>

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: apps-ingress
spec:
  ingressClassName: traefik        # k3d's built-in controller
  tls:
    - hosts: [web.localhost, echo.localhost]
      secretName: apps-tls
  rules:
    - host: web.localhost
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port: {number: 80}
    - host: echo.localhost
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: echo
                port: {number: 80}
```

Host-based routing (one Service per hostname) avoids path-rewrite middleware, so the request path reaches each backend unchanged — `https://echo.localhost:8443/ping` hits echo's `/ping`.

```bash
curl -k https://echo.localhost:8443/ping   # -> pong (through Traefik + TLS)
curl -k https://web.localhost:8443/health  # -> your app's health response
```

> ⚠️ k3d's bundled controller is **Traefik**, not ingress-nginx — that's why there's no controller to install and why we use `ingressClassName: traefik`. The **Gateway API** is the future of K8s traffic management; you'll meet it later in the program.

</details>

**Documentation required:**
- `kubectl get pods -n kube-system | grep traefik` showing the controller Running
- `k8s/ingress.yaml` with TLS + host-based routing through Traefik
- `curl -k https://devops.local/...` output for both routes
- One or two sentences on what Ingress buys you over a raw NodePort Service

---

## How to Submit

1. **Create a branch:**
   ```bash
   git checkout -b lab09
   ```

2. **Commit your manifests and docs:**
   ```bash
   git add k8s/
   git commit -m "feat: deploy web + echo services to kubernetes (lab09)"
   git push -u origin lab09
   ```

3. **Open Pull Requests:**
   - **PR #1:** `your-fork:lab09` → `course-repo:master`
   - **PR #2:** `your-fork:lab09` → `your-fork:master`

4. **Verify** all four manifests, `k8s/README.md`, and your evidence are present.

---

## Acceptance Criteria

### Task 1 — Local Kubernetes Setup (2 pts)
- [ ] `kubectl` and `k3d` installed; `k3d cluster create` ran with the loadbalancer port maps
- [ ] Cluster running on **Kubernetes 1.36** (server version verified)
- [ ] `kubectl get nodes -o wide` output captured
- [ ] Chosen tool justified (1–2 sentences)

### Task 2 — Deploy Your Web Service (3 pts)
- [ ] `k8s/web-deployment.yaml` written, using your **Lab 2** image
- [ ] 3 replicas, matching `app: web` labels/selector
- [ ] Resource requests **and** limits set
- [ ] Liveness **and** readiness probes wired to `/health`
- [ ] `k8s/web-service.yaml` — NodePort, selects `app: web`, port 80 → container port
- [ ] Deployment reports 3/3 ready and the Service has 3 endpoints

### Task 3 — Deploy the echo Service (2 pts)
- [ ] `k8s/echo-deployment.yaml` uses provided `ghcr.io/inno-devops-labs/echo:v1` (not self-built)
- [ ] 2 replicas, `app: echo` labels, probes on `/healthz:8081`
- [ ] `k8s/echo-service.yaml` — ClusterIP, port 80 → targetPort 8081
- [ ] 2 echo pods Ready, Service has 2 endpoints

### Task 4 — Cross-Service Networking, Scaling & Updates (2 pts)
- [ ] **`kubectl exec` into web pod + `curl http://echo:80/ping` returns `pong`** (headline evidence)
- [ ] `/echo` output shows hostname rotating across echo pods (load balancing)
- [ ] `web` scaled to 5 replicas, all Ready
- [ ] Rolling update performed; zero downtime; history shown
- [ ] Rollback demonstrated

### Task 5 — Documentation (1 pt)
- [ ] `k8s/README.md` covers architecture, manifests, cross-service evidence, operations, and challenges

### Bonus — Ingress with TLS (2 pts)
- [ ] Ingress controller enabled and Running
- [ ] Self-signed TLS Secret created
- [ ] `k8s/ingress.yaml` routes `/` → web and `/echo` → echo over HTTPS
- [ ] `curl -k https://devops.local/...` works for both routes

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Setup** | 2 pts | K8s 1.36 cluster running, tools installed and verified |
| **Web service** | 3 pts | Hand-written Deployment + Service, probes, resources, 3/3 ready |
| **echo service** | 2 pts | Provided image deployed as 2nd Deployment + ClusterIP Service |
| **Cross-service + ops** | 2 pts | `web → echo` `pong` proven; scaling, rolling update, rollback |
| **Documentation** | 1 pt | `k8s/README.md` complete and accurate |
| **Bonus** | 2 pts | Ingress with TLS routing to both services |
| **Total** | 12 pts | 10 pts required + 2 pts bonus |

**Grading:**
- **10/10:** Both services deployed, cross-service `pong` proven, clean manifests and docs, deep understanding
- **8–9/10:** Both services run and talk; minor gaps in probes/resources or docs
- **6–7/10:** Web service works but the 2nd service or cross-service call is incomplete
- **<6/10:** Missing the echo service, no working cross-service call, or no probes/resources

---

## Resources

<details>
<summary>📚 Official Kubernetes Documentation</summary>

- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [Kubernetes 1.36 release notes](https://kubernetes.io/blog/2026/04/22/kubernetes-v1-36-release/)
- [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Services & kube-DNS](https://kubernetes.io/docs/concepts/services-networking/service/)
- [DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [Liveness, Readiness & Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/quick-reference/)

</details>

<details>
<summary>🛠️ Tools</summary>

- [kubectl](https://kubernetes.io/docs/tasks/tools/) — Kubernetes CLI
- [k3d](https://k3d.io/) — k3s in Docker (local Kubernetes)
- [k3s](https://docs.k3s.io/) — the lightweight Kubernetes k3d runs
- [k9s](https://k9scli.io/) — terminal UI for Kubernetes
- [kubectx/kubens](https://github.com/ahmetb/kubectx) — context & namespace switcher

</details>

<details>
<summary>🔍 Debugging</summary>

- [Debug Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/)
- [Debug Services](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/)
- [Troubleshooting Applications](https://kubernetes.io/docs/tasks/debug/debug-application/)

</details>

<details>
<summary>🌐 Ingress (Bonus)</summary>

- [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [k3d Ingress & exposing services](https://k3d.io/stable/usage/exposing_services/)
- [Gateway API](https://gateway-api.sigs.k8s.io/) — next-generation traffic management

</details>

---

## Looking Ahead

- **Lab 10:** Package these manifests as a **Helm 4** chart (echo becomes a subchart)
- **Lab 11:** Secrets management with OpenBao / Vault
- **Lab 12:** ConfigMaps and application configuration
- **Lab 13:** ArgoCD GitOps — `web` + `echo` via an ApplicationSet
- **Lab 14:** Progressive delivery — Argo Rollouts canary on `echo`
- **Lab 15:** StatefulSets for stateful workloads
- **Lab 16:** Kubernetes monitoring & observability (scrape `echo`'s `/metrics`)

---

**Good luck!** 🚢

> **Remember:** Kubernetes is declarative — define desired state and let the control plane reconcile. The whole networking model only clicks once you have a **second** service to talk to. That `pong` from `echo` is the moment it all comes together.
