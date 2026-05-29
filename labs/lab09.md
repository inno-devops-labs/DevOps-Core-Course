# Lab 9 — Kubernetes Fundamentals on k3d

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Kubernetes-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-Kubernetes%201.36%20%7C%20k3d-informational)

> **Goal:** stand up a local k3d cluster (1 server + 2 agents), deploy **two** services side by side — your Lab 2 Python image and the course's Go `echo` plumbing — and prove they can talk to each other through `Service` + kube-DNS.
> **Deliverable:** a PR from `lab09` adding `k8s/` (Deployment + Service manifests for both services + the bonus Ingress) and `k8s/docs/LAB09.md` with the evidence captures.

---

## Overview

In this lab you will practice:
- Driving a cluster with `kubectl get / describe / logs / exec / apply / rollout`
- **Writing Deployment + Service manifests from the API up** — picking the right `apiVersion/kind`, getting the label/selector triangle right, sizing requests/limits, wiring probes at a cheap endpoint
- Reading the K8s networking model: `Service` virtual IP → kube-DNS short name → endpoints list → pod IPs
- Importing locally-built images into a k3d cluster's containerd
- Scaling, rolling out, and rolling back a `Deployment`

> ⚠️ **Scope:** plain YAML only — Helm comes in Lab 10. No persistent volumes, no secrets, no metrics scraping yet — those come in Labs 11, 12, 16. Don't reach for `kubectl edit` and don't templatize anything; learn the raw API first.

> 🪨 **Pedagogical core.** Through Lab 8 you ran **one** service. With one service, "why a stable IP and DNS name?" is genuinely hard to answer. This lab runs **two**. From inside your `web` pod you will `curl http://echo/ping` and get back `pong` — that single round-trip exercises kube-DNS, label selectors, and Service load-balancing all at once. **If you only take one capture, take that one.**

---

## Project State

**You should have from previous labs:**
- `app_python/` from Lab 1 — Flask/FastAPI service with `/` and `/health`
- A working container image of it from Lab 2 (pushed to GHCR / Docker Hub, **or** built locally and tagged)
- Familiarity with `docker compose up` (Labs 6–8) — you've felt its limits

