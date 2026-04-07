# Lab 16 — Kubernetes Monitoring & Init Containers

![difficulty](https://img.shields.io/badge/difficulty-advanced-red)
![topic](https://img.shields.io/badge/topic-Observability-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-Prometheus%20%7C%20Grafana-informational)

> Implement comprehensive cluster monitoring with Kube-Prometheus stack and learn init container patterns.

## Overview

Production Kubernetes clusters require robust monitoring. The Kube-Prometheus stack provides a complete solution with Prometheus, Grafana, and Alertmanager. Init containers enable setup tasks before your main application starts.

**What You'll Learn:**
- Kube-Prometheus stack components
- Grafana dashboard exploration
- Prometheus metrics and queries
- Init container patterns

**Tech Stack:** Prometheus | Grafana | Alertmanager | node-exporter | Init Containers

**Tested Versions:** Minikube v1.34+ | Kubernetes v1.32+ | kube-prometheus-stack 65.x

---

## Tasks

### Task 1 — Kube-Prometheus Stack (2 pts)

**Objective:** Install and understand the monitoring stack.

**Requirements:**

1. **Understand Components** - Document roles of:
   - Prometheus Operator
   - Prometheus
   - Alertmanager
   - Grafana
   - kube-state-metrics
   - node-exporter

2. **Install via Helm**
   - Add prometheus-community repository
   - Install in monitoring namespace
   - Verify all pods are running

<details>
<summary>💡 Hints</summary>

**Installation:**
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

kubectl get pods -n monitoring
```

**Resources:**
- [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)

</details>

---

### Task 2 — Grafana Dashboard Exploration (3 pts)

**Objective:** Use Grafana dashboards to answer questions about your cluster.

**Access Grafana:**
```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# Default: admin / prom-operator
```

**Answer these questions using dashboards:**

1. **Pod Resources:** CPU/memory usage of your StatefulSet
2. **Namespace Analysis:** Which pods use most/least CPU in default namespace?
3. **Node Metrics:** Memory usage (% and MB), CPU cores
4. **Kubelet:** How many pods/containers managed?
5. **Network:** Traffic for pods in default namespace
6. **Alerts:** How many active alerts? Check Alertmanager UI

<details>
<summary>💡 Hints</summary>

**Useful Dashboards:**
- "Kubernetes / Compute Resources / Namespace (Pods)"
- "Kubernetes / Compute Resources / Pod"
- "Node Exporter / Nodes"
- "Kubernetes / Kubelet"

**Alertmanager:**
```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```

</details>

---

### Task 3 — Init Containers (3 pts)

**Objective:** Implement init containers for pod initialization.

**Requirements:**

1. **Implement Basic Init Container**
   - Download a file using `wget`
   - Save to shared volume
   - Verify main container can access it

2. **Wait-for-Service Pattern**
   - Create init container that waits for a service
   - Only start main container when dependency ready

<details>
<summary>💡 Hints</summary>

**Download Init Container:**
```yaml
spec:
  initContainers:
    - name: init-download
      image: busybox:1.36
      command: ['sh', '-c', 'wget -O /work-dir/index.html https://example.com']
      volumeMounts:
        - name: workdir
          mountPath: /work-dir
  containers:
    - name: main-app
      volumeMounts:
        - name: workdir
          mountPath: /data
  volumes:
    - name: workdir
      emptyDir: {}
```

**Wait Pattern:**
```yaml
initContainers:
  - name: wait-for-service
    image: busybox:1.36
    command: ['sh', '-c', 'until nslookup myservice; do sleep 2; done']
```

**Verification:**
```bash
kubectl get pods -w  # Watch Init:0/1 → Running
kubectl logs <pod> -c init-download
kubectl exec <pod> -- cat /data/index.html
```

</details>

---

### Task 4 — Documentation (2 pts)

**Create `k8s/MONITORING.md` with:**

1. **Stack Components** - Descriptions in your own words
2. **Installation Evidence** - `kubectl get po,svc -n monitoring`
3. **Dashboard Answers** - All 6 questions with screenshots
4. **Init Containers** - Implementation and proof of success

---

## Bonus Task — Custom Metrics & ServiceMonitor (2.5 pts)

**Objective:** Expose application metrics and configure Prometheus scraping.

**Requirements:**

1. **Add `/metrics` endpoint** to your app using Prometheus client library
2. **Create ServiceMonitor** CRD for Prometheus to scrape your app
3. **Verify metrics in Prometheus UI**

<details>
<summary>💡 Hints</summary>

**ServiceMonitor:**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: myapp-monitor
  labels:
    release: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: myapp
  endpoints:
    - port: http
      path: /metrics
```

**Prometheus UI:**
```bash
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
```

</details>

---

## Checklist

- [ ] Prometheus stack installed
- [ ] All 6 dashboard questions answered
- [ ] Screenshots included
- [ ] Init container downloading file
- [ ] Wait-for-service pattern implemented
- [ ] `k8s/MONITORING.md` complete

---

## Rubric

| Criteria | Points |
|----------|--------|
| **Prometheus Stack** | 2 pts |
| **Grafana Exploration** | 3 pts |
| **Init Containers** | 3 pts |
| **Documentation** | 2 pts |
| **Bonus** | 2.5 pts |
| **Total** | 12.5 pts |

---

## Resources

<details>
<summary>📚 Documentation</summary>

- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)
- [Init Containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [ServiceMonitor](https://prometheus-operator.dev/docs/user-guides/getting-started/)

</details>

---

## Course Completion

Congratulations on completing the core Kubernetes labs! You now have experience with the complete DevOps lifecycle from development to production monitoring.

**Optional:** Labs 17-18 are exam alternatives covering Cloudflare Workers and Nix.

---

**Good luck!** 📊

> **Remember:** Monitoring is not optional in production. If you can't measure it, you can't improve it.
