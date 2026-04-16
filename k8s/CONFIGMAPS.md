# ConfigMaps & Persistent Volumes – DevOps Info Service

## 1. Application Changes

### Visits Counter
- Added persistent visit counter stored in `/data/visits`.
- New endpoint `GET /visits` returns current count.
- Each request to `/` increments the counter.

### Local Testing with Docker Compose
```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
```

Test:
```bash
mkdir data
docker compose up -d
curl http://localhost:8000/          # increments
curl http://localhost:8000/visits     # returns {"visits":1}
docker compose restart
curl http://localhost:8000/visits     # still 1
```

---

## 2. ConfigMap Implementation

### File‑based ConfigMap
- **Source file:** `files/config.json`
- **Template:** `templates/configmap.yaml` uses `.Files.Get`
- **Mounted at:** `/config/config.json`

**`files/config.json`:**
```json
{
  "appName": "DevOps Info Service",
  "environment": "production",
  "features": {"visits": true, "metrics": true},
  "logLevel": "info"
}
```

### Environment Variable ConfigMap
- Keys: `APP_ENV`, `LOG_LEVEL`, `VISITS_ENABLED`
- Injected via `envFrom` in deployment.

**Verification:**
```bash
$ kubectl exec deployment/myapp-my-python-app -- cat /config/config.json
{...}

$ kubectl exec deployment/myapp-my-python-app -- printenv | grep -E "APP_ENV|LOG_LEVEL|VISITS_ENABLED"
APP_ENV=production
LOG_LEVEL=info
VISITS_ENABLED=true
```

---

## 3. Persistent Volume

### PVC Configuration
- **Size:** 100Mi
- **Access mode:** ReadWriteOnce
- **Storage class:** default (provided by minikube)

**`templates/pvc.yaml`** (simplified):
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "my-python-app.fullname" . }}-data
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
```

### Mounting in Deployment
```yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "my-python-app.fullname" . }}-data
containers:
  - volumeMounts:
      - name: data-volume
        mountPath: /data
```

### Persistence Test

```bash
# Create visits
$ for i in {1..5}; do curl http://$(minikube ip):30080/; done
$ curl http://$(minikube ip):30080/visits
{"visits": 5}

# Delete pod
$ kubectl delete pod myapp-my-python-app-xxxxx

# New pod starts automatically
$ kubectl get pods -w

# Check again
$ curl http://$(minikube ip):30080/visits
{"visits": 5}
```

✅ Data survives pod deletion.

---

## 4. ConfigMap vs Secret

| Feature          | ConfigMap                 | Secret                     |
|------------------|---------------------------|----------------------------|
| **Data**         | Plain text                | Base64‑encoded (encryptable at rest) |
| **Use case**     | Non‑sensitive config      | Passwords, tokens, certs   |
| **Size limit**   | 1 MiB                     | 1 MiB                      |
| **Mount as file**| Yes                       | Yes                        |
| **Auto‑update**  | Yes (with full directory) | Yes                        |

---

## 5. Bonus – ConfigMap Hot Reload

- **Default behaviour:** Mounted ConfigMap files are updated automatically after kubelet sync (≈60–120s).
- **`subPath` limitation:** Files mounted with `subPath` do **not** auto‑update.
- **Checksum annotation** forces pod restart on ConfigMap change:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

After `helm upgrade` with new config values, the pod restarts and picks up changes immediately.

---

## 6. Verification Commands Summary

```bash
# Check ConfigMaps and PVC
kubectl get configmap,pvc

# View mounted config file
kubectl exec deployment/myapp-my-python-app -- cat /config/config.json

# View environment variables from ConfigMap
kubectl exec deployment/myapp-my-python-app -- env | grep -E "APP_ENV|LOG_LEVEL"

# Test visits persistence
curl http://$(minikube ip):30080/visits
kubectl delete pod <pod-name>
curl http://$(minikube ip):30080/visits   # same value
```

---

## Conclusion

All requirements are satisfied:
- Application persists visit counter via PVC.
- Configuration externalised via two ConfigMaps (file + env vars).
- Data survives pod restarts.
- Documentation includes test outputs and analysis.