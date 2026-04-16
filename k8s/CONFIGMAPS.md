# Lab 12: ConfigMaps & Persistent Volumes

## 1. Application Changes

### Visits Counter
I extended the `app.py` in the `pythonapp` to include a file-based counter logic:
- Reads the counter from `/data/visits` (using the `$DATA_DIR` environment variable, defaulting to `./data`).
- Increments the value and saves it synchronously during each hit to the root `/` endpoint.
- Returns the current visit count from `/visits` endpoint cleanly as `{"visits":<count>}`.

Local testing logic with Docker Compose was added to `docker-compose.yml` to verify persistence outside of Kubernetes, using host volumes.

## 2. ConfigMap Implementation

A new ConfigMap handling file mounts inside the pod was introduced. Load the local file `files/config.json` via Helm templating:

### ConfigMap Template (File)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "pythonapp.fullname" . }}-config
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}
```

```
$ kubectl exec pythonapp-dev-pythonapp-599755bcd8-snhfx -c pythonapp -- cat /config/config.json
{"app_name": "pythonapp", "environment": "dev", "feature_flags": {"new_ui": true}}
```

### ConfigMap Template (Env Variables)

**Mapping inside Pod via `envFrom: configMapRef`:**
```
$ kubectl exec pythonapp-dev-pythonapp-599755bcd8-snhfx -c pythonapp -- printenv | Select-String "APP_ENV|LOG_LEVEL"
APP_ENV=dev
LOG_LEVEL=INFO
```

The application logic mounts the Code file directly by leveraging `subPath` ConfigMap mounts. This let me bypass PyPI SSL timeout issues on the host.

## 3. Persistent Volume Implementation

To guarantee the visits counter does not reset back to 0 on a pod restart, a PersistentVolumeClaim (PVC) was requested:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "pythonapp.fullname" . }}-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Mi
```

### Storage Persistence Test

**Step 1. Increment Data via endpoints:**
```
$ kubectl exec $podName -c pythonapp -- python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')"
$ kubectl exec $podName -c pythonapp -- python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')"
```

**Step 2. Verify Count inside Pod A:**
```
$ kubectl exec $podName -c pythonapp -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000/visits').read().decode())"
{"visits":2}
```

**Step 3. Induce Pod restart:**
```
$ kubectl delete pod pythonapp-dev-pythonapp-599755bcd8-tpslj
pod "pythonapp-dev-pythonapp-599755bcd8-tpslj" deleted from default namespace
```

**Step 4. Read Data post-respawn inside Pod B:**
```
$ kubectl exec pythonapp-dev-pythonapp-599755bcd8-nv4zx -c pythonapp -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000/visits').read().decode())"
{"visits":2}
```


## 4. ConfigMap vs Secret

**ConfigMaps**
- Plaintext configuration suitable for generic properties (Log Levels, System flags, Environment indicators).
- Viewable completely natively by anyone with basic access unless restricted arbitrarily by cluster roles.
- Great for mounting application code directly (like in this lab) to dynamically change behavior without rebuilding a new container image!

**Secrets**
- Base-64 Encoded (or stored internally encrypted) objects suitable for API Keys, Passwords and highly sensitive metrics.
- Should ideally be sourced via an External Secrets proxy like Hashicorp Vault to limit Kubernetes cluster explosion radii.
