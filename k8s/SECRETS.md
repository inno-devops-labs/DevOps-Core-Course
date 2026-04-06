# Lab 11 - Kubernetes Secrets & HashiCorp Vault

## 1. Kubernetes Secrets

### 1.1 Create a Secret via kubectl

Command:
```bash
kubectl create secret generic app-credentials \
  --from-literal=username="[HIDDEN]" \
  --from-literal=password="[HIDDEN]"
```

Output:
```bash
$ kubectl create secret generic app-credentials \
  --from-literal=username="[HIDDEN]" \
  --from-literal=password="[HIDDEN]"
secret/app-credentials created
```

### 1.2 View the Secret and Decode Values

View YAML:
```bash
kubectl get secret app-credentials -o yaml
```

Output:
```bash
$ kubectl get secret app-credentials -o yaml
apiVersion: v1
data:
  password: [HIDDEN_ENC]
  username: [HIDDEN_ENC]
kind: Secret
metadata:
  creationTimestamp: "2026-04-06T18:58:10Z"
  name: app-credentials
  namespace: default
  resourceVersion: "397"
  uid: c9313a77-de6e-47b3-b835-b9a628fe97b0
type: Opaque
```

Decode values:
```bash
printf '%s' "BASE64_VALUE" | base64 -d
```

Decoded values:
```
$ printf '%s' "[HIDDEN_ENC]" | base64 -d
[HIDDEN]
$ printf '%s' "[HIDDEN_ENC]" | base64 -d
[HIDDEN]
```

### 1.3 Encoding vs Encryption

Kubernetes Secrets are **base64-encoded**, which is only an encoding for data transport. Anyone who can read the Secret can decode it. This is not encryption and does not protect data from unauthorized access.

### 1.4 Security Implications (etcd Encryption)

By default, Secrets are stored in etcd as base64-encoded data. For production, we should **enable encryption at rest in etcd**, and enforce RBAC to restrict access. This ensures that even if etcd is compromised, raw Secret data is protected by encryption keys.

## 2. Helm Secret Integration

### 2.1 Chart Structure

Updated chart structure:
```
k8s/devops-info-chart/
|-- values.yaml
|-- values-dev.yaml
|-- values-prod.yaml
`-- templates/
    |-- deployment.yaml
    |-- secrets.yaml
    `-- serviceaccount.yaml
```

### 2.2 Secret Template

`templates/secrets.yaml` uses `stringData` so plaintext values from `values.yaml` are automatically encoded by Kubernetes. Example values:
```yaml
secrets:
  enabled: true
  data:
    username: "change-me"
    password: "change-me"
```

### 2.3 Deployment Consumption

The deployment uses `envFrom` with a `secretRef` to inject all keys:
```yaml
envFrom:
  - secretRef:
      name: <release>-secret
```

This avoids exposing values in `kubectl describe pod` output, while still making them available as environment variables inside the container.

### 2.4 Verification

Upgrade the chart:
```bash
helm upgrade --install devops-info k8s/devops-info-chart \
  -f k8s/devops-info-chart/values-dev.yaml
```

Output:
```bash
$ helm upgrade --install devops-info k8s/devops-info-chart \
  -f k8s/devops-info-chart/values-dev.yaml
Release "devops-info" does not exist. Installing it now.
NAME: devops-info
LAST DEPLOYED: Mon Apr  6 22:01:47 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
Thank you for installing devops-info.

Release: devops-info
Namespace: default

Service type: NodePort
Service port: 80

If you used NodePort, access the service via the node IP and the NodePort.
```

Verify env vars inside the pod:
```bash
POD=$(kubectl get pods -l app.kubernetes.io/instance=devops-info -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it "$POD" -- printenv | grep -E 'username|password'
```

Output:
```bash
$ POD=$(kubectl get pods -l app.kubernetes.io/instance=devops-info -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it "$POD" -- printenv | grep -E 'username|password'
password="[HIDDEN]"
username="[HIDDEN]"
```

Verify that Secret values are not shown in describe output:
```bash
kubectl describe pod "$POD"
```

Output:
```bash
$ kubectl describe pod "$POD"
Name:             devops-info-devops-info-7d86c8f455-thdl9
Namespace:        default
Priority:         0
Service Account:  devops-info-devops-info-sa
Node:             devops-lab9-control-plane/172.18.0.2
Start Time:       Mon, 06 Apr 2026 22:02:04 +0300
Labels:           app.kubernetes.io/instance=devops-info
                  app.kubernetes.io/name=devops-info
                  pod-template-hash=7d86c8f455
                  tier=backend
Annotations:      <none>
Status:           Running
IP:               10.244.0.6
IPs:
  IP:           10.244.0.6
Controlled By:  ReplicaSet/devops-info-devops-info-7d86c8f455
Containers:
  devops-info-service:
    Container ID:  containerd://10234d3d5aa8a842593667823d1af55807e2786556a0c0a8ca3717195acaeea1
    Image:         alsstarikova/devops-info-service:latest
    Image ID:      docker.io/alsstarikova/devops-info-service@sha256:3499da7374e2acd1409c1294ef3c0425ed50a4cea0cae81bc46da5b54c9221df
    Port:          5000/TCP (http)
    Host Port:     0/TCP (http)
    Command:
      python
      -m
      uvicorn
    Args:
      app:app
      --host
      0.0.0.0
      --port
      5000
    State:          Running
      Started:      Mon, 06 Apr 2026 22:02:21 +0300
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     100m
      memory:  128Mi
    Requests:
      cpu:      50m
      memory:   64Mi
    Liveness:   http-get http://:http/health delay=5s timeout=2s period=10s #success=1 #failure=3
    Readiness:  http-get http://:http/health delay=3s timeout=2s period=5s #success=1 #failure=3
    Environment Variables from:
      devops-info-devops-info-secret  Secret  Optional: false
    Environment:
      PORT:        5000
      PYTHONPATH:  /home/app
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-42574 (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   True
  Initialized                 True
  Ready                       True
  ContainersReady             True
  PodScheduled                True
Volumes:
  kube-api-access-42574:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    Optional:                false
    DownwardAPI:             true
QoS Class:                   Burstable
Node-Selectors:              <none>
Tolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:
  Type     Reason     Age                 From               Message
  ----     ------     ----                ----               -------
  Normal   Scheduled  2m13s               default-scheduler  Successfully assigned default/devops-info-devops-info-7d86c8f455-thdl9 to devops-lab9-control-plane
  Normal   Pulling    2m11s               kubelet            spec.containers{devops-info-service}: Pulling image "alsstarikova/devops-info-service:latest"
  Normal   Pulled     117s                kubelet            spec.containers{devops-info-service}: Successfully pulled image "alsstarikova/devops-info-service:latest" in 14.292s (14.292s including waiting). Image size: 65724117 bytes.
  Normal   Created    117s                kubelet            spec.containers{devops-info-service}: Container created
  Normal   Started    116s                kubelet            spec.containers{devops-info-service}: Container started
  Warning  Unhealthy  92s (x2 over 102s)  kubelet            spec.containers{devops-info-service}: Liveness probe failed: Get "http://10.244.0.6:5000/health": dial tcp 10.244.0.6:5000: connect: connection refused
  Warning  Unhealthy  90s (x5 over 110s)  kubelet            spec.containers{devops-info-service}: Readiness probe failed: Get "http://10.244.0.6:5000/health": dial tcp 10.244.0.6:5000: connect: connection refused
```

## 3. Resource Management

The chart already defines requests and limits in `values.yaml`, and they are wired into the deployment:
```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "250m"
    memory: "256Mi"
```

**Requests** reserve guaranteed CPU/memory for the pod, while **limits** cap maximum usage. Requests help the scheduler place pods reliably, and limits prevent a single pod from starving the node.

### How to Choose Values

Use small requests based on observed baseline consumption, and set limits to allow short spikes but prevent runaway usage. For production, measure with real workload and adjust.

## 4. Vault Integration

### 4.1 Install Vault via Helm

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

Output:
```bash
$ helm repo add hashicorp https://helm.releases.hashicorp.com
"hashicorp" has been added to your repositories
$ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "hashicorp" chart repository
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
$ helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
NAME: vault
LAST DEPLOYED: Mon Apr  6 22:07:50 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
NOTES:
Thank you for installing HashiCorp Vault!

Now that you have deployed Vault, you should look over the docs on using
Vault with Kubernetes available here:

https://developer.hashicorp.com/vault/docs


Your release is named vault. To learn more about the release, try:

  $ helm status vault
  $ helm get manifest vault
```

Verify pods:
```bash
kubectl get pods -l app.kubernetes.io/name=vault
```

Output:
```bash
 kubectl get pods -l app.kubernetes.io/name=vault
NAME      READY   STATUS    RESTARTS   AGE
vault-0   1/1     Running   0          59s
```

### 4.2 Configure Vault (KV v2)

```bash
kubectl exec -it vault-0 -- /bin/sh
vault secrets enable -path=secret kv-v2
vault kv put secret/myapp/config username="[HIDDEN]" password="[HIDDEN]"
```

Output:
```bash
$ kubectl exec -it vault-0 -- /bin/sh
/ $ vault secrets enable -path=secret kv-v2
Error enabling: Error making API request.

URL: POST http://127.0.0.1:8200/v1/sys/mounts/secret
Code: 400. Errors:

* path is already in use at secret/
/ $ vault kv put secret/myapp/config username="[HIDDEN]" password="[HIDDEN]"
====== Secret Path ======
secret/data/myapp/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-06T19:09:39.069795739Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
/ $ exit
```

### 4.3 Kubernetes Auth, Policy, and Role

```bash
vault auth enable kubernetes

vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
```

Output:
```bash
/ $ vault auth enable kubernetes
Success! Enabled kubernetes auth method at: kubernetes/
/ $ vault write auth/kubernetes/config \
>   kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
Success! Data written to: auth/kubernetes/config
```

Create policy file `app-policy.hcl`:
```hcl
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

Apply policy and role:
```bash
vault policy write app-policy app-policy.hcl

vault write auth/kubernetes/role/devops-info-role \
  bound_service_account_names="devops-info-devops-info-sa" \
  bound_service_account_namespaces="default" \
  policies="app-policy" \
  ttl="1h"
```

Output:
```bash
$ kubectl exec -it vault-0 -- /bin/sh -c 'cat <<EOF > /tmp/app-policy.hcl
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
EOF'
$ kubectl exec -it vault-0 -- vault policy write app-policy /tmp/app-policy.hcl
Success! Uploaded policy: app-policy
$ kubectl exec -it vault-0 -- vault write auth/kubernetes/role/devops-info-role \
  bound_service_account_names="devops-info-devops-info-sa" \
  bound_service_account_namespaces="default" \
  policies="app-policy" \
  ttl="1h"
WARNING! The following warnings were returned from Vault:

  * Role devops-info-role does not have an audience configured. While
  audiences are not required, consider specifying one if your use case would
  benefit from additional JWT claim verification.
```

### 4.4 Vault Agent Injection

Enable in `values.yaml`:
```yaml
vault:
  enabled: true
  role: "devops-info-role"
  agentInjectSecretPath: "secret/data/myapp/config"
```

Deploy the chart and verify injected file:
```bash
helm upgrade --install devops-info k8s/devops-info-chart \
  -f k8s/devops-info-chart/values-dev.yaml \
  --set vault.enabled=true

POD=$(kubectl get pods -l app.kubernetes.io/instance=devops-info -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it "$POD" -- ls -la /vault/secrets
kubectl exec -it "$POD" -- cat /vault/secrets/config
```

Output:
```bash
$ helm upgrade --install devops-info k8s/devops-info-chart \
  -f k8s/devops-info-chart/values-dev.yaml \
  --set vault.enabled=true
Release "devops-info" has been upgraded. Happy Helming!
NAME: devops-info
LAST DEPLOYED: Mon Apr  6 22:17:47 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
TEST SUITE: None
NOTES:
Thank you for installing devops-info.

Release: devops-info
Namespace: default

Service type: NodePort
Service port: 80

If you used NodePort, access the service via the node IP and the NodePort.
$ POD=$(kubectl get pods -l app.kubernetes.io/instance=devops-info -o jsonpath='{.items[0].metadata.name}')
$ kubectl exec -it "$POD" -- ls -la /vault/secrets
Defaulted container "devops-info-service" out of: devops-info-service, vault-agent, vault-agent-init (init)
total 8
drwxrwxrwt 2 root root   60 Apr  6 19:17 .
drwxr-xr-x 3 root root 4096 Apr  6 19:17 ..
-rw-r--r-- 1  100 1000  177 Apr  6 19:17 config
$ kubectl exec -it "$POD" -- cat /vault/secrets/config
Defaulted container "devops-info-service" out of: devops-info-service, vault-agent, vault-agent-init (init)
data: map[password:[HIDDEN] username:[HIDDEN]]
metadata: map[created_time:2026-04-06T19:09:39.069795739Z custom_metadata:<nil> deletion_time: destroyed:false version:1]
```

### Sidecar Injection Pattern

Vault Injector mutates the pod to add a Vault Agent sidecar and volume. The agent authenticates using the pod's service account, fetches secrets from Vault, and writes them to `/vault/secrets`. The application reads secrets from files instead of environment variables.

## 5. Security Analysis

### Kubernetes Secrets

Pros:
- Native to Kubernetes
- Simple to create and consume
- Works well for small clusters and dev environments

Cons:
- Base64 encoding only
- Needs extra setup for encryption at rest
- Access control depends entirely on RBAC

### HashiCorp Vault

Pros:
- Centralized secret management
- Strong policies and audit logging
- Dynamic secrets and rotation
- Supports multiple auth methods and platforms

Cons:
- Additional operational complexity
- Requires careful configuration and monitoring

### Recommendations

- Use Kubernetes Secrets for low-risk dev/test environments.
- For production, enable etcd encryption and prefer Vault or another external secret manager.
- Use RBAC, least privilege, and periodic rotation in all environments.
