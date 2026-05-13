# File to remind myself about stuff

## SSH keys

### Outdated (doesn't use anywhere)
- terraform-vm-key (in ~/.ssh)

### Current
- devops-terraform-passwordless (two directories: uni/devops for terraform vm config and ~/.ssh for ansible and CI/CD)

## Ports

### Main stack
- app port: 1999
- container port: 12345

### Loki stack
- loki: 3100
- grafana: 3000
- promtail: 9080
- prometheus: 9090

```bash
# Test Loki
curl http://localhost:3100/ready

# Check Promtail targets
curl http://localhost:9080/targets

# Access Grafana
open http://localhost:3000
```

## VM commands

### ssh into vm
```bash
ssh -l ubuntu 93.77.189.231
```

### check curl

```bash
curl http://127.0.0.1:1999/health
curl http://127.0.0.1:1999/
```

## Local commands

### run app.py locally
```bash
python app.py
```

### kube stack

```bash
fountainer@Veronicas-MacBook-Air DevOps-Core-Course % helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
NAME: monitoring
LAST DEPLOYED: Sat May  2 22:35:24 2026
NAMESPACE: monitoring
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
kube-prometheus-stack has been installed. Check its status by running:
  kubectl --namespace monitoring get pods -l "release=monitoring"

Get Grafana 'admin' user password by running:

  kubectl --namespace monitoring get secrets monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 -d ; echo

Access Grafana local instance:

  export POD_NAME=$(kubectl --namespace monitoring get pod -l "app.kubernetes.io/name=grafana,app.kubernetes.io/instance=monitoring" -oname)
  kubectl --namespace monitoring port-forward $POD_NAME 3000

Get your grafana admin user password by running:

  kubectl get secret --namespace monitoring -l app.kubernetes.io/component=admin-secret -o jsonpath="{.items[0].data.admin-password}" | base64 --decode ; echo


Visit https://github.com/prometheus-operator/kube-prometheus for instructions on how to create & configure Alertmanager and Prometheus instances using the Operator.
```
