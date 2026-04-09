# Lab 11

## Output of creating and viewing your secret

```bash
~/Projects/DevOps-Core-Course$ kubectl create secret generic app-credentials \
  --from-literal=username='testuser' \
  --from-literal=password='testpassword'
secret/app-credentials created
bulatgazizov@fedora:~/Projects/DevOps-Core-Course$ kubectl get secret app-credentials -o yaml
apiVersion: v1
data:
  password: dGVzdHBhc3N3b3Jk
  username: dGVzdHVzZXI=
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T19:22:25Z"
  name: app-credentials
  namespace: default
  resourceVersion: "19710"
  uid: 8be33663-f705-443b-9367-9771044fa479
type: Opaque
bulatgazizov@fedora:~/Projects/DevOps-Core-Course$ 
bulatgazizov@fedora:~/Projects/DevOps-Core-Course$ echo dGVzdHBhc3N3b3Jk | base64 -d
testpasswordbulatgazizov@fedora:~/Projects/DevOps-Core-Course$ echo dGVzdHVzZXI= | base64 -d
testuser
```

- Encoding: reversible transformation to represent data (e.g., base64). Not intended to protect confidentiality; anyone who can read the encoded string can easily recover the original.
- Encryption: uses a key and algorithm to make data unreadable without the key. Designed to protect confidentiality and requires proper key management.

## Helm Secret Integration

### Chart structure showing secrets.yaml

```bash
Chart/
    Chart.yaml
    values.yaml
    templates/
        secrets.yaml
        deployment.yaml
        _helpers.tpl
```

### How secrets are consumed in deployment

Using envFrom (all keys)

```yaml
containers:
...
    envFrom:
      - secretRef:
          name: {{ include "mychart.fullname" . }}-credentials
```

### Verification output (env vars in pod, excluding actual values)

```bash
kubectl exec myapp-mychart-69bdcbddc7-cmqx4  -it -- printenv
password=***
username=***
```

```bash
kubectl describe pod myapp-mychart-69bdcbddc7-cmqx4 
Name:             myapp-mychart-69bdcbddc7-cmqx4
Namespace:        default
Priority:         0
Service Account:  default
Node:             minikube/192.168.49.2
Start Time:       Thu, 09 Apr 2026 22:50:28 +0300
Labels:           app.kubernetes.io/instance=myapp
                  app.kubernetes.io/managed-by=Helm
                  app.kubernetes.io/name=mychart
                  app.kubernetes.io/version=1.0.1
                  helm.sh/chart=mychart-0.1.0
                  pod-template-hash=69bdcbddc7
Annotations:      <none>
Status:           Running
IP:               10.244.0.26
IPs:
  IP:           10.244.0.26
Controlled By:  ReplicaSet/myapp-mychart-69bdcbddc7
Containers:
  mychart:
    Container ID:   docker://2f794a4fcbeae453f5ade5f058323924d41b71b462282f3b76673628320d36f2
    Image:          bulatgazizov/python_app:1.0.1
    Image ID:       docker-pullable://bulatgazizov/python_app@sha256:e682890d1fc05d93ed67193a21d1d6a39d66bd25bb2a09981a8e639710eb7680
    Port:           5000/TCP (http)
    Host Port:      0/TCP (http)
    State:          Running
      Started:      Thu, 09 Apr 2026 22:50:29 +0300
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     200m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:5000/health delay=0s timeout=1s period=10s #success=1 #failure=3
    Readiness:  http-get http://:5000/ delay=0s timeout=1s period=10s #success=1 #failure=3
    Environment Variables from:
      myapp-mychart-credentials  Secret  Optional: false
```

## Resource Management

### Resource limits configuration

```bash
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

### Explanation of requests vs limits

Requests: guaranteed resources reserved by scheduler when placing the pod; used for scheduling decisions. If node has available capacity, pod gets at least its requests.
Limits: hard cap on resource usage enforced at runtime (cgroup). If a container exceeds CPU limit it is throttled; if it exceeds memory limit it may be OOM-killed_

### How to choose appropriate values

Use requests to size scheduling footprint and limits to protect node/other pods; keep requests <= limits. For production, set realistic requests and conservative limits and monitor actual usage for tuning.

## Vault Integration

### Vault installation verification (kubectl get pods)

```bash
kubectl get pods
NAME                                    READY   STATUS              RESTARTS       AGE
vault-0                                 1/1     Running     0              51s
vault-agent-injector-848dd747d7-h9nm9   0/1     Running     0              51s
```

### Policy and role configuration (sanitized)

```bash
path "secret/data/myapp/*" {
  capabilities = ["read"]
}

path "secret/metadata/myapp/*" {
  capabilities = ["list"]
}
```

```bash
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "myapp-role"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
  ```

### Proof of secret injection (show file exists, path structure)

```bash
kubectl exec -it myapp-mychart-8477bfdd7-tqk4z -c app-python -- ls -la /vault/secrets/
```

```bash
total 8
drwxrwxrwt 2 root root      60 Apr  9 23:23 .
drwxr-xr-x 3 root root    4096 Apr  9 23:23 ..
-rw-r--r-- 1  100 appuser  173 Apr  9 23:23 config
```

### Security analysis

- Strong points: central auth/policy, encryption in Vault, short-lived/dynamic creds, audit logging, fine-grained access control.  
- Risks: sidecar increases attack surface; improper RBAC/annotation controls can enable privilege escalation; dev-mode/insecure Vault configs are dangerous.  
- Mitigations: restrict who can annotate pods, bind roles tightly to service accounts, use TLS/HA/secure unseal, monitor/audit.

### Comparison: K8s Secrets vs Vault

- K8s Secrets: built-in, simple, stored in etcd (base64 by default), relies on cluster RBAC; low ops overhead.  
- Vault: external secrets manager, encrypted-at-rest, dynamic secrets, leasing/rotation, robust auditing; higher ops cost.

### When to use each

- K8s Secrets: small-scale, low-sensitivity workloads, internal tools, or when operational simplicity is required and etcd encryption + tight RBAC are in place.  
- Vault: production, compliance, shared multi-environment infrastructure, need for dynamic/short-lived credentials, central rotation/auditing.

### Production recommendations (short)

- For K8s Secrets: enable etcd encryption at rest, enforce strict RBAC, avoid storing plaintext in manifests, rotate secrets regularly.  
- For Vault: run HA Vault with secure storage backend, TLS, automated/unsealing (KMS), narrow Kubernetes role bindings, short TTLs, and audit logging.  
- Hybrid: use Vault for secret management and dynamic credentials; use K8s Secrets only for non-sensitive config or as ephemeral caches.
