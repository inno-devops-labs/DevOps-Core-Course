# ConfigMaps & Persistent Volumes Documentation

## Application Changes

### Visits Counter Implementation
The application now includes a persistent visit counter that:
- Increments on each request to the root endpoint (`/`)
- Stores the counter in a file at `/data/visits`
- Provides a `/visits` endpoint to retrieve the current count
- Uses thread locking for concurrent access safety

### New Endpoints
- `GET /` - Returns welcome message and increments visit counter
- `GET /visits` - Returns current visit count
- `GET /health` - Health check with data directory status
- `GET /config` - Returns current application configuration

### Local Testing with Docker
```bash
# Start the application
cd monitoring
docker-compose up -d

# Test endpoints
% curl http://localhost:8000/
{"checks":{"config_loaded":"/app/config/config.json","data_writable":true,"visits_file_exists":false},"status":"healthy","timestamp":"2026-04-16T13:05:02.004757+00:00","uptime_seconds":100}

% curl http://localhost:8000/visits
{"data_file":"/data/visits.txt","total_visits":1,"tracking_enabled":true}

% curl http://localhost:8000/health
{"checks":{"config_loaded":"/app/config/config.json","data_writable":true,"visits_file_exists":false},"status":"healthy","timestamp":"2026-04-16T13:06:13.307770+00:00","uptime_seconds":171}

# Verify persistence
% docker-compose restart app-python

% curl http://localhost:8000/visits 
{"data_file":"/data/visits.txt","total_visits":1,"tracking_enabled":true}
```

## ConfigMap Implementation
### File-Based ConfigMap

The configuration is stored in `mychart/files/config.json` and mounted as a file:
```json
{
  "app_name": "DevOps Python Application",
  "environment": "production",
  "features": {
    "visits_counter": true,
    "logging_enabled": true
  }
}
```

### Environment Variables ConfigMap
Key-value pairs are injected as environment variables:

- `APP_ENV=production`

- `LOG_LEVEL=INFO`

- `APP_NAME=DevOps Python App`

### Verification
```bash
# Check ConfigMaps
 % kubectl get configmap -n devops
NAME                        DATA   AGE
kube-root-ca.crt            1      14m
my-release-mychart-config   1      14m
my-release-mychart-env      4      14m

# Verify mounted file
% kubectl exec -n devops my-release-mychart-66db5b94bd-57cr7 -- cat /app/config/config.json
{
  "app_name": "DevOps Python Application",
  "environment": "production",
  "version": "1.0.0",
  "features": {
    "visits_counter": true,
    "logging_enabled": true,
    "metrics_enabled": false
  },
  "settings": {
    "max_visits_display": 1000000,
    "refresh_interval_seconds": 30
  }
}% 

# Check environment variables
% kubectl exec -n devops my-release-mychart-66db5b94bd-57cr7 -- printenv | grep -E "APP_LOG_LEVEL"                                        APP_ENV=production
APP_NAME=DevOps Python App
LOG_LEVEL=INFO
```

## Persistent Volume Implementation

### PVC Configuration
```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""
  accessMode: ReadWriteOnce
```

### Volume Mount
The PVC is mounted at `/data` in the container, where the application writes the visits counter file.

### Persistence Test Results
**Before pod deletion:**
```bash
% kubectl exec my-release-mychart-xxx -- cat /data/visits
2

% curl http://localhost:8000/visits
{
  "data_file": "/data/visits.txt",
  "total_visits": 2,
  "tracking_enabled": true
}
```

**Delete pod**
```bash
% kubectl delete pod  my-release-mychart-5b8fc577b7-fjx6d -n devops
pod "my-release-mychart-5b8fc577b7-fjx6d" deleted from devops namespace
```

**After new pod starts**
```bash
% kubectl get pods -n devops
NAME                                  READY   STATUS    RESTARTS   AGE
my-release-mychart-5b8fc577b7-x57m2   1/1     Running   0          38s

% curl http://localhost:8000/visits
{"data_file":"/data/visits.txt","total_visits":2,"tracking_enabled":true}
```

**PVC status:**
```bash
% kubectl get pvc -n devops
NAME                      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
my-release-mychart-data   Bound    pvc-6a6fa3a9-a7a6-4ba8-af53-d1e3d21bf46d   100Mi      RWO            standard       <unset>                 105m
```

## ConfigMap vs Secret

| Aspect |	ConfigMap |	Secret |
|--------|------------|--------|
| Purpose |	Non-sensitive configuration data |	Sensitive data (passwords, tokens, keys) |
| Encoding |	Plain text |	Base64 encoded (not encrypted) |
| Size | Limit |	1MiB per object	1MiB per object |
| Use Cases |	Environment variables, config files, feature flags |	Credentials, API keys, TLS certificates |
| Security |	Can be viewed by anyone with access |	Data is obfuscated but not encrypted at rest | 
| etcd Storage | 	Stored in plain text |	Stored in plain text (base64) |
| Best Practice	| Use for configuration data | Use with encryption at rest enabled |

