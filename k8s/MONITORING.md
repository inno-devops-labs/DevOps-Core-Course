# Monitoring Notes

This file is the Lab 16 entry point for Kubernetes monitoring and init containers.

## Lab 16 Documentation

The full report is in [docs/LAB16.md](docs/LAB16.md). It includes:

- kube-prometheus-stack component descriptions and installation evidence.
- Grafana dashboard answers for pod resources, namespace CPU, node metrics, kubelet counts, default namespace network traffic, and active alerts.
- Init container implementation and proof that the main container can read the downloaded file.
- Bonus ServiceMonitor configuration and Prometheus query evidence for the app's `/metrics` endpoint.

## Screenshots

- [Grafana StatefulSet resources](docs/img/lab16_grafana_statefulset_resources.png)
- [Grafana node metrics](docs/img/lab16_grafana_node_metrics.png)
- [Grafana kubelet dashboard](docs/img/lab16_grafana_kubelet.png)
- [Alertmanager active alerts](docs/img/lab16_alertmanager_alerts.png)
- [Prometheus application metrics](docs/img/lab16_prometheus_app_metrics.png)

## Current Results

- Monitoring stack: `monitoring` Helm release on kube-prometheus-stack `84.5.0`.
- App release: existing `lab15` StatefulSet release upgraded with chart `devops-app-py` `0.8.0`.
- Init containers: `wait-for-headless-service` and `init-download`, both completed successfully.
- ServiceMonitor: `lab15-devops-app-py` in namespace `lab15`, labeled `release: monitoring`.
- Prometheus targets: six healthy app targets because both normal and headless Services match the ServiceMonitor selector.

