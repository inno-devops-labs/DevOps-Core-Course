# Lab 12 — ConfigMaps & Persistence

This document describes the implementation of configuration management and data persistence for the devops-app.

---

## 1. Application Changes

### Visits Counter Implementation

The application was updated to support persistent storage of visit counts.

* **Atomic Operations:** Implemented using a thread-safe `threading.Lock` and a temporary file-replace strategy (`os.replace`) to ensure data integrity during concurrent writes.
* **Path Configuration:** The database file path is configurable via the `VISITS_FILE` environment variable (default: `/data/visits`).

### New Endpoint

* **GET /visits** — Returns a JSON object with the total number of visits.

Example:

```json
{"count": 5}
```

### Local Testing Evidence

Tested using `docker-compose` with a local volume mapping:

```yaml
./data:/data
```

Steps:

```bash
docker compose up -d
curl http://localhost:8080/
docker compose restart
```

**Result:** The counter value was preserved in the `./data/visits` file after restart.

---

## 2. ConfigMap Implementation

### Template Structure

The ConfigMap is generated via Helm using:

```
templates/configmap.yaml
```

It provides two types of data:

* **File-based:** `config.json` containing application settings
* **Key-Value pairs:** Environment variables (`APP_NAME`, `LOG_LEVEL`)

### How It Is Mounted

* **As a File:** Mounted under `/config` using `volumes` and `volumeMounts` in `deployment.yaml`
* **As Environment Variables:** Injected using:

```yaml
envFrom:
  - configMapRef:
      name: devops-app-env
```

### Verification Commands

```bash
# Check ConfigMap presence
kubectl get configmap devops-app-env

# Verify file content inside the pod
kubectl exec <pod-name> -- cat /config/config.json

# Verify environment variables
kubectl exec <pod-name> -- printenv | grep APP_
```

---

## 3. Persistent Volume (PVC)

### Configuration

* **Name:** `devops-app-data` (aligned in both PVC and Deployment)
* **Access Mode:** `ReadWriteOnce (RWO)`
* **Storage Class:** Default cluster storage (e.g., `standard` in Minikube)

### Persistence Test Evidence

* **Initial State:**

```bash
curl <url>/visits
```

```json
{"count": 10}
```

* **Pod Deletion:**

```bash
kubectl delete pod -l app.kubernetes.io/instance=devops-app
```

* **Recovery:** Wait for a new pod to reach `Running` state.

* **Final State:**

```bash
curl <url>/visits
```

```json
{"count": 11}
```

**Result:** The counter value persisted after pod restart.

---

## 4. ConfigMap vs Secret

| Feature    | ConfigMap                          | Secret                                    |
| ---------- | ---------------------------------- | ----------------------------------------- |
| Purpose    | Non-sensitive configuration        | Sensitive data (passwords, tokens, certs) |
| Storage    | Plain text in etcd                 | Base64 encoded (often encrypted at rest)  |
| Visibility | Readable via `kubectl get -o yaml` | Requires decoding                         |
| Size Limit | 1MB                                | 1MB                                       |

**Recommendation:** Use ConfigMap for general configuration and Secret for sensitive data.

---

## 5. Verification Outputs

### kubectl get configmap,pvc

```bash
PS C:\Users\Bulat\OneDrive\Документы\GitHub\DevOps-Core-Course> kubectl get configmap,pvc
NAME                          DATA   AGE
configmap/devops-app-config   1      148m
configmap/devops-app-env      3      148m
configmap/kube-root-ca.crt    1      21d
configmap/vault-config        1      6d12h

NAME                                    STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-vault-0      Bound    pvc-ccad69ee-1423-4098-90c0-8fb9a594aa57   10Gi       RWO            standard       <unset>                 6d12h
persistentvolumeclaim/devops-app-data   Bound    pvc-8c48c5c7-2697-4b01-a678-664cf3b7b7ff   1Gi        RWO            standard       <unset>                 148m
```

### /config/config.json inside pod

```json
{
  "app_name": "python-devops-app",
  "log_level": "INFO"
}
```
