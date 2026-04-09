# Lab 11: Kubernetes Secrets & HashiCorp Vault

## Kubernetes Secrets

### Create Secret

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ kubectl create secret generic app-credentials --from-literal=username=*user* --from-literal=password=*pass*
secret/app-credentials created
```

### View Secret

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ kubectl get secret app-credentials -o yaml
apiVersion: v1
data:
  password: c2VjcmV0MTIz
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-09T08:31:08Z"
  name: app-credentials
  namespace: default
  resourceVersion: "20349"
  uid: 758e4980-2d88-4f4d-b3e8-d5d0f1bad3c5
type: Opaque
```

### Decode Values

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d 
*user*

s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d
*pass*
```

Kubernetes Secrets are base64-encoded, not encrypted by default. Base64 only changes representation; anyone with API access to the Secret can decode it.

Secrets are not encrypted at rest by default unless the cluster administrator enables etcd encryption with an API server `EncryptionConfiguration`. In production this should be enabled.


## Helm Secret Integration

### Chart Structure

```text
k8s/devops-python/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── secrets.yaml
    ├── serviceaccount.yaml
    ├── pre-install-job.yaml
    └── post-install-job.yaml
```

### Secret Consumption

The chart now creates a Kubernetes `Secret` in `templates/secrets.yaml` and injects it into the application pod through `envFrom.secretRef` in `templates/deployment.yaml`.

Rendered chart verification:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ helm template lab11-release k8s/devops-python -f k8s/devops-python/values-dev.yaml --set secret.username=*user* --set secret.password=*pass*
# Source: devops-python/templates/serviceaccount.yaml
kind: ServiceAccount
# Source: devops-python/templates/secrets.yaml
kind: Secret
stringData:
  username: "*user*"
  password: "*pass*"
# Source: devops-python/templates/service.yaml
kind: Service
# Source: devops-python/templates/deployment.yaml
kind: Deployment
      serviceAccountName: lab11-release-devops-python
          envFrom:
            - secretRef:
# Source: devops-python/templates/post-install-job.yaml
kind: Job
# Source: devops-python/templates/pre-install-job.yaml
kind: Job
```

Installed release resources:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ kubectl get all -l app.kubernetes.io/instance=lab11-release
NAME                                               READY   STATUS    RESTARTS   AGE
pod/lab11-release-devops-python-644969578d-fnswb   2/2     Running   0          49s

NAME                                  TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/lab11-release-devops-python   NodePort   10.109.51.125   <none>        80:31192/TCP   5m34s

NAME                                          READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/lab11-release-devops-python   1/1     1            1           5m34s

NAME                                                     DESIRED   CURRENT   READY   AGE
replicaset.apps/lab11-release-devops-python-644969578d   1         1         1       49s
replicaset.apps/lab11-release-devops-python-79df994fc8   0         0         0       5m34s
```

Environment variable can be seen with this command

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ POD=$(kubectl get pods -l app.kubernetes.io/instance=lab11-release -o jsonpath='{.items[0].metadata.name}'); kubectl exec "$POD" -c app -- env
```

`kubectl describe pod` does not expose the secret values themselves, to see them use this command:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ POD=$(kubectl get pods -l app.kubernetes.io/instance=lab11-release -o jsonpath='{.items[0].metadata.name}'); kubectl describe pod "$POD"
```

## Resource Management

### Configuration

The deployment uses configurable requests and limits from `values.yaml`:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 200m
    memory: 256Mi
```

Development overrides in `values-dev.yaml`:

```yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```

Requests define the minimum resources Kubernetes should reserve for the container. Limits define the maximum resources the container is allowed to consume.

For this service, small dev values are enough because the app is lightweight. In production the values should be chosen from observed CPU and memory usage, then increased with some headroom for traffic spikes.


## Vault Integration

### Vault Installation

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ helm repo add hashicorp https://helm.releases.hashicorp.com
"hashicorp" has been added to your repositories
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "hashicorp" chart repository
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ helm search repo hashicorp/vault
NAME                            	CHART VERSION	APP VERSION	DESCRIPTION                               
hashicorp/vault                 	0.32.0       	1.21.2     	Official HashiCorp Vault Chart            
hashicorp/vault-radar-agent     	0.1.0        	0.42.0     	Official HashiCorp Vault Radar Agent Chart
hashicorp/vault-secrets-gateway 	0.0.2        	0.1.0      	A Helm chart for Kubernetes               
hashicorp/vault-secrets-operator	1.3.0        	1.3.0      	Official Vault Secrets Operator Chart     
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ helm install vault hashicorp/vault --set server.dev.enabled=true --set injector.enabled=true --wait
NAME: vault
LAST DEPLOYED: Thu Apr  9 11:35:19 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
NOTES:
Thank you for installing HashiCorp Vault!

Now that you have deployed Vault, you should look over the docs on using
Vault with Kubernetes available here:

https://developer.hashicorp.com/vault/docs


Your release is named vault. To learn more about the release, try:

  $ helm status vault
  $ helm get manifest vault
```

Vault pods verification:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ kubectl get pods -l app.kubernetes.io/instance=vault
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          2m12s
vault-agent-injector-848dd747d7-lvs5l   1/1     Running   0          2m50s
```

### Vault Configuration

Vault status:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ kubectl exec vault-0 -- sh -lc 'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root; vault status'
Key             Value
---             -----
Seal Type       shamir
Initialized     true
Sealed          false
Total Shares    1
Threshold       1
Version         1.21.2
Build Date      2026-01-06T08:33:05Z
Storage Type    inmem
Cluster Name    vault-cluster-0ea77300
Cluster ID      027a6918-eb5c-7fe9-fd7c-9ddf393053fe
HA Enabled      false
```

KV engine and secret creation:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ kubectl exec vault-0 -- sh -lc 'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root; vault secrets enable -path=kv kv-v2'
Success! Enabled the kv-v2 secrets engine at: kv/
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ kubectl exec vault-0 -- sh -lc 'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root; vault kv put kv/myapp/config username=*user* password=*pass*'
==== Secret Path ====
kv/data/myapp/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-09T08:36:51.710336864Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
```

Kubernetes auth configuration:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ kubectl exec vault-0 -- sh -lc 'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root; vault auth enable kubernetes'
Success! Enabled kubernetes auth method at: kubernetes/
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ kubectl exec vault-0 -- sh -lc 'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root; vault write auth/kubernetes/config token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token kubernetes_host="https://${KUBERNETES_PORT_443_TCP_ADDR}:443" kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'
Success! Data written to: auth/kubernetes/config
```

Policy and role:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ kubectl exec vault-0 -- sh -lc 'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root; vault policy read devops-python-policy'
path "kv/data/myapp/config" {
  capabilities = ["read"]
}
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ kubectl exec vault-0 -- sh -lc 'export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=root; vault read auth/kubernetes/role/devops-python-role'
Key                                         Value
---                                         -----
alias_name_source                           serviceaccount_uid
bound_service_account_names                 [lab11-release-devops-python]
bound_service_account_namespace_selector    n/a
bound_service_account_namespaces            [default]
policies                                    [devops-python-policy]
token_bound_cidrs                           []
token_explicit_max_ttl                      0s
token_max_ttl                               0s
token_no_default_policy                     false
token_num_uses                              0
token_period                                0s
token_policies                              [devops-python-policy]
token_ttl                                   24h
token_type                                  default
ttl                                         24h
```

### Injection Verification

The deployment was upgraded with Vault annotations so the injector adds a sidecar and mounts rendered secrets into `/vault/secrets`.

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ kubectl get pods -l app.kubernetes.io/instance=lab11-release -o wide
NAME                                           READY   STATUS        RESTARTS   AGE    IP            NODE       NOMINATED NODE   READINESS GATES
lab11-release-devops-python-644969578d-fnswb   2/2     Running       0          23s    10.244.0.89   minikube   <none>           <none>
lab11-release-devops-python-79df994fc8-hdw8t   1/1     Terminating   0          5m8s   10.244.0.84   minikube   <none>           <none>
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ POD=$(kubectl get pods -l app.kubernetes.io/instance=lab11-release -o jsonpath='{.items[0].metadata.name}'); kubectl describe pod "$POD" | sed -n '/Annotations:/,/Containers:/p'
Annotations:      vault.hashicorp.com/agent-inject: true
                  vault.hashicorp.com/agent-inject-secret-config.txt: kv/data/myapp/config
                  vault.hashicorp.com/agent-inject-status: injected
                  vault.hashicorp.com/role: devops-python-role
Status:           Running
IP:               10.244.0.89
IPs:
  IP:           10.244.0.89
Controlled By:  ReplicaSet/lab11-release-devops-python-644969578d
Init Containers:
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab11 λ POD=$(kubectl get pods -l app.kubernetes.io/instance=lab11-release -o jsonpath='{.items[0].metadata.name}'); kubectl exec "$POD" -c app -- sh -lc 'find /vault -maxdepth 2 -type f | sort'
/vault/secrets/config.txt
```

This uses the sidecar injection pattern: Vault Agent is injected into the pod, authenticates to Vault using the pod's Kubernetes service account, reads the permitted secret path, and writes the secret to a shared volume that the application container can read as a file.


## Security Analysis

### Kubernetes Secrets vs Vault
- Kubernetes Secrets are simple, native, and enough for small internal workloads that only need basic secret distribution inside the cluster.
- Vault provides stronger secret management with dedicated access policies, secret versioning, dynamic credentials, and a cleaner separation between application deployment and secret storage.
- Kubernetes Secrets are stored in etcd and depend heavily on cluster hardening.
- Vault keeps secret access behind explicit auth methods and policies, which scales better for production systems.

### When To Use Each
- Use Kubernetes Secrets for simple cluster-local configuration when the security requirements are moderate and operational simplicity matters.
- Use Vault when you need stronger access control, rotation, dynamic secrets, or centralized secret management across multiple applications and platforms.

### Production Recommendations
- Enable etcd encryption at rest for Kubernetes Secrets.
- Restrict secret access with RBAC and least privilege.
- Do not store real credentials in Git or Helm values files.
- Use Vault or another external secret manager for production credentials.
- Prefer short-lived or dynamic credentials where possible.
