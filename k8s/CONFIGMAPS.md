# Lab 12 — ConfigMaps & Persistent Volumes

## Application Changes

### Description of visits counter implementation

- Added visits counter:
    - File to save count `./data/visits`
    - Every `/` visit increments count
    - Incremented count saves to file
    - Every app start gets current count of visits
- New path `/visits` to show count of visits

### New endpoint documentation

Endpoint:
```
GET /visits
```

Returns:
```
{"visits": n}
```

### Local testing evidence with Docker

Volume from `docker-compose.yml`:
```
./data:/data
```

After docker start
```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl 127.0.0.1:5000
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"},{"description":"Endpoint that raises an error for testing","method":"GET","path":"/raise-error"},{"description":"Metrics endpoint","method":"GET","path":"/metrics"}],"request":{"client_ip":"172.20.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-04-09T12:18:06.253144+00:00","timezone":"UTC","uptime_human":"0.0h 0.0m","uptime_seconds":29.862655},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"1f899ade0e9b","platform":"Linux","platform_version":"#1 SMP Tue Nov 5 00:21:55 UTC 2024","python_version":"3.12.13"}}

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl 127.0.0.1:5000
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"},{"description":"Endpoint that raises an error for testing","method":"GET","path":"/raise-error"},{"description":"Metrics endpoint","method":"GET","path":"/metrics"}],"request":{"client_ip":"172.20.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-04-09T12:18:07.449712+00:00","timezone":"UTC","uptime_human":"0.0h 0.0m","uptime_seconds":31.059223},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"1f899ade0e9b","platform":"Linux","platform_version":"#1 SMP Tue Nov 5 00:21:55 UTC 2024","python_version":"3.12.13"}}

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl 127.0.0.1:5000
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"},{"description":"Endpoint that raises an error for testing","method":"GET","path":"/raise-error"},{"description":"Metrics endpoint","method":"GET","path":"/metrics"}],"request":{"client_ip":"172.20.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-04-09T12:18:08.305313+00:00","timezone":"UTC","uptime_human":"0.0h 0.0m","uptime_seconds":31.914824},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"1f899ade0e9b","platform":"Linux","platform_version":"#1 SMP Tue Nov 5 00:21:55 UTC 2024","python_version":"3.12.13"}}

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl 127.0.0.1:5000/visits
{"visits":3}
```

After restart container
```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl 127.0.0.1:5000/visits
{"visits":3}
```

## ConfigMap Implementation

### `config.json` content

```json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsCount": true
  }
}
```

### How ConfigMap is mounted as file

In `deployment.yaml` added `volumes` and `volumeMounts`:
```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
  - name: data-volume
    mountPath: /data

volumes:
  - name: config-volume
    configMap:
      name: {{ include "devops-info-service.fullname" . }}-config
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "devops-info-service.fullname" . }}-data
```

### How ConfigMap provides environment variables

In `deployment.yaml` into `envFrom` added `configMapRef`:
```yaml
- configMapRef:
    name: {{ include "devops-info-service.fullname" . }}-env
```

### Verification outputs

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm upgrade --install app ./k8s/devops-info-service-chart --namespace dev --create-namespace
Release "app" does not exist. Installing it now.
devops-info-serviceNAME: app      
LAST DEPLOYED: Sat Apr 11 17:24:05 2026
NAMESPACE: dev
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing devops-info-service.

Release: app
Namespace: dev

Your application should expose:
- GET /
- GET /health

Useful commands:
        kubectl get pods -n dev
        kubectl get svc -n dev
Service type is NodePort.

Access options:
1. Minikube:
         minikube service app-devops-info-service -n dev --url

2. Manual NodePort access:
         export NODE_PORT=$(kubectl get svc app-devops-info-service -n dev -o jsonpath='{.spec.ports[0].nodePort}')
         export NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
         echo "http://${NODE_IP}:${NODE_PORT}/"
         curl -i "http://${NODE_IP}:${NODE_PORT}/health"

Troubleshooting:
        kubectl describe deployment app-devops-info-service -n dev
        kubectl logs -n dev deployment/app-devops-info-service



Required Sections:

Chart Overview

Chart structure explanation
Key template files and their purpose
Values organization strategy


Configuration Guide

Important values and their purpose
How to customize for different environments
Example installations with different configurations


Hook Implementation

What hooks you implemented and why
Hook execution order and weights
Deletion policies explanation


Installation Evidence

helm list output
kubectl get all showing deployed resources
Hook execution output (kubectl get jobs, kubectl describe job)
Different environment deployments (dev vs prod)


Operations

Installation commands used
How to upgrade a release
How to rollback
How to uninstall


Testing & Validation

helm lint output
helm template verification
Dry-run output
Application accessibility verification


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ export POD_NAME=$(kubectl get pods --namespace dev -l "app.kubernetes.io/name=devops-info-service,app.kubernetes.io/instance=app" -o jsonpath="{.items[0].metadata.name}")


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get configmap,pvc --namespace dev
NAME                                       DATA   AGE
configmap/app-devops-info-service-config   1      11m
configmap/app-devops-info-service-env      2      11m
configmap/kube-root-ca.crt                 1      11m

