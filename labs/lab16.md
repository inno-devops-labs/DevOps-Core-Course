# Lab 16 — Kubernetes Monitoring & Init Containers

![difficulty](https://img.shields.io/badge/difficulty-advanced-red)
![topic](https://img.shields.io/badge/topic-Observability-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-Prometheus%20%7C%20Grafana-informational)

> Build full cluster monitoring with kube-prometheus-stack and practice init container patterns.

## Overview

Production Kubernetes clusters require robust monitoring. In this lab you will install kube-prometheus-stack, inspect Grafana dashboards, and implement two practical init container scenarios.

**What You'll Learn**
- kube-prometheus-stack components and responsibilities
- Grafana dashboard analysis in Kubernetes
- Prometheus target verification and metric queries
- Init container patterns for bootstrap and dependency waiting

**Tech Stack:** Prometheus | Grafana | Alertmanager | kube-state-metrics | node-exporter | Init Containers  
**Tested Versions:** Minikube v1.34+ | Kubernetes v1.32+ | kube-prometheus-stack 65.x

> Use `k8s/MONITORING.md` as your execution guide and report template.

---

## Environment Requirements

- Docker Desktop is running (required for Minikube Docker driver)
- All lab commands are executed from **WSL** terminal
- `kubectl`, `helm`, and `minikube` are available in WSL
- Active context is the same Minikube cluster (`kubectl config current-context`)

---

## Tasks

### Task 1 — Install kube-prometheus-stack (2 pts)

**Objective:** Deploy the monitoring stack and explain each component.

**Requirements:**
1. Document roles of:
   - Prometheus Operator
   - Prometheus
   - Alertmanager
   - Grafana
   - kube-state-metrics
   - node-exporter
2. Install stack in namespace `monitoring` via Helm.
3. Verify all monitoring workloads are healthy.

Use `Part A (A0-A6)` in `k8s/MONITORING.md`.

---

### Task 2 — Grafana Dashboard Exploration (3 pts)

**Objective:** Answer dashboard-based cluster questions.

**Questions to answer (with screenshots):**
1. CPU and memory usage of your StatefulSet pod
2. Highest and lowest CPU pod in `default` namespace
3. Node memory usage (% and MB) and CPU core count
4. Number of pods/containers managed by kubelet
5. Pod network traffic in `default` namespace
6. Number of active alerts (Alertmanager)

Use `Part B3` in `k8s/MONITORING.md`.

---

### Task 3 — Init Containers (3 pts)

**Objective:** Implement and verify two init patterns.

**Requirements:**
1. **Download pattern**
   - Init container downloads a file with `wget`
   - Shared `emptyDir` volume is mounted in main container
   - Prove file is available in main container
2. **Wait-for-service pattern**
   - Init container waits until dependency is actually reachable
   - Main container starts only after dependency is ready

Use manifests:
- `k8s/init-container-download.yaml`
- `k8s/init-container-wait-service.yaml`

Note: DNS-only checks (`nslookup`) are not enough in many cases. Use HTTP/TCP reachability checks.

---

### Task 4 — Documentation (2 pts)

Complete `k8s/MONITORING.md` in English:

1. Stack component descriptions
2. Installation evidence (`kubectl get po,svc -n monitoring`)
3. Answers for all 6 dashboard questions with screenshots
4. Init container implementation and verification proof

---

## Bonus — Custom Metrics + ServiceMonitor (2.5 pts)

**Objective:** Expose app metrics and let Prometheus scrape them.

**Requirements:**
1. `/metrics` endpoint in the app (`app_python/app.py`)
2. `ServiceMonitor` resource (`k8s/servicemonitor.yaml`)
3. Verification in Prometheus UI (`myapp-monitor` target is `UP`, query returns data)

Use `Part A (A7-A13)` and `Part B5` in `k8s/MONITORING.md`.

---

## Checklist

- [ ] Monitoring stack installed
- [ ] All 6 dashboard answers recorded
- [ ] Screenshots attached
- [ ] Init download pattern verified
- [ ] Init wait-for-service pattern verified
- [ ] `k8s/MONITORING.md` completed in English

---

## Rubric

| Criteria | Points |
|----------|--------|
| Prometheus Stack | 2 pts |
| Grafana Exploration | 3 pts |
| Init Containers | 3 pts |
| Documentation | 2 pts |
| Bonus | 2.5 pts |
| **Total** | **12.5 pts** |

---

## Resources

- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)
- [Kubernetes Init Containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [Prometheus Operator ServiceMonitor](https://prometheus-operator.dev/docs/user-guides/getting-started/)

---

**Good luck.**  
If you cannot measure it, you cannot improve it.
