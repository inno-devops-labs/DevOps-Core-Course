# Lab 12 — ConfigMaps & Persistent Volumes

## 1. Application Changes

The application was updated to support a persistent visits counter.

### Changes:
- A visits counter is stored in `/data/visits`
- Each request to `/` increments the counter
- A new endpoint `/visits` returns the current counter
- The file is read on startup (default = 0 if not exists)

### Endpoints:
- `GET /` — increments visits counter
- `GET /visits` — returns current visits count

### Local Docker Test

```bash
docker run --rm -p 5000:5000 -v "$(pwd)/data:/data" fayzullin/devops-info-service:latest
```

### Verification:

Counter increased after requests
Value persisted after container restart

## 2. ConfigMap Implementation
File-based ConfigMap

Config file:

{
  "appName": "devops-info-service",
  "environment": "dev",
  "featureFlag": true
}

Mounted inside pod:

```bash
kubectl exec -it <pod> -- cat /config/config.json
```

Output:

{
  "appName": "devops-info-service",
  "environment": "dev",
  "featureFlag": true
}
Environment Variables via ConfigMap
kubectl exec -it <pod> -- printenv | grep APP_
kubectl exec -it <pod> -- printenv | grep LOG_LEVEL

Output:

APP_ENV=dev
LOG_LEVEL=debug

## 3. Persistent Volume

### PVC

```bash
kubectl get pvc
```

Output:

lab12-release-devops-info-service-data   Bound   100Mi   RWO
Volume Mount

PVC is mounted at:

/data
Persistence Verification

Before pod restart:

cat /data/visits

Output:

2

After pod recreation:

kubectl delete pod <pod>
kubectl get pods
kubectl exec -it <new-pod> -- cat /data/visits

Output:

2

After new request:

curl localhost:8080/visits

Output:

{"visits":3}

✅ Data persisted across pod restart

## 4. ConfigMap vs Secret
ConfigMap	Secret
Non-sensitive data	Sensitive data
App config	Passwords, tokens
Plain text	Base64 encoded
Example: APP_ENV	Example: DB_PASSWORD

## 5. Summary

In this lab:

ConfigMaps were used for configuration (file + env vars)
PersistentVolumeClaim was used for data storage
Application data persisted across pod restarts
/visits endpoint confirmed correct behavior

The application is now production-ready with:

externalized configuration
persistent storage
