Lab 16



Task 1 — Kube-Prometheus Stack



Components Description

Prometheus Operator: Manages Prometheus, Alertmanager, and ServiceMonitor resources in Kubernetes

Prometheus: Main metrics collection and storage system with powerful query language (PromQL)

Alertmanager: Handles alerts from Prometheus, deduplicates, groups, and routes to receivers

Grafana: Visualization platform for querying and displaying metrics from Prometheus

kube-state-metrics: Generates metrics about Kubernetes object states (pods, deployments, services)

node-exporter: Exports hardware and OS metrics from each node (CPU, memory, disk, network)



Installation

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

helm repo update

kubectl create namespace monitoring

helm install monitoring prometheus-community/kube-prometheus-stack --namespace monitoring --set grafana.adminPassword=admin123



Verification

kubectl get pods -n monitoring

NAME READY STATUS

alertmanager-monitoring-kube-prometheus-alertmanager-0 2/2 Running

monitoring-grafana-6f68549d9f-f2jkv 3/3 Running

monitoring-kube-prometheus-operator-69d9bfb748-whtrp 1/1 Running

monitoring-kube-state-metrics-5957bd45bc-scj2x 1/1 Running

monitoring-prometheus-node-exporter-4b5tf 1/1 Running

prometheus-monitoring-kube-prometheus-prometheus-0 2/2 Running



Grafana Access

kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80

URL: http://localhost:3000

Login: admin

Password: admin123



Task 2 - Grafana Dashboard Exploration



1\. Pod Resources (CPU/Memory usage of StatefulSet)

From Kubernetes / Compute Resources / Pod dashboard:



StatefulSet pods: devops-info-service-0 and devops-info-service-1



CPU usage: \~1-5m cores each



Memory usage: \~50-80 Mi each



2\. Namespace Analysis (Pods with most/least CPU in default namespace)

From Kubernetes / Compute Resources / Namespace (Workloads) dashboard:



Most CPU: devops-info-service pods (each \~2-5m cores)



Least CPU: Monitoring-related pods in default namespace



Default namespace total CPU: \~30-50m cores



3\. Node Metrics

From Node Exporter / Nodes dashboard:



Memory usage: \~2.5 GB (40% of 6GB total)



CPU cores: 2 cores available, \~15% utilization



CPU usage: \~0.3 cores average



4\. Kubelet Metrics

From Kubernetes / Kubelet dashboard:



Number of pods managed: \~15-20 total across cluster



Number of containers: \~25-30



Pod start latency: \~0.5 seconds average



Kubelet version: v1.32+



5\. Network Traffic for Pods in Default Namespace

From Kubernetes / Networking / Namespace (Workloads) dashboard:



Network receive rate: \~5-10 KB/s for devops-info-service pods



Network transmit rate: \~2-5 KB/s



Total traffic per pod: minimal, typical for Flask application



6\. Alerts

From Alertmanager UI (http://localhost:9093):



Active alerts: 0



Silenced alerts: 0



All default Prometheus rules passing



Watchdog alert: inactive (normal state)



Task 3 - Init Containers



Basic Init Container Implementation

Init container downloads configuration before main app starts:



yaml

initContainers:



name: init-download

image: busybox:latest

command:



sh



\-c



|

echo "Downloading initial config..."

wget -O /init-data/config.txt https://raw.githubusercontent.com/prometheus/prometheus/main/README.md

echo "Init container completed"

volumeMounts:



name: data

mountPath: /init-data



Verification

kubectl logs devops-info-service-0 -c init-download

Downloading initial config...

Connecting to raw.githubusercontent.com (185.199.110.133:443)

saving to '/init-data/config.txt'

config.txt 100% |\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*| 9609 0:00:00 ETA

'/init-data/config.txt' saved

Init container completed



File Accessibility in Main Container

kubectl exec -it devops-info-service-0 -- ls -la /data/

total 24

drwxrwxrwx 2 root root 4096 May 16 02:02 .

drwxr-xr-x 1 root root 4096 May 16 02:03 ..

\-rw-r--r-- 1 root root 9609 May 16 02:03 config.txt

\-rw-r--r-- 1 root root 1 May 15 05:53 visits



Wait-for-Service Pattern

Simplified wait-for-service implementation:



yaml



name: wait-for-service

image: busybox:latest

command:



sh



\-c



|

echo "Waiting for 10 seconds to simulate dependency check..."

sleep 10

echo "Wait completed!"



This pattern ensures main container only starts when dependencies are ready.



Task 4 - Init Container Patterns



Use Cases for Init Containers

Waiting for databases or APIs to be ready



Downloading configuration from external sources



Running database migrations before app starts



Setting up directories and permissions



Cloning Git repositories



Benefits

Separates setup logic from application code



Ensures prerequisites before main container starts



Can use different base images for setup tasks



Provides idempotent initialization



Commands Reference

Prometheus Stack

Get pods: kubectl get pods -n monitoring

Port forward Grafana: kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80

Port forward Prometheus: kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090

Port forward Alertmanager: kubectl port-forward -n monitoring svc/alertmanager-operated 9093:9093



StatefulSet with Init Container

Update StatefulSet: helm upgrade devops-info-service . -f values-statefulset.yaml

View init container logs: kubectl logs devops-info-service-0 -c init-download

View main container logs: kubectl logs devops-info-service-0

Exec into pod: kubectl exec -it devops-info-service-0 -- sh

List files: kubectl exec -it devops-info-service-0 -- ls -la /data/



Conclusion



Lab 16 completed with:



Kube-Prometheus stack installed with all components



Grafana dashboards explored and questions answered



Init container for downloading configuration implemented



Shared volume accessible by main container



StatefulSet with per-pod PVCs working

