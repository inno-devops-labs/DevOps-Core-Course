# Lab 14 — in-cluster Prometheus pointer (bonus only)

Lab 8 stood up Prometheus in a **Docker-Compose** stack on your laptop. Lab 14's
bonus `AnalysisTemplate` runs **inside** the k3d cluster — `http://localhost:9090`
from a pod means *the pod's own localhost*, not your laptop's.

This file lists the three ways to give Argo Rollouts a reachable URL. Pick one,
document the choice in `docs/LAB14.md`.

---

## Option 1 — Reach back to the host (cheapest)

k3d exposes the Docker host as **`host.k3d.internal`**. Your Lab 8 Prometheus on
`localhost:9090` becomes reachable from any pod in the cluster as
`http://host.k3d.internal:9090`.

```yaml
  provider:
    prometheus:
      address: http://host.k3d.internal:9090
```

✅ Zero setup — works today if Lab 8's stack is `docker compose up`.
❌ Lab 16 replaces this when you move Prometheus into the cluster — you'll edit
   the AnalysisTemplate again.
❌ Doesn't work on plain `kind` (use `host.docker.internal` there instead).

---

## Option 2 — Minimal in-cluster Prometheus (recommended)

Stand up a tiny Prometheus in a `monitoring` namespace that scrapes your
`app-python` Service via the `prometheus.io/scrape` annotation pattern. This is
what Lab 16 will replace with kube-prometheus-stack — installing it now is a
two-file dress rehearsal.

```bash
kubectl create namespace monitoring

# Minimal scrape config — adapt the job_name to match your app's Service labels
cat <<'EOF' | kubectl apply -n monitoring -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: app-python
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app_kubernetes_io_name]
            regex: app-python
            action: keep
          - source_labels: [__meta_kubernetes_pod_ip]
            target_label: __address__
            replacement: ${1}:5000
EOF

kubectl apply -n monitoring -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
spec:
  replicas: 1
  selector: { matchLabels: { app: prometheus } }
  template:
    metadata: { labels: { app: prometheus } }
    spec:
      serviceAccountName: prometheus
      containers:
        - name: prometheus
          image: prom/prometheus:v3.1.0
          args:
            - --config.file=/etc/prometheus/prometheus.yml
          ports: [ { containerPort: 9090 } ]
          volumeMounts:
            - { name: config, mountPath: /etc/prometheus }
      volumes:
        - { name: config, configMap: { name: prometheus-config } }
---
apiVersion: v1
kind: Service
metadata: { name: prometheus }
spec:
  selector: { app: prometheus }
  ports: [ { port: 9090, targetPort: 9090 } ]
EOF

# RBAC for the kubernetes_sd_configs discovery — Prometheus needs to list pods
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: ServiceAccount
metadata: { name: prometheus, namespace: monitoring }
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata: { name: prometheus }
rules:
  - apiGroups: [""]
    resources: ["pods", "services", "endpoints"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata: { name: prometheus }
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
  - { kind: ServiceAccount, name: prometheus, namespace: monitoring }
EOF
```

Then in your `AnalysisTemplate`:

```yaml
  provider:
    prometheus:
      address: http://prometheus.monitoring:9090
```

✅ Survives Lab 16 — kube-prometheus-stack publishes a Service at the same name
   (`prometheus-operated.monitoring`). Switching is a one-line URL change.
✅ No host-coupling — works on `kind`, EKS, GKE, anywhere.

---

## Option 3 — Skip the bonus

The main tasks (1–4) do not need Prometheus. If your Lab 8 stack is gone and
Lab 16 is still two weeks out, hand in 10/10 on the main tasks and pick up the
bonus when kube-prometheus-stack lands.

---

## Sanity check whichever option you pick

From a throwaway pod inside the cluster, prove the URL resolves and returns
Prometheus's own metrics:

```bash
kubectl run probe --rm -it --image=curlimages/curl:8.11.0 --restart=Never -- \
  curl -s http://<your-address>/-/healthy
# expected: Prometheus is Healthy.

kubectl run probe --rm -it --image=curlimages/curl:8.11.0 --restart=Never -- \
  curl -s 'http://<your-address>/api/v1/query?query=up' | head -20
# expected: JSON with "status":"success" — proves the API works from inside the cluster
```

If the second call returns no `up{job="app-python"}` series, Prometheus isn't
scraping your app — fix scraping first; the `AnalysisTemplate` cannot succeed
against metrics that don't exist.
