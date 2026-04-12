# Lab 12 — ConfigMaps & Persistent Volumes



## Application Changes

### Visits counter implementation

- File-based storage with locks for atomicity
- At startup, read from the file, if there is no file, create
- Each request to "/" increments the counter
- New endpoint "/visits" to view
- Docker volume for persistence between restarts

### Local testing evidence with Docker

```bash
 curl http://localhost:5050/
```

```bash
...
"visits": {
    "total": 7
}
```

```bash
 curl http://localhost:5050/
```

```bash
...
"visits": {
    "total": 8
}
```



## ConfigMap Implementation

### ConfigMap template structure

```bash
kubectl get configmap config-demo-info-service-config -o yaml
```

```yaml
apiVersion: v1
data:
  config.json: |
    {
      "app": {
        "name": "info-service",
        "environment": "development",
        "version": "1.0.0",
        "debug": true
      },
      "features": {
        "enable_vault": false,
        "enable_metrics": true,
        "enable_visits": true,
        "enable_secrets_endpoint": true
      },
      "logging": {
        "level": "INFO",
        "format": "json"
      }
    }
kind: ConfigMap
metadata:
  name: config-demo-info-service-config
```

### config.json content

```bash
cat config.json
```

```yaml
{
    "app": {
        "name": "info-service",
        "environment": "{{ .Values.environment }}",
        "version": "1.0.0",
        "debug": {
            { .Values.debug | default false}
        }
    },
    "features": {
        "enable_vault": {
            { .Values.vault.enabled | default false}
        },
        "enable_metrics": true,
        "enable_visits": true,
        "enable_secrets_endpoint": {
            { .Values.debug | default false}
        }
    },
    "logging": {
        "level": "{{ .Values.logLevel | default "INFO" }}",
        "format": "json"
    },
    "limits": {
        "max_visits_file_size": 1048576,
        "request_timeout": 30
    },
    "endpoints": {
        "health": "/health",
        "metrics": "/metrics",
        "visits": "/visits",
        "secrets": "/secrets"
    }
}
```

### ConfigMap file

- Stores structured configuration in JSON
- Is mounted as a file in `/config/config.json`
- The application can read and parse JSON
- Allows complex nested configuration

### Env ConfigMap

- Stores simple key-value pairs
- Injected via envFrom
- Convenient for 12-factor apps
- Easy to redefine via `values.yaml`

### Verification

```bash
kubectl get configmap config-demo-info-service-env -o yaml
```

```bash
apiVersion: v1
data:
  APP_NAME: "info-service-dev"
  CONFIG_PATH: "/config/config.json"
  LOG_LEVEL: "INFO"
  VAULT_ENABLED: "false"
  VISITS_FILE: "/data/visits.txt"
kind: ConfigMap
```

```bash
kubectl exec $POD_NAME -- cat /config/config.json
```

```bash
{
  "app": {
    "name": "info-service",
    "environment": "development",
    "version": "1.0.0",
    "debug": true
  },
  "features": {
    "enable_vault": false,
    "enable_metrics": true,
    "enable_visits": true,
    "enable_secrets_endpoint": true
  },
  "logging": {
    "level": "INFO",
    "format": "json"
  }
}
```

```bash
kubectl exec $POD_NAME -- env | grep -E "APP_NAME|LOG_LEVEL|CONFIG"
```

```bash
APP_NAME=info-service-dev
LOG_LEVEL=INFO
CONFIG_PATH=/config/config.json
```



## Persistent Volume

### PVC configuration

- **Storage request**: 100Mi
- **Access mode**: ReadWriteOnce
- Automatically connects to PV via storage class

### Access modes and storage class

- **ReadWriteOnce (RWO)**: one node read/write
- **ReadOnlyMany (ROX)**: many nodes read-only
- **ReadWriteMany (RWX)**: multiple read/write nodes

### Volume mount configuration

```bash
kubectl describe pvc pvc-demo-info-service-data
```

```bash
Name:          pvc-demo-info-service-data
Namespace:     default
StorageClass:  standard
Status:        Bound
Volume:        pvc-12345678-1234-1234-1234-123456789abc
Labels:        app.kubernetes.io/instance=pvc-demo
               app.kubernetes.io/name=info-service
Access Modes:  RWO
Capacity:      100Mi
```

### Persistence test evidence:

- Counter value before pod deletion

```bash
 curl http://localhost:5050/
```

```bash
...
"visits": {
    "total": 12
}
```

- Pod deletion command

```bash
kubectl delete pod $POD_NAME
```

```bash
pod "pvc-demo-info-service-6b4f9c5d8b-4k5jv" deleted
```

- Counter value after new pod starts

```bash
 curl http://localhost:5050/
```

```bash
...
"visits": {
    "total": 12
}
```

### `kubectl get configmap,pvc`

```bash
NAME                                               DATA   AGE
configmap/config-demo-info-service-config          1      11m
configmap/config-demo-info-service-env             5      11m
configmap/kube-root-ca.crt                         1      2d
```

## ConfigMap vs Secret

### When to use ConfigMap

- Non-sensitive configuration data
- Configuration files
- Environment variables for 12-factor applications
- Settings that change between environments

### When to use Secret

- Passwords and credentials
- API keys and tokens
- TLS certificates
- Encryption keys
- Credentials for external services

### Key differences

| Characteristic | ConfigMap | Secret |
|----------------|-----------|--------|
| Storage | Plain text data | Sensitive data |
| Encryption | Not encrypted | Can be encrypted |
| Size | Up to 1MB | Up to 1MB |
| RBAC | Regular access rights | Strict access control |
| Audit | Not logged | Access can be logged |
| Visibility | `kubectl get` shows data | `kubectl get` shows only names |
| Updates | Can be updated without pod restart | Requires pod restart |
| Use Cases | Configs, settings, features | Passwords, tokens, keys, certificates |
| Values | Any characters | Base64 encoded |
| In Pods | As files or env vars | As files or env vars |



## ConfigMap Hot Reload 

### subPath limitation

```yaml
# With subPath mounting
volumeMounts:
- name: config
  mountPath: /config/config.json
  subPath: config.json  # Does not update automatically

# Without subPath mounting
volumeMounts:
- name: config
  mountPath: /config  # Updates automatically
```

### Reload approach implementation

```bash
# Before changing
kubectl exec hotreload-demo-info-service-5a3e8b4c7a-3j4iu -- cat /config/config.json | jq '.app.environment'
```

```bash
# Before changing
"development"
```

```bash
# Changing the config and making a helm upgrade
sed -i 's/development/staging/' files/config.json
helm upgrade hotreload-demo ./info-service-chart
```

```bash
# After changing
kubectl exec hotreload-demo-info-service-7c5g0d6e9c-5l6kw -- cat /config/config.json | jq '.app.environment'
```

```bash
# After changing
"staging"
```

### Update delay measurement

Just wait and check the changes