### When to use each:
**ConfigMap**: Application settings, feature flags, configuration files, environment names

**Secret**: Database passwords, API tokens, SSH keys, TLS certificates

## Verification Commands Summary
![check all resources](screenshots/lab12_screenshots/kubectl%20get%20configmap,%20pvc.png)

```bash
# Verify ConfigMap mounting
% kubectl describe configmap my-release-mychart-config -n devops
Name:         my-release-mychart-config
Namespace:    devops
Labels:       app.kubernetes.io/instance=my-release
              app.kubernetes.io/managed-by=Helm
              app.kubernetes.io/name=mychart
              app.kubernetes.io/version=1.0.0
              helm.sh/chart=mychart-0.1.0
Annotations:  meta.helm.sh/release-name: my-release
              meta.helm.sh/release-namespace: devops

Data
====
config.json:
----
{
  "app_name": "DevOps Python Application",
  "environment": "production",
  "version": "1.0.0",
  "features": {
    "visits_counter": true,
    "logging_enabled": true,
    "metrics_enabled": false
  },
  "settings": {
    "max_visits_display": 1000000,
    "refresh_interval_seconds": 30
  }
}

BinaryData
====

Events:  <none>

```bash
 % kubectl describe configmap my-release-mychart-env -n devops
Name:         my-release-mychart-env
Namespace:    devops
Labels:       app.kubernetes.io/instance=my-release
              app.kubernetes.io/managed-by=Helm
              app.kubernetes.io/name=mychart
              app.kubernetes.io/version=1.0.0
              helm.sh/chart=mychart-0.1.0
Annotations:  meta.helm.sh/release-name: my-release
              meta.helm.sh/release-namespace: devops

Data
====
APP_ENV:
----
production

APP_NAME:
----
DevOps Python App

LOG_LEVEL:
----
INFO

PYTHONUNBUFFERED:
----
1


BinaryData
====

Events:  <none>
```

```bash
# Verify PVC binding
% kubectl describe pvc my-release-mychart-data -n devops
Name:          my-release-mychart-data
Namespace:     devops
StorageClass:  standard
Status:        Bound
Volume:        pvc-6a6fa3a9-a7a6-4ba8-af53-d1e3d21bf46d
Labels:        app.kubernetes.io/instance=my-release
               app.kubernetes.io/managed-by=Helm
               app.kubernetes.io/name=mychart
               app.kubernetes.io/version=1.0.0
               helm.sh/chart=mychart-0.1.0
Annotations:   meta.helm.sh/release-name: my-release
               meta.helm.sh/release-namespace: devops
               pv.kubernetes.io/bind-completed: yes
               pv.kubernetes.io/bound-by-controller: yes
               volume.beta.kubernetes.io/storage-provisioner: k8s.io/minikube-hostpath
               volume.kubernetes.io/storage-provisioner: k8s.io/minikube-hostpath
Finalizers:    [kubernetes.io/pvc-protection]
Capacity:      100Mi
Access Modes:  RWO
VolumeMode:    Filesystem
Used By:       my-release-mychart-5b8fc577b7-x57m2
Events:        <none>
```

```bash
# Test application endpoints
% curl http://localhost:8000/
{"endpoints":[{"description":"Service information with visit counter","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"},{"description":"Prometheus metrics","method":"GET","path":"/metrics"},{"description":"Readiness probe","method":"GET","path":"/ready"},{"description":"Get current visit count","method":"GET","path":"/visits"},{"description":"Show current configuration","method":"GET","path":"/config"}],"request":{"client_ip":"127.0.0.1","method":"GET","path":"/","user_agent":"curl/8.7.1"},"runtime":{"current_time":"2026-04-16T15:00:34.533576+00:00","timezone":"UTC","uptime_human":"0 hours, 14 minutes","uptime_seconds":890},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu-count":8,"hostname":"my-release-mychart-5b8fc577b7-x57m2","platform":"Linux","platform-version":"#1 SMP PREEMPT Thu Nov 20 09:34:02 UTC 2025","python-version":"3.13.13"},"visits":{"message":"Welcome to DevOps Info Service!","total":3}}
```

```bash
% curl http://localhost:8000/visits
{"data_file":"/data/visits.txt","total_visits":3,"tracking_enabled":true}
```

```bash
% curl http://localhost:8000/config
{"app_name":"DevOps Python Application","config_file":"/app/config/config.json","data_dir":"/data","environment":"production","features":{"logging_enabled":true,"metrics_enabled":false,"visits_counter":true},"log_level":"INFO"}
```

```bash
 % curl http://localhost:8000/health
{"checks":{"config_loaded":"/app/config/config.json","data_writable":true,"visits_file_exists":true},"status":"healthy","timestamp":"2026-04-16T15:01:14.620055+00:00","uptime_seconds":930}
```
    