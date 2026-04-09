# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## 1. Kubernetes Secrets Fundamentals

### Create secret

```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=hhehehahhaha
```

### Viewing the Secret

```bash
$ kubectl get secret app-credentials -o yaml
```

So  the output:
```yaml
apiVersion: v1
data:
  password: aGhlaGVoYWhoYWhhCg==
  username: YWRtaW4=
kind: Secret
metadata:
  name: app-credentials
  namespace: default
type: Opaque
```

### Decoding b64
```bash
$ echo aGhlaGVoYWhoYWhhCg== | base64 -d
hhehehahhaha

$ echo YWRtaW4= | base64 -d
admin
```

### Base64 vs Encryption

**Base64 encoding** is a binary-to-text representation format. it DOES NOT encrypt or protect data. It only transforms bytes into a safe ASCII string using a 64-character alphabet

**Encryption algos** transforms data using a cryptographic key so that the output (ciphertext) is computationally infeasible to reverse without the correct key

By default, Secrets are stored in plaintext in etcd. To actually protect secrets at rest, you must enable **etcd encryption** via an `EncryptionConfiguration` resource, which encrypts secret data before it is written to etcd using a key managed by you (or a KMS provider). This is not enabled by default on most distributions including minikube

For prod:
- Enable etcd encryption for clusters that store sensitive data in Secret resources
- Use KMS-backed providers in cloud/production environments

## Helm Secret Integration
### Chart Structure

```
k8s/testiks/
├── Chart.yaml
├── values.yaml                    
├── templates/
│   ├── _helpers.tpl
│   ├── secrets.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── hooks/
│       ├── pre-install-job.yaml
│       └── post-install-job.yaml
```

All artefacts are located in `templates` folder 

### How secret are used in deployment

The deployment uses envFrom with secretRef:
```yaml
envFrom:
  - secretRef:
      name: {{ include "app-python.fullname" . }}-secret
env:
  {{- include "app-python.envVars" . | nindent 12 }}
```
All keys are injected as environment variables via envFrom. Static non-sensitive variables (APP_ENV, LOG_LEVEL) come from the named template

### Live evidence

```bash
$ kubectl exec deploy/myapp-app-python -- env | grep -E "SERVICE_NAME|API_KEY|APP_ENV|LOG_LEVEL|HOST"
APP_ENV=production
LOG_LEVEL=info
HOST=xxx
API_KEY=xxx
SERVICE_NAME=testiks

$ helm status testiks
NAME: testiks
LAST DEPLOYED: Thu Apr  9 18:06:31 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2

==> v1/Secret
testiks-secret   Opaque   2

==> v1/Service
testiks   NodePort   80:30080/TCP

==> v1/Deployment
testiks   3/3   3   3

==> v1/Pod(related)
testiks-819f7b16c8-fxkfr   2/2   Running
testiks-819f7b16c8-mgv2q   2/2   Running
testiks-819f7b16c8-wlbv7   2/2   Running

$ kubectl get pods -l app.kubernetes.io/instance=testiks
NAME                                   READY   STATUS    RESTARTS   AGE
testiks-819f7b16c8-fxkfr   2/2     Running   0          5m1s
testiks-819f7b16c8-mgv2q   2/2     Running   0          5m9s
testiks-819f7b16c8-wlbv7   2/2     Running   0          4m52s
```

## 3. Resource Management

Configuration in values.yaml:
```yaml
resources:
  limits:
    cpu: 128m
    memory: 256Mi
  requests:
    cpu: 128m
    memory: 128Mi
```

Requests vs Limits:
- Requests: scheduler guarantee used to place pods
- Limits: hard cap enforced by the kubelet/runtime


How to choose values:
- Start with observed baseline usage
- Set requests near steady-state p50 or p75
- Set limits with headroom for p95 bursts
- Revisit after load tests and production telemetry

## 4. Vault Integration

```bash
$ helm repo add hashicorp https://helm.releases.hashicorp.com
$ helm repo update
$ helm install vault hashicorp/vault \
    --set "server.dev.enabled=true" \
    --set "injector.enabled=true"
```


Live evidence:
```bash
$ kubectl get pods -n vault
NAME                                   READY   STATUS    RESTARTS   AGE
vault-0                                1/1     Running   0          11m
vault-agent-injector-706f77e965-jvl8n  1/1     Running   0          11m
testiks-84d4785464-27d4m               2/2     Running   0          28s
```

```bash
$ kubectl exec -it -n vault vault-0 -- sh

vault secrets enable -path=secret kv-v2
vault kv put secret/myapp/config \
  username="xxx" \
  password="xxx" \
  db_url="postgres://xxx:xxx@postgres:5432/app" \
  api_key="xxx"
```

Kubernetes Auth:
```bash
$ kubectl exec vault-0 -- vault auth enable kubernetes
Success! Enabled kubernetes auth method at: kubernetes/

$ kubectl exec vault-0 -- sh -c '
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)"
'
Success! Data written to: auth/kubernetes/config
```

Proof of Secret Injection:
```bash
$ kubectl exec myapp-app-python-84d4785464-27d4m -c app-python -- \
    cat /vault/secrets/config

USERNAME=admin
PASSWORD=hehehaha
```

Sidecar injection pattern summary:
- Vault Agent runs in the pod and authenticates with pod service account
- Agent reads secret from Vault using configured role and policy
- Agent writes rendered file to shared in-pod volume
- Application reads secrets from the mounted file path

The **Vault Agent Injector** works as a Kubernetes Mutating Admission Webhook:
1. When a pod with `vault.hashicorp.com/agent-inject: "true"` is created, the
   webhook intercepts the pod creation request before it reaches the scheduler
2. It automatically adds a Vault Agent init container (fetches secrets before
   the app starts) and a Vault Agent sidecar container (keeps secrets refreshed)
3. The Vault Agent authenticates to Vault using the pod's Kubernetes Service Account JWT
4. Secrets are written to a shared in-memory volume at `/vault/secrets/`
5. The application reads secrets from files — they never appear in the pod spec,
   making them invisible to `kubectl describe`

## Kubernetes Secrets vs Vault

Kubernetes Secrets: 
- Good for simple cluster-local secret distribution
- Tight integration with K8s and easy to use
- Weaker security posture without etcd encryption and strict RBAC
- Limited auditing and rotation workflows compared to dedicated secret managers

Vault:
- Strong centralized secret management and access control
- Rich audit logging, dynamic secrets, short-lived credentials, and rotation support
- Better fit for production and multi-environment workloads
- Higher operational complexity than native K8s Secrets

When to use each:
- Use Kubernetes Secrets for low-complexity labs and non-critical internal setups
- Use Vault for production workloads, regulated environments, and dynamic credentials

Production Recommendations
- Never commit real secrets to Git — use placeholder values in values.yaml; inject real values at deploy time with --set or a gitignored values file
- Enable etcd encryption at rest — even when using Vault, defense-in-depth protects against etcd backup leaks
- Apply RBAC least privilege — restrict get/list on secrets resources to only the service accounts that need them
- Use Vault for production — especially for databases, use dynamic secrets with short TTLs (minutes, not days)
- Enable Vault audit logging — ship audit logs to a SIEM for compliance and incident response
- Run Vault in HA mode — never use dev mode in production (no persistence, single point of failure)
- Use vault.hashicorp.com/agent-inject-command — trigger app config reload on secret rotation for zero-downtime updates
- Rotate root tokens — generate and immediately revoke Vault root tokens after initial setup; use AppRole or K8s auth for automation
- Namespace isolation — deploy Vault in a dedicated namespace with strict network policies
- Consider External Secrets Operator — as a GitOps-friendly alternative that syncs Vault secrets into K8s Secrets declaratively