# Lab 11 Implementation Report

## 1. Kubernetes Secrets
### Creation and Viewing
Command to create secret:
```bash
kubectl create secret generic app-credentials --from-literal=username=admin --from-literal=password=supersecret
```

YAML Output (Sanitized):
```yaml
apiVersion: v1
data:
  password: c3VwZXJzZWNyZXRwYXNzd29yZA==
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T14:12:10Z"
  name: app-credentials
  namespace: default
  resourceVersion: "102511"
  uid: 1b45b668-7f45-4428-b8c9-6319c5ce0e76
type: Opaque
```

### Decoding
```bash
echo "c3VwZXJzZWNyZXRwYXNzd29yZA==" | base64 -d
supersecretpassword
```

### Security Analysis: Encoding vs Encryption
- **Base64 Encoding:** This is a data representation format, NOT encryption. It is easily reversible by anyone with access to the secret object.
- **Encryption at Rest:** By default, Kubernetes stores secrets in `etcd` as plain text (or base64). To secure them, **etcd encryption** must be enabled at the cluster level so that the data is encrypted before being written to disk.

---

## 2. Helm Secret Integration

### Chart Structure
```text
k8s/my-python-app/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── deployment.yaml
    ├── secrets.yaml       <-- New
    └── ...
```

### Configuration
**`templates/secrets.yaml`**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "my-python-app.fullname" . }}-credentials
  labels:
    {{- include "my-python-app.labels" . | nindent 4 }}
type: Opaque
data:
  username: {{ .Values.secrets.username | b64enc | quote }}
  password: {{ .Values.secrets.password | b64enc | quote }}
```

**`values.yaml`**
```yaml
secrets:
  username: "admin"
  password: "supersecretpassword"

resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "200m"
```

**`templates/deployment.yaml`**
```yaml
spec:
  template:
    spec:
      containers:
        - name: {{ .Chart.Name }}
          envFrom:
            - secretRef:
                name: {{ include "my-python-app.fullname" . }}-credentials
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

### Verification
```bash
kubectl exec -it myapp2-my-python-app-67d6866844-8z225 -- printenv | grep -E 'username|password'
password=supersecretpassword
username=admin
```

---

## 3. Resource Management
- **Requests:** The minimum resources guaranteed to the container. Used by the scheduler to place pods.
- **Limits:** The maximum resources a container is allowed to consume. If a container hits its memory limit, it is OOMKilled.

---

## 4. Vault Integration

### Vault Installation
```bash
helm upgrade --install vault /tmp/vault-helm --set "server.dev.enabled=true" --set "injector.enabled=true" --wait --timeout 300s
Release "vault" does not exist. Installing it now.
NAME: vault
LAST DEPLOYED: Thu Apr  9 18:03:54 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
NOTES:
Thank you for installing HashiCorp Vault!
```
Verification:
```bash
kubectl get po
NAME                                    READY   STATUS    RESTARTS        AGE
myapp2-my-python-app-67c4f78976-5wvpr   1/1     Running   0               24m
vault-0                                 1/1     Running   0               82s
vault-agent-injector-85857876c6-djjwq   1/1     Running   0               82s
```

### Vault Agent Injection
**Deployment Annotations:**
```yaml
metadata:
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/role: "myapp-role"
    vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
```

### Proof of Injection
```bash
kubectl exec -it myapp2-my-python-app-67d6866844-8z225 -- ls /vault/secrets/
total 8
drwxrwxrwt 2 root root   60 Apr  9 21:35 .
drwxr-xr-x 3 root root 4096 Apr  9 21:35 ..
-rw-r--r-- 1  100 1000   47 Apr  9 21:35 config
```

```bash
kubectl exec -it myapp2-my-python-app-67d6866844-8z225 -- cat /vault/secrets/config
USERNAME=admin
PASSWORD=supersecretpassword
```
---

## 5. Security Analysis Summary

| Feature | Kubernetes Secrets | HashiCorp Vault |
|---------|--------------------|------------------|
| **Storage** | etcd (needs encryption enabled) | Encrypted storage engine |
| **Complexity** | Low (Native) | Medium/High (Requires setup) |
| **Lifecycle** | Manual/Helm managed | Dynamic rotation & TTL support |
| **Access** | RBAC on K8s API | Granular policies & Auth methods |

**Recommendation:**
- Use **Kubernetes Secrets** for non-sensitive environment configs or when low complexity is required in small clusters.
- Use **HashiCorp Vault** for production environments requiring dynamic secrets, automatic rotation, and centralized auditing across multiple clusters/clouds.