**This lab adds:**
- `k8s/web-deployment.yaml` — **you write** (Deployment for your Lab 2 image)
- `k8s/web-service.yaml` — **you write** (Service in front of `web`)
- `k8s/echo-deployment.yaml` — **you write** (Deployment for the course's `echo` plumbing)
- `k8s/echo-service.yaml` — **you write** (ClusterIP Service for `echo`)
- `k8s/ingress.yaml` — **you write** (Traefik Ingress, bonus only)
- `k8s/docs/LAB09.md` — your submission report

By Lab 10 you re-package all of these as a single **Helm 4** chart; by Lab 13 ArgoCD deploys them via an `ApplicationSet`. So get the labels/selectors right *now* — they propagate everywhere.

Course-repo plumbing for this lab:
- `plumbing/echo/` — the Go HTTP service you deploy in Task 3. **Do not modify.** The pre-built image is published by the course CI to `ghcr.io/inno-devops-labs/echo:v1`. See `plumbing/echo/README.md` for the endpoint list.

---

## Setup

Versions used in this lab — pin these where you have a choice:

| Component | Version | Released |
|---|---|---|
| Kubernetes (k3s) | `v1.36.1-k3s1` | Apr 22 2026 (1.36 "Haru") |
| k3d | 5.7+ | — |
| kubectl | 1.36.x (match the cluster) | — |
| `echo` plumbing image | `ghcr.io/inno-devops-labs/echo:v1` | published by course CI |

```bash
docker --version           # 28.x or 29.x — k3d runs k3s inside Docker
k3d version                # 5.7+
kubectl version --client   # 1.36.x — match the cluster you'll create
```

> ⚠️ **Do not use Docker Desktop's bundled Kubernetes.** It lags upstream and you will get version-skew surprises mid-lab.

Create the directory layout (you'll fill the files yourself):

```
k8s/
├── web-deployment.yaml          # YOU write this (§2)
├── web-service.yaml             # YOU write this (§2)
├── echo-deployment.yaml         # YOU write this (§3)
├── echo-service.yaml            # YOU write this (§3)
├── ingress.yaml                 # YOU write this (bonus only)
└── docs/
    └── LAB09.md                 # your submission report
```

---

## Task 1 — Local k3d cluster (2 pts)

### 1.1 — Why k3d, not minikube / kind / Docker Desktop

In `docs/LAB09.md` answer in 2–3 sentences each:

1. What does k3d actually run inside Docker, and how is that different from minikube's VM-based approach?
2. Why does this lab need **multi-node** (`--agents 2`)? What's visible at 3 nodes that isn't visible at 1?
3. Which ingress controller and LoadBalancer implementation does k3d ship by default, and what would change in your Bonus Ingress if you swapped k3d for kind?

(Lecture 9 slide 13 + the [k3d docs](https://k3d.io/) cover this.)

### 1.2 — Create the cluster

`YOUR TASK`: bring up a cluster named `devops` with **1 server + 2 agents** on Kubernetes **1.36.1**, mapping the LoadBalancer ports `80→8080` and `443→8443` on your host so the bonus Ingress is reachable.

```bash
# YOUR TASK lines below:
#   --image:  which k3s tag = K8s 1.36.1?  (see hint after the block)
#   --agents: how many agents for a multi-node cluster?
#   first -p: host port that maps cluster :80
#   second -p: host port that maps cluster :443
k3d cluster create devops \
  --image rancher/k3s:___-k3s1 \
  --agents ___ \
  -p "___:80@loadbalancer" \
  -p "___:443@loadbalancer"
```

> 💡 k3s image tags **append** `-k3s1` to the upstream K8s version. Pick the newest `v1.36.x-k3s1` tag from [`rancher/k3s` on Docker Hub](https://hub.docker.com/r/rancher/k3s/tags).

### 1.3 — Verify

```bash
kubectl config use-context k3d-devops    # k3d sets this automatically — sanity-check
kubectl version                          # server MUST report 1.36.x; client can be ±1 minor (skew is OK)
kubectl cluster-info
kubectl get nodes -o wide                # YOUR TASK: expect exactly THREE nodes — 1 server + 2 agents
```

> 💡 If `kubectl` prints a `WARNING: version difference between client (1.34) and server (1.36) exceeds the supported version skew`, it's a warning, not an error — the lab still passes. To silence it, install kubectl 1.36.x to match the cluster.

### 1.4 — Proof of work

**Paste into `docs/LAB09.md`:**

- The 3-question research answers from §1.1
- `kubectl version` showing client + server `1.36.x`
- `kubectl get nodes -o wide` showing **3** nodes, all `Ready`, all `v1.36.1+k3s1`
- Your `k3d cluster create` command (so the grader can re-create your environment)

---

## Task 2 — Deploy your `web` service (3 pts)

This is the manifest-writing skill. The shape below shows you which fields a `Deployment` requires; the **values** are yours to derive from the K8s API + your Lab 1/2 work.

### 2.1 — The Deployment

`YOUR TASK`: write `k8s/web-deployment.yaml`. Three labels-and-selectors must agree across this file (Deployment metadata, `spec.selector.matchLabels`, and `spec.template.metadata.labels`) — that label triangle is the #1 K8s YAML error. The Service in §2.2 will select the same label.

```yaml
# k8s/web-deployment.yaml
apiVersion: ___                       # YOUR TASK: which apiGroup/version owns Deployment?
kind: ___                             # YOUR TASK
metadata:
  name: ___                           # YOUR TASK: lab's headline name
  labels:
    ___: ___                          # YOUR TASK: the label the Service selector will match
spec:
  replicas: ___                       # YOUR TASK: how many web pods? (lecture 9 + Task 4 scale)
  selector:
    matchLabels:
      ___: ___                        # MUST match the pod template labels below
  strategy:
    type: ___                         # YOUR TASK: which strategy for zero-downtime updates?
    rollingUpdate:
      maxUnavailable: ___             # YOUR TASK: 0 = strict zero-downtime
      maxSurge: ___
  template:
    metadata:
      labels:
        ___: ___                      # MUST match selector.matchLabels EXACTLY
    spec:
      containers:
        - name: ___                   # YOUR TASK
          image: ___                  # YOUR TASK: your Lab 2 image. Two valid forms:
                                      #   - GHCR pull: ghcr.io/<you>/devops-info-service:1.0.0  (public package — Lab 2 Task 7)
                                      #   - Local tag: devops-info-service:lab02-multi          (must `k3d image import` — see §2.3)
          imagePullPolicy: ___        # YOUR TASK: which policy lets a k3d-imported image work?
                                      #            (hint: see Setup note about local images + Common Pitfalls)
          ports:
            - name: ___               # YOUR TASK: name this port (e.g. `http`). Lab 10's Helm chart
                                      #            and Lab 16's ServiceMonitor both target the port BY NAME.
                                      #            Pick a name now or rewrite both labs later.
              containerPort: ___      # YOUR TASK: the port your Lab 1 app listens on
              protocol: TCP
          resources:
            requests:
              cpu: ___                # YOUR TASK: scheduler reserves this — see lecture 9 slide 15
              memory: ___
            limits:
              cpu: ___                # YOUR TASK
              memory: ___             # YOUR TASK: memory-OOMKill ceiling — set tightly
          livenessProbe:
            httpGet:
              path: ___               # YOUR TASK: which endpoint from Lab 1? (hint: cheap, not the app root)
              port: ___
            initialDelaySeconds: ___  # YOUR TASK
            periodSeconds: ___
          readinessProbe:
            httpGet:
              path: ___               # YOUR TASK
              port: ___
            periodSeconds: ___        # YOUR TASK: fail fast — readiness gates traffic
```

**Why each blank matters (read this before filling them in):**

- **`apiVersion` / `kind`** — Deployment lives in `apps/v1` (the *only* GA group/version for it). `Pod` is `v1`, `Service` is `v1`. Memorize the table; you'll write it from muscle by Lab 13.
- **The label triangle** — `metadata.labels`, `spec.selector.matchLabels`, and `spec.template.metadata.labels` are three *separate* dicts that all need the same key/value pair. The selector is **immutable after creation**; if you mis-key it you must `kubectl delete` and re-apply.
- **`imagePullPolicy`** — `Always` re-pulls every restart; **fails on k3d for locally-built images** because the registry doesn't have them. `IfNotPresent` uses what's already in containerd (which is what `k3d image import` populates). `Never` is the paranoid version. Pick deliberately.
- **`resources.requests`** — the **scheduler** reads these to pick a node. Set too low and noisy neighbours starve you; too high and your pods sit `Pending` because no node has the headroom.
- **`resources.limits.memory`** — past this, the kernel OOMKills the container. Set tightly so a leak shows up as a restart, not a node-wide swap death. **CPU** limits cause silent throttling — be more lenient there.
- **Probes** — `livenessProbe` failing = container restarted. `readinessProbe` failing = pod pulled from the Service endpoints list (no restart). Both pointing at the app's root `/` is the single most common production foot-gun (slow page = restart loop = outage). Pick a `/health` or `/healthz` that returns 200 with no DB calls.
- **`strategy.rollingUpdate.maxUnavailable: 0`** is what guarantees zero downtime in Task 4. The default (25%) means one of your three pods is gone during the update.

### 2.2 — The Service

`YOUR TASK`: write `k8s/web-service.yaml`. Choose the **Service type** that makes the app reachable from your laptop without a port-forward (lecture 9 slide 9 has the table; on k3d it's the development-friendly one).

```yaml
# k8s/web-service.yaml
apiVersion: ___                       # YOUR TASK
kind: ___                             # YOUR TASK
metadata:
  name: ___                           # YOUR TASK: kube-DNS will resolve THIS name inside the cluster
spec:
  type: ___                           # YOUR TASK: see lecture 9 slide 9 — pick the one that exposes :NodePort on every node
  selector:
    ___: ___                          # MUST match the Deployment pod labels — kube-proxy uses this to build endpoints
  ports:
    - name: ___                       # YOUR TASK: same name you gave the containerPort (e.g. `http`).
                                      #            Lab 16's ServiceMonitor uses this string, not the number.
      port: ___                       # YOUR TASK: the port the Service listens on (cluster-side)
      targetPort: ___                 # YOUR TASK: prefer the port NAME (e.g. `http`) over a number —
                                      #            keeps the Service stable when the container port changes
      protocol: TCP
      # nodePort: ___                 # OPTIONAL: pin it (30000–32767), or let K8s pick
```

**Why each blank matters:**

- **Service `name`** — this is what kube-DNS resolves inside the cluster. `curl http://web/` from any other pod hits this Service. Pick something short and stable; renaming a Service is a footgun (DNS clients cache).
- **`type`** — `ClusterIP` (default) is internal-only; `NodePort` exposes a high port on every node; `LoadBalancer` provisions a cloud LB (klipper-lb on k3d). For local dev a NodePort works once you've mapped the host port; `LoadBalancer` works on k3d too thanks to klipper. Pick one, justify it.
- **`port` vs `targetPort`** — `port` is what *clients* hit on the Service IP; `targetPort` is what the **container** listens on. Mismatched here = endpoints exist but no connectivity. Don't blindly set them equal — they're different concepts.
- **Named ports** — `ports[].name: http` (and `targetPort: http` referencing the container's `ports[].name`) is **not optional polish**. Lab 16's `ServiceMonitor.spec.endpoints[].port` is a **string** (the port *name*), not a number — a bare numeric port silently fails to resolve and the operator skips your service. Set the name now or rewrite this Service later.
- **`selector`** — must match the pod labels exactly. `kubectl get endpoints web` is your debugging oracle: if it's empty, your selector doesn't match any pod.

### 2.3 — Load your image and apply

**Two paths** — pick one based on whether your Lab 2 image is public on GHCR:

**Path A — GHCR (recommended).** Your `ghcr.io/<you>/devops-info-service:1.0.0` is public (per Lab 2 §7). k3d's containerd pulls it directly; **no `k3d image import` needed**. Skip to `kubectl apply`.

**Path B — Local build only.** Your image only exists in your laptop's Docker (`devops-info-service:lab02-multi` or similar) — k3d's containerd has never heard of it. You **must** import it:

```bash
docker images | grep devops-info-service         # confirm the tag exists locally
k3d image import ___ --cluster devops            # YOUR TASK: paste the exact `<name>:<tag>` from above
```

> 💡 The k3d nodes run k3s in their own containers with their own containerd — your laptop's Docker daemon is invisible to them. `k3d image import` is how you bridge that gap (it `docker save | docker load`s into each k3d node). If `kubectl get pods` shows `ErrImagePull`/`ImagePullBackOff` and you're sure the tag is right, you forgot this step.

Once the image is reachable (either path):

```bash
kubectl apply -f k8s/web-deployment.yaml
kubectl apply -f k8s/web-service.yaml

kubectl rollout status deploy/web              # blocks until 3/3 ready
kubectl get pods -l app=web -o wide            # YOUR TASK: confirm pods spread across all 3 nodes
kubectl get endpoints web                      # MUST list 3 pod IPs once readiness passes
```

> 💡 **Debug ladder when this doesn't work first time:**
> 1. `kubectl get pods` — `ImagePullBackOff` = registry/credentials/`imagePullPolicy` wrong; `CrashLoopBackOff` = the container exits, look at logs.
> 2. `kubectl describe pod <name>` — bottom **Events** section has the real failure.
> 3. `kubectl logs <pod-name>` — your app's stdout.
> 4. `kubectl get endpoints web` — empty list = selector/label mismatch (the label triangle is wrong).

### 2.4 — Proof of work

**Paste into `docs/LAB09.md`:**

- `kubectl get deploy,rs,pods,svc,endpoints -l app=web` — must show **3/3** ready and **3 endpoint IPs**
- `kubectl get pods -l app=web -o wide` — the **NODE** column must show all 3 nodes represented (proves multi-node scheduling — this is half the reason you ran `--agents 2`)
- A `kubectl port-forward svc/web 8080:80` + `curl -s localhost:8080/health` capture proving the Service is wired to a working app
- Your `imagePullPolicy` choice + 1 sentence justifying it
- Your resource requests/limits + 1 sentence justifying them

---

## Task 3 — Deploy the `echo` plumbing service (2 pts)

The 2nd service. Read `plumbing/echo/README.md` for the endpoint contract — you do **not** build or modify this code.

| Path | Behaviour |
|---|---|
| `GET /ping` | Returns `pong\n` — your headline smoke test in Task 4 |
| `* /echo` | JSON with `hostname` + a request counter — useful for spotting load-balancing |
| `GET /healthz` | Returns `ok` (200) — wire into probes |
| `GET /metrics` | Prometheus format (you'll scrape this in Lab 16) |

The image is `ghcr.io/inno-devops-labs/echo:v1`; it listens on **port 8081**.

### 3.1 — The echo Deployment

`YOUR TASK`: write `k8s/echo-deployment.yaml`. Same shape as `web` but different labels, different image, different port, different replica count — **2 replicas** is non-negotiable because Task 4 needs the Service to round-robin across **two** pods.

```yaml
# k8s/echo-deployment.yaml
apiVersion: ___                       # YOUR TASK
kind: ___                             # YOUR TASK
metadata:
  name: ___                           # YOUR TASK
  labels:
    ___: ___                          # YOUR TASK: must be DIFFERENT from web's label value
spec:
  replicas: ___                       # YOUR TASK: read the prose above — why two?
  selector:
    matchLabels:
      ___: ___
  template:
    metadata:
      labels:
        ___: ___
    spec:
      containers:
        - name: ___
          image: ___                  # YOUR TASK: the published echo image — see plumbing/echo/README.md
          ports:
            - name: ___               # YOUR TASK: name the port (e.g. `http`). Same reason as the web Deployment.
              containerPort: ___      # YOUR TASK: see echo README — what port?
              protocol: TCP
          resources:
            requests: { cpu: ___, memory: ___ }    # YOUR TASK: echo is a tiny Go binary
            limits:   { cpu: ___, memory: ___ }
          readinessProbe:
            httpGet:
              path: ___               # YOUR TASK: echo's readiness endpoint — README has it
              port: ___
            periodSeconds: ___
          livenessProbe:
            httpGet:
              path: ___
              port: ___
            initialDelaySeconds: ___
            periodSeconds: ___
```

> 💡 **Go binaries are tiny.** Set `requests.memory` to single-digit MiB and `requests.cpu` to ~10–50m. If you copy your `web` numbers you'll over-reserve cluster capacity and pods will go `Pending`.

### 3.2 — The echo Service

`YOUR TASK`: write `k8s/echo-service.yaml`. This one is `ClusterIP` (internal-only — the `web` pod calls it; no laptop access needed). The cross-service call in §4.1 will hit `http://echo:___/ping` — pick the Service `port` that makes that URL clean (lecture 9 slide 9 has the convention).

```yaml
# k8s/echo-service.yaml
apiVersion: ___
kind: ___
metadata:
  name: ___                           # YOUR TASK: the DNS name `web` will use to reach echo
spec:
  type: ___                           # YOUR TASK: internal-only — which type?
  selector:
    ___: ___                          # MUST match echo pod labels (NOT web's)
  ports:
    - name: ___                       # YOUR TASK: same name you gave the containerPort
      port: ___                       # YOUR TASK: HTTP-default port, so `http://echo/ping` works with no `:port`
      targetPort: ___                 # YOUR TASK: prefer the port NAME (string) over the container port number
      protocol: TCP
```

> 💡 **Why service `port: 80`?** Because `http://echo/ping` (no port) defaults to 80. If you set `port: 8081`, callers have to write `http://echo:8081/ping` — works, but the lecture/docs/your future Helm chart all assume the clean form. The Service port and container port are **decoupled**; that's the whole point.

### 3.3 — Apply and verify

```bash
kubectl apply -f k8s/echo-deployment.yaml
kubectl apply -f k8s/echo-service.yaml

kubectl get pods,svc,endpoints -l app=echo     # 2 pods Ready, 2 endpoint IPs
kubectl rollout status deploy/echo
```

### 3.4 — Proof of work

**Paste into `docs/LAB09.md`:**

- `kubectl get pods,svc,endpoints -l app=echo` — **2** pods Ready, Service has **2** endpoints
- One `kubectl describe svc echo` capture showing the `Selector` and `Endpoints` lines
- 1–2 sentences on **why your echo `requests` are smaller than `web`'s** — the tiny Go binary justification

---

## Task 4 — Cross-service networking, scaling, rolling updates (2 pts) ← **headline task**

### 4.1 — The kube-DNS proof — the most important command in this lab

`YOUR TASK`: from **inside a `web` pod**, call `echo`'s `/ping` endpoint by its **DNS name** and capture `pong`. No port-forward. No NodePort. The request must traverse pod → Service DNS → kube-proxy → echo pod, with kube-DNS doing the name resolution.

```bash
WEBPOD=$(kubectl get pod -l ___=___ -o jsonpath=___)    # YOUR TASK: get the name of any web pod
                                                        #            (hint: -o jsonpath='{.items[0].metadata.name}')

kubectl exec $WEBPOD -- ___ ___                         # YOUR TASK: hit http://echo/ping
                                                        #            (hint: which tool? — see "If curl is missing" below)
# expected output:
# pong
```

**Why this matters.** If you get `pong`, six things just worked at once:
1. **kube-DNS** in `kube-system` resolved `echo` → the Service's ClusterIP
2. The Service's **selector** matched the echo pod labels
3. **kube-proxy** programmed iptables/IPVS rules to route Service IP → one of two pod IPs
4. The echo pod's **readinessProbe** passed, so it appears in `endpoints`
5. Cluster-internal networking forwarded the request across the node boundary (probably — `web` and `echo` likely landed on different nodes)
6. Your manifests' **label triangle** is consistent end-to-end

If any one of those is wrong, you get a timeout or a DNS NXDOMAIN. **Save the output.** This is the headline artifact of Lab 9.

<details>
<summary>💡 If your <code>web</code> image doesn't ship <code>curl</code></summary>

A slim Lab 2 image likely doesn't have `curl`. Two options — both acceptable as long as the call originates **inside the cluster**:

```bash
# Option A — use python (Lab 1 left you a Python interpreter)
kubectl exec $WEBPOD -- python -c \
  "import urllib.request; print(urllib.request.urlopen('http://echo/ping').read().decode())"

# Option B — throwaway client pod inside the cluster
kubectl run tmp --rm -it --image=curlimages/curl:8.11.0 --restart=Never -- \
  curl -s http://echo/ping
```

What does **NOT** count: `curl localhost:8088/ping` after `port-forward svc/echo` — that proves your laptop can reach echo, not that `web` can. The whole point is the **pod-to-pod** call.

</details>

### 4.2 — Service load-balancing across two echo pods

The echo Service has 2 endpoints. Hit `/echo` a few times — the response includes the responding pod's `hostname`, so you can see kube-proxy round-robining the traffic.

```bash
kubectl exec $WEBPOD -- sh -c '___'                     # YOUR TASK: hit http://echo/echo 6+ times in a loop,
                                                        #            extract or print the hostname per call
# expected: hostname rotates between the 2 echo pods (roughly 50/50 over enough calls)
```

> 💡 Round-robin is per-connection by default, not per-request. If you see the same hostname every time, your client is reusing one connection — add a fresh request each time (`-H 'Connection: close'` for curl, or just loop fresh `urlopen` calls in Python).

### 4.3 — Scale `web` to 5 replicas

`YOUR TASK`: scale up. Use the **declarative** path (edit `replicas:` in the manifest and `kubectl apply -f`) — imperative `kubectl scale` works but doesn't survive the next `apply` of your manifest, which is the GitOps-killing footgun you'll meet again in Lab 13.

```bash
# After editing the manifest:
kubectl apply -f k8s/web-deployment.yaml
kubectl get pods -l app=web -w           # watch new pods come up
kubectl get endpoints web                # 5 pod IPs once readiness passes
```

### 4.4 — Rolling update + rollback

Change the `web` image to a different tag (rebuild your Lab 2 image with a new tag, or temporarily change `name:` of the container — anything that makes the pod template hash different). Apply and watch:

```bash
kubectl apply -f k8s/web-deployment.yaml
kubectl rollout status deploy/web        # blocks until new ReplicaSet is fully ready
kubectl rollout history deploy/web       # shows both revisions

kubectl rollout undo deploy/web          # back to the previous revision
kubectl rollout status deploy/web
```

With `maxUnavailable: 0` (from §2.1), at no point should `kubectl get endpoints web` drop below 5. **Verify this in another shell.**

### 4.5 — Proof of work

**Paste into `docs/LAB09.md`:**

- The **kube-DNS proof** — your `kubectl exec $WEBPOD -- ... http://echo/ping` command and its `pong` output. **This is the headline artifact.**
- The load-balancing capture — 6+ hostnames showing **both** echo pod names appearing roughly evenly
- `kubectl get pods -l app=web -o wide` after scaling to 5 — 5 pods, spread across nodes
- `kubectl rollout history deploy/web` — at least 2 revisions visible
- `kubectl rollout undo` output + a `kubectl rollout status` confirming the rollback succeeded
- 2–3 sentences on the most useful `kubectl describe` / `kubectl get events` finding you hit while debugging — what was the actual `Events:` line that told you the answer?

---

## Task 5 — Documentation (1 pt)

`YOUR TASK`: write `k8s/docs/LAB09.md` with these sections, in order:

1. **Architecture** — a Mermaid diagram showing `User → web Service → 3× web pods` and `web pod → echo Service → 2× echo pods`, with the kube-DNS resolution marked on the second arrow
2. **Cluster** — your `k3d cluster create` command + the 3-question research from §1.1
3. **Manifests** — one short paragraph per file: which labels, which Service type, which replica count, which probe endpoints — and **why** for each non-obvious choice
4. **Cross-service evidence** — the §4.1 `pong` capture, with a sentence explaining each of the six things that just worked
5. **Operations** — scaling, rolling update, rollback evidence from §4.3–4.4
6. **Challenges & solutions** — at least one real one (not "I was new to YAML"); include the `kubectl describe` line that unblocked you

Include manifest **snippets** (not whole files — those are committed already) and the real CLI captures from Tasks 1–4.

---

## Bonus Task — Ingress with TLS through Traefik (2 pts)

Less hand-holding. k3d ships Traefik built in (it's the LoadBalancer behind the `:8080`/`:8443` host ports you mapped in §1.2) — **no controller install**. Use `*.localhost` (resolves to `127.0.0.1` automatically — no `/etc/hosts` edits).

`YOUR TASK`: route `web.localhost` → `web` Service and `echo.localhost` → `echo` Service, both over HTTPS, through a single `Ingress`.

1. **Self-signed cert + Secret** covering both hostnames:
   ```bash
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout tls.key -out tls.crt \
     -subj "/CN=web.localhost" \
     -addext "subjectAltName=DNS:web.localhost,DNS:echo.localhost"
   kubectl create secret tls ___ --key tls.key --cert tls.crt   # YOUR TASK: pick a Secret name
   ```

2. **`k8s/ingress.yaml`** — Ingress shape:

```yaml
apiVersion: ___                       # YOUR TASK: which group/version owns Ingress? (NOT extensions/v1beta1 — that's gone)
kind: ___
metadata:
  name: ___
spec:
  ingressClassName: ___               # YOUR TASK: k3d's built-in controller name (lecture 9 slide 13)
  tls:
    - hosts: [___, ___]               # YOUR TASK: both hostnames
      secretName: ___                 # YOUR TASK: matches the Secret name above
  rules:
    - host: ___                       # YOUR TASK: web's hostname
      http:
        paths:
          - path: ___                 # YOUR TASK
            pathType: ___             # YOUR TASK: Prefix or Exact?
            backend:
              service:
                name: ___             # YOUR TASK: which Service is this rule routing to?
                port:
                  number: ___         # YOUR TASK: the Service's port (NOT the targetPort).
                                      #            Or use `name: http` to reference the named Service port.
    - host: ___                       # YOUR TASK: echo's hostname
      http:
        paths:
          - path: ___
            pathType: ___
            backend:
              service:
                name: ___
                port:
                  number: ___         # (same options as above — number or name)
```

3. **Verify** via the host port you mapped at cluster create:
   ```bash
   curl -k https://echo.localhost:8443/ping    # → pong, through Traefik + TLS
   curl -k https://web.localhost:8443/health   # → your app's health JSON
   ```

> 💡 **Host-based routing** (one Service per hostname) avoids path-rewrite middleware, so each backend sees the request path unchanged. The alternative — path-based (`/web` → web, `/echo` → echo on a single hostname) — needs Traefik middleware to strip the prefix; not worth the complication for two services.

**Evidence (paste into `docs/LAB09.md`):**
- `kubectl get pods -n kube-system | grep traefik` — controller Running
- `kubectl get ingress` — your Ingress with the two hosts visible
- Both `curl -k https://...localhost:8443/...` captures, real output
- 1–2 sentences on what Ingress buys you over the NodePort Service from §2.2

---

## How to Submit

```bash
git switch -c lab09
git add k8s/
git commit -m "feat(lab09): web + echo on k3d — cross-service kube-DNS proven"
git push -u origin lab09
```

Open **two** PRs:

- `your-fork:lab09` → `course-repo:master` *(reviewed)*
- `your-fork:lab09` → `your-fork:master` *(merges into your own main when done)*

PR checklist:

```text
- [ ] Task 1 done — 3-node k3d cluster on K8s 1.36.1, evidence captured
- [ ] Task 2 done — web Deployment (3 replicas) + Service, label triangle correct, probes on cheap endpoint
- [ ] Task 3 done — echo Deployment (2 replicas) + ClusterIP Service, sized for a tiny Go binary
- [ ] Task 4 done — kubectl exec from inside web pod returns `pong` from echo; LB rotation shown; scaled to 5; rolled out & back
- [ ] Task 5 done — LAB09.md with all 6 sections + Mermaid diagram + the pong capture
- [ ] Bonus done — Ingress over HTTPS via Traefik, both hostnames reachable
```

---

## Acceptance Criteria

### Task 1 — k3d cluster (2 pts)
- ✅ `kubectl version` reports server `1.36.x`
- ✅ `kubectl get nodes -o wide` shows **3 nodes**, all `Ready`
- ✅ LoadBalancer host-port maps `:80→:8080` and `:443→:8443` present in the `k3d cluster create` command
- ✅ Research answers from §1.1 in `docs/LAB09.md`

### Task 2 — web service (3 pts)
- ✅ `web-deployment.yaml` and `web-service.yaml` written by hand
- ✅ Label triangle consistent (Deployment labels = selector.matchLabels = template labels)
- ✅ **Container port AND Service port both named** (e.g. `name: http`) — Lab 10/16 require this
- ✅ 3 replicas Ready; `kubectl get endpoints web` shows **3 IPs**
- ✅ Resource **requests AND limits** set; both probes wired to a `/health`-style endpoint, not the app root
- ✅ Pods spread across all 3 nodes (`-o wide` capture)

### Task 3 — echo service (2 pts)
- ✅ `echo-deployment.yaml` uses `ghcr.io/inno-devops-labs/echo:v1` (no self-builds)
- ✅ **2** replicas Ready; ClusterIP Service has **2** endpoints
- ✅ Probes wired to `/healthz:8081` (echo's actual readiness endpoint, per `plumbing/echo/README.md`)
- ✅ Resources sized smaller than web (tiny Go binary)

### Task 4 — cross-service + ops (2 pts)
- ✅ **`kubectl exec` into a web pod + call to `http://echo/ping` returns `pong`** — kube-DNS proof captured
- ✅ Load-balancing capture shows **both** echo pod hostnames appearing
- ✅ `web` scaled to 5; endpoints list reaches 5; no downtime visible
- ✅ Rolling update + rollback shown with `kubectl rollout history` evidence

### Task 5 — docs (1 pt)
- ✅ All 6 sections in `k8s/docs/LAB09.md`; Mermaid diagram included; the pong capture is the headline artefact

### Bonus — Ingress + TLS (2 pts)
- ✅ Self-signed Secret created with both SANs
- ✅ Ingress uses `ingressClassName: traefik`, both hosts routed
- ✅ Both `curl -k https://...localhost:8443/...` calls succeed

---

## Rubric

| Task | Points | Criteria |
|------|-------:|----------|
| **Task 1** — k3d cluster | **2** | 3-node K8s 1.36 cluster up, research answers, port maps for bonus |
| **Task 2** — web service | **3** | Hand-written Deployment + Service, label triangle correct, probes on cheap endpoint, requests+limits, 3 endpoints |
| **Task 3** — echo service | **2** | Provided image deployed (2 replicas), ClusterIP Service, probes on `/healthz` |
| **Task 4** — cross-service + ops | **2** | `pong` from inside web pod, LB rotation, scale+rollout+rollback |
| **Task 5** — docs | **1** | 6 sections, Mermaid, pong capture as headline |
| **Bonus** — Ingress + TLS | **2** | Traefik Ingress, both hostnames over HTTPS |
| **Total** | **12** | 10 main + 2 bonus |

---

## Resources

<details>
<summary>📚 Kubernetes documentation</summary>

- [Kubernetes 1.36 "Haru" release notes](https://kubernetes.io/blog/2026/04/22/kubernetes-v1-36-release/)
- [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Services & networking](https://kubernetes.io/docs/concepts/services-networking/service/)
- [DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [Liveness, readiness, startup probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [kubectl cheat sheet](https://kubernetes.io/docs/reference/kubectl/quick-reference/)

</details>

<details>
<summary>🛠️ Tools</summary>

- [k3d](https://k3d.io/) — k3s in Docker
- [k3s docs](https://docs.k3s.io/)
- [k9s](https://k9scli.io/) — TUI for kubectl
- [kubectx/kubens](https://github.com/ahmetb/kubectx) — context + namespace switcher
- [stern](https://github.com/stern/stern) — multi-pod log tailing

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs)</summary>

- **Label-selector mismatch — the #1 K8s YAML error.** The Deployment has *three* places where labels appear: `metadata.labels`, `spec.selector.matchLabels`, and `spec.template.metadata.labels`. The Service's `spec.selector` is a fourth. They all need to agree. Symptom: `kubectl get endpoints <svc>` is empty even though pods are Running. The selector is **immutable** after Deployment creation — if you got it wrong, you must `kubectl delete deploy/...` and re-apply (you can't `kubectl edit` your way out).

- **`imagePullPolicy: Always` fails for locally-built images on k3d.** `k3d image import` populates the cluster's containerd directly; there's no registry holding your `:latest` tag. `Always` re-pulls every restart and gets `ErrImagePull` / `ImagePullBackOff`. Use `IfNotPresent` for locally-imported images (this is also the default when your tag is anything other than `:latest` — but **don't rely on the default**; declare it).

- **NodePort on k3d needs the host port mapped at cluster create.** k3d's klipper-lb exposes the LoadBalancer-class ports you listed in `-p`, but a NodePort in the 30000–32767 range isn't reachable from your laptop unless you either (a) added `-p "3xxxx:3xxxx@server:0"` at cluster create, or (b) `kubectl port-forward`. `LoadBalancer` Services and `port-forward` both work without ceremony; raw NodePort doesn't.

- **`livenessProbe` pointing at the app's main page.** When traffic spikes, your handler slows. Liveness times out, K8s restarts the container, the queue drains onto the remaining pods, *they* slow under doubled load — **cascading restarts** during the exact moment you needed the system to stay up. Liveness must point at a **cheap, in-process** signal (`/health` returning 200 with no DB calls). That's why Lab 1 made you build `/health` separately.

- **Missing or slow `readinessProbe` causes rolling-update gaps.** Without readiness, K8s adds a pod to the Service endpoints the instant the container *starts* — before your app is actually serving. During a rolling update, that means a few seconds of `connection refused` on every replacement. Readiness with `periodSeconds: 3–5` and a low `failureThreshold` keeps unready pods out of the endpoint list and out of traffic.

- **`port` vs `targetPort` confusion.** `port` is what *clients* hit on the Service; `targetPort` is what the **container** listens on. Common error: `port: 8081` on the echo Service. It works — but every caller now writes `http://echo:8081/ping` and your future Helm chart, Lab 13 ApplicationSet, and Lab 16 ServiceMonitor all have to special-case the port. Pick `port: 80` for HTTP services so DNS-only URLs work.

- **Resource requests too low → noisy-neighbour starvation.** k3d on a laptop has finite memory. If `web`'s `requests: 64Mi` is realistic but you set `8Mi`, the scheduler over-packs nodes and your pods get OOM-evicted under any real workload. Set `requests` to what your app actually uses at idle + a small buffer, not the minimum it can boot with.

- **`kubectl edit` instead of `kubectl apply -f`.** `edit` mutates the live object directly; your manifest in git no longer matches reality. Next `apply` reverts your hotfix. In a GitOps world (Lab 13+) this is a deploy-time race condition. Always edit the YAML, `apply -f`, commit.

- **Container missing `curl`/`wget` and you reach for the wrong workaround.** Don't `port-forward` to "test" cross-service calls — that proves your laptop reaches echo, not that `web` does. Use `kubectl run tmp --rm -it --image=curlimages/curl ...` or `kubectl exec $WEBPOD -- python -c "..."` so the call originates **inside the cluster**.

- **k3d's bundled Traefik vs ingress-nginx muscle memory.** Tutorials online assume ingress-nginx (`ingressClassName: nginx`, `nginx.ingress.kubernetes.io/*` annotations). On k3d it's Traefik (`ingressClassName: traefik`, `traefik.ingress.kubernetes.io/*` annotations). The Kubernetes `Ingress` core fields are portable; annotations are not.

</details>

<details>
<summary>🔍 Debugging cheatsheet</summary>

```bash
kubectl describe pod <name>           # bottom Events section = root-cause oracle
kubectl get events --sort-by=.lastTimestamp  # cluster-wide event stream
kubectl logs <pod> --previous         # logs from the previous (crashed) container
kubectl get endpoints <svc>           # empty = selector/label mismatch
kubectl exec -it <pod> -- /bin/sh     # shell into the pod (if it has one)
kubectl run net-debug --rm -it --image=nicolaka/netshoot --restart=Never -- bash
                                       # DNS + network sandbox with dig, nslookup, curl, tcpdump
```

</details>

---

## Looking Ahead

| Lab | What it adds to this stack |
|---:|---|
| 10 | Re-package these manifests as a **Helm 4** chart; `echo` becomes a subchart |
| 11 | Replace plaintext config with **Secrets** (and meet OpenBao) |
| 12 | **ConfigMaps** + **PVCs** — config injection + state survival across pod restarts |
| 13 | **ArgoCD** GitOps — `web` + `echo` deployed via an `ApplicationSet` for 2 envs |
| 14 | **Argo Rollouts** — canary the `echo` Deployment with progressive traffic shift |
| 16 | **kube-prometheus-stack** — scrape `echo`'s `/metrics` via a `ServiceMonitor` |

---

**Good luck!** ☸️

> **Remember:** the K8s networking model only clicks once you have a **second** service to talk to. That `pong` returned by `echo` — to a `curl` run *inside* your `web` pod — is the moment everything in lecture 9 (Pod, Service, label selector, kube-DNS, endpoints, kube-proxy) lines up. If only one capture survives the lab, make it that one.