NAME                                                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/app-devops-info-service-data   Bound    pvc-7b634a81-466c-4657-84c4-0619f3a7efaa   100Mi      RWO            standard       <unset>                 11m


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl exec -it $POD_NAME --namespace dev -- cat /config/config.json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsCount": true
  }
}


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl exec -it $POD_NAME --namespace dev -- printenv | grep APP_
APP_PASSWORD=password_for_DevOps
APP_USERNAME=chal
APP_ENV=dev
APP_DEVOPS_INFO_SERVICE_PORT_80_TCP_ADDR=10.101.156.249
APP_DEVOPS_INFO_SERVICE_SERVICE_PORT=80
APP_DEVOPS_INFO_SERVICE_PORT_80_TCP=tcp://10.101.156.249:80
APP_DEVOPS_INFO_SERVICE_SERVICE_HOST=10.101.156.249
APP_DEVOPS_INFO_SERVICE_PORT=tcp://10.101.156.249:80
APP_DEVOPS_INFO_SERVICE_PORT_80_TCP_PROTO=tcp
APP_DEVOPS_INFO_SERVICE_PORT_80_TCP_PORT=80
```

## Persistent Volume

### PVC configuration

`pvc.yaml`:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "devops-info-service.fullname" . }}-data
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
  {{- if .Values.persistence.storageClass }}
  storageClassName: {{ .Values.persistence.storageClass }}
  {{- end }}
```

`values.yaml`:
```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""
```

### Access modes and storage class discussion

*   **`accessModes: [ReadWriteOnce]`**: Volume can be mounted for reading and writing by only one node in the cluster..

*   **`storageClassName`**: ЭThis parameter determines which type of physical storage will be used. In this case, `StorageClass` is used by default (in MiniKube it is usually standard)

### Volume mount configuration

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
  - name: data-volume
    mountPath: /data

volumes:
  - name: config-volume
    configMap:
      name: {{ include "devops-info-service.fullname" . }}-config
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "devops-info-service.fullname" . }}-data
```

### Persistence test evidence

#### Counter value before pod deletion

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl 127.0.0.1:5000
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"},{"description":"Endpoint that raises an error for testing","method":"GET","path":"/raise-error"},{"description":"Metrics endpoint","method":"GET","path":"/metrics"}],"request":{"client_ip":"172.20.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-04-09T12:18:06.253144+00:00","timezone":"UTC","uptime_human":"0.0h 0.0m","uptime_seconds":29.862655},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"1f899ade0e9b","platform":"Linux","platform_version":"#1 SMP Tue Nov 5 00:21:55 UTC 2024","python_version":"3.12.13"}}

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl 127.0.0.1:5000
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"},{"description":"Endpoint that raises an error for testing","method":"GET","path":"/raise-error"},{"description":"Metrics endpoint","method":"GET","path":"/metrics"}],"request":{"client_ip":"172.20.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-04-09T12:18:07.449712+00:00","timezone":"UTC","uptime_human":"0.0h 0.0m","uptime_seconds":31.059223},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"1f899ade0e9b","platform":"Linux","platform_version":"#1 SMP Tue Nov 5 00:21:55 UTC 2024","python_version":"3.12.13"}}

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl 127.0.0.1:5000
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"},{"description":"Endpoint that raises an error for testing","method":"GET","path":"/raise-error"},{"description":"Metrics endpoint","method":"GET","path":"/metrics"}],"request":{"client_ip":"172.20.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-04-09T12:18:08.305313+00:00","timezone":"UTC","uptime_human":"0.0h 0.0m","uptime_seconds":31.914824},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"1f899ade0e9b","platform":"Linux","platform_version":"#1 SMP Tue Nov 5 00:21:55 UTC 2024","python_version":"3.12.13"}}

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl 127.0.0.1:5000/visits
{"visits":3}
```

#### Pod deletion command

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ export POD_NAME=$(kubectl get pods --namespace dev -l "app.kubernetes.io/name=devops-info-service,app.kubernetes.io/instance=app" -o jsonpath="{.items[0].metadata.name}")

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl delete pod $POD_NAME --namespace dev
pod "app-devops-info-service-6ddd959fbf-2w62z" deleted from dev namespace
```

#### Counter value after new pod starts

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl 127.0.0.1:5000/visits
{"visits":3}
```

## ConfigMap vs Secret

### When to use ConfigMap

**ConfigMap** is used to store non-confidential settings as key-value pairs. 

For example:
- `Logging level`: INFO
- `API url`: http://localhost:8496/api

### When to use Secret

**Secret** is designed for storing and managing secret data. Secrets are stored as encoded/encrypted data.

For example:
- Password
- Tokens

### Key differences

| Characteristic | ConfigMap | Secret |
| ---- | ---- | ---- |
| **Purpose** | Non-confidential configuration | Confidential data |
| **Storage** | Plaintext | Base64 by default, but can be encrypted |
| **Security** | Data is visible to everyone | Data is hidden |