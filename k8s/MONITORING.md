# Kubernetes monitoring (Lab 16)

This document covers the **kube-prometheus-stack**, **Grafana** exploration, and the **init container** pattern implemented in the `devops-info-service` Helm chart. The bonus task (ServiceMonitor and `/metrics` in the app) is not required here; see the lab for optional points.

## 1. Stack components (what each part does)

| Component | Role |
|------------|------|
| **Prometheus Operator** | Kubernetes operator that manages Prometheus, Alertmanager, and scrape configs (including `ServiceMonitor` CRDs) in a declarative way. |
| **Prometheus** | Time-series database and scraper: pulls metrics on a schedule, stores them, and evaluates alerting rules. |
| **Alertmanager** | Receives alerts from Prometheus, deduplicates, groups, and routes them (e.g. to receivers or a UI) according to your routing config. |
| **Grafana** | Dashboards and visualization: connects to Prometheus (and other sources) to graph metrics and explore queries. |
| **kube-state-metrics** | Exposes state of Kubernetes API objects (Pods, Deployments, etc.) as Prometheus metrics, so you can query cluster/object health. |
| **node-exporter** | Runs on (or for) nodes and exports hardware/OS metrics (CPU, memory, disk, network) for node-level dashboards. |

## 2. Install kube-prometheus-stack (Helm)

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f k8s/monitoring/kube-prometheus-stack-values.yaml
```

Adjust the release name or values file as needed. After install, all Pods in `monitoring` should reach `Running` / `Ready`.

**Verify:**

```bash
kubectl get pods,svc -n monitoring
```

Capture the output of the command above (or a fresh run) and keep it in this doc or your lab report as **installation evidence** — example placeholder:

```text
# Paste your `kubectl get pods,svc -n monitoring` output here
```

**Access UIs (local development):**

- Grafana (default in many charts: `admin` / `prom-operator` if unchanged by values):
  - `kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80`
- Alertmanager:
  - `kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093`
- Prometheus:
  - `kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090`

Service names can vary slightly with Helm release name and chart version; use `kubectl get svc -n monitoring` to match.

## 3. Grafana dashboard questions (Task 2)

Answer each question in your own words using the dashboards. Add **screenshots** (or exported panel links) under each item when you submit the lab.

1. **Pod resources (StatefulSet)**  
   *Question:* What are the CPU and memory usage characteristics of your StatefulSet workload?  
   *Hint:* e.g. “Kubernetes / Compute Resources / Pod” or namespace-level pod views; filter to your StatefulSet pods.

   **Your answer:** *(fill in after checking Grafana)*

2. **Namespace analysis (default)**  
   *Question:* In the `default` namespace, which pods use the most and least CPU?*  
   *Hint:* e.g. “Kubernetes / Compute Resources / Namespace (Pods)”.

   **Your answer:**

3. **Node metrics**  
   *Question:* What is node memory usage (percent and/or MB) and how many CPU cores are visible?*  
   *Hint:* e.g. “Node Exporter / Nodes” or node overview dashboards.

   **Your answer:**

4. **Kubelet**  
   *Question:* How many pods and containers does the kubelet report as managed?*  
   *Hint:* e.g. “Kubernetes / Kubelet”.

   **Your answer:**

5. **Network (default namespace)**  
   *Question:* What network traffic (e.g. receive/transmit) do you see for pods in `default`?*  
   *Hint:* use a dashboard that breaks traffic by namespace/pod (exact name depends on your stack version).

   **Your answer:**

6. **Alerts (Alertmanager)**  
   *Question:* How many **active** alerts are shown, and what do you see in the Alertmanager UI?*  
   *Access:* port-forward to Alertmanager (port **9093** above) and check “Active” (or equivalent).

   **Your answer:**

## 4. Init containers in the Helm chart (Task 3)

The chart supports two patterns when `initContainers` is enabled:

1. **Wait-for-service (DNS):** an init container runs `nslookup` in a loop until the configured host (default: `kubernetes.default.svc.cluster.local`) resolves, modelling “dependency ready” before the app starts.
2. **Download with wget:** a second init container runs `wget` and writes a file to a shared `emptyDir` at `/init-work`; the main container mounts the same volume **read-only** at `appMountPath` (default **`/data/init`**) so the app (or a shell) can read the file.

**Enable for the lab:**

```bash
# Example: render manifests with Lab 16 overrides
helm template lab k8s/devops-info-service \
  -f k8s/devops-info-service/values-monitoring-lab16.yaml \
  -n default
```

**Install/upgrade a release (cluster):**

```bash
helm upgrade --install devops-info-service k8s/devops-info-service \
  -f k8s/devops-info-service/values-monitoring-lab16.yaml \
  -n default
```

**Proof (run against a real cluster after rollout):**

```bash
kubectl get pods -l app.kubernetes.io/name=devops-info-service
kubectl describe pod <pod-name> | less   # look for init containers and event sequence
kubectl logs <pod-name> -c init-wait-for-dns
kubectl logs <pod-name> -c init-download
kubectl exec -it <pod-name> -c app -- \
  sh -c 'ls -la /data/init && head -5 /data/init/index.html'
```

Paste key command output in your lab or below as **evidence**:

```text
# init container logs and /data/init listing
```

**Defaults (see `values.yaml`):** `initContainers` is `false` unless you add `-f values-monitoring-lab16.yaml`. Tweak `initContainers.waitFor.host`, `initContainers.download.url`, and file names as needed; keep at least one of `waitFor` / `download` enabled when `initContainers.enabled` is true.

## 5. Checklist (non-bonus)

- [ ] Stack installed; `kubectl get pods,svc -n monitoring` saved
- [ ] All six Grafana/Alertmanager questions answered with notes
- [ ] Screenshots attached where required
- [ ] Init containers verified (`logs` + `exec` showing file under `/data/init`)

## 6. References

- [kube-prometheus-stack chart](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [Init containers (Kubernetes)](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator)
