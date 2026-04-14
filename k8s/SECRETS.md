# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## Overview

This lab extends the Helm chart from Lab 10 with secret management capabilities. The implementation covers native Kubernetes Secrets, Helm-managed secrets, resource management, and HashiCorp Vault integration for runtime secret injection.

---

## 1. Kubernetes Secrets

### Creating a Secret with `kubectl`

The first part of the lab was to create a native Kubernetes Secret and inspect how Kubernetes stores secret data.

```bash
kubectl create secret generic app-credentials --from-literal=username=admin --from-literal=password=secret123
```

### Viewing the Secret

```bash
kubectl get secret app-credentials
kubectl get secret app-credentials -o yaml
kubectl describe secret app-credentials
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl create secret generic app-credentials --from-literal=username=SECRET --from-literal=password=OHHH_SECRET
secret/app-credentials created
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get secret app-credentials
NAME              TYPE     DATA   AGE
app-credentials   Opaque   2      16s
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get secret app-credentials -o yaml
apiVersion: v1
data:
  password: c2VjcmV0MTIz
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-04T13:42:27Z"
  name: app-credentials
  namespace: default
  resourceVersion: "561"
  uid: 37f798ad-43eb-4443-b891-4406681457eb
type: Opaque
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl describe secret app-credentials
Name:         app-credentials
Namespace:    default
Labels:       <none>
Annotations:  <none>

Type:  Opaque

Data
====
sonpath="{.data.password}"
c2VjcmV0MTIz
sonpath="{.data.password}"
c2VjcmV0MTIz
```

### Decoding Secret Values

Linux/macOS:

```bash
echo "YWRtaW4=" | base64 -d
echo "c2VjcmV0MTIz" | base64 -d
```

PowerShell:

```powershell
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("YWRtaW4="))
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("c2VjcmV0MTIz"))
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String((kubectl get secret app-credentials -o jsonpath="{.data.username}")))
>>
SECRET
PS C:\Users\zagur\DevOps\DevOps-Core-Course> [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String((kubectl get secret app-credentials -o jsonpath="{.data.password}")))
OHHH_SECRET
```

### Base64 Encoding vs Encryption

Kubernetes Secrets are **base64-encoded**, but base64 is only an encoding format, not a security mechanism. It makes binary or special-character data easier to store in YAML and JSON, but anyone who can read the secret can decode it immediately.

Encryption is different: encrypted data requires a cryptographic key to recover the original value. By default, Kubernetes Secrets are not strongly protected just because they are stored as base64 in manifests or API responses.

### Security Implications

Kubernetes Secrets should not be treated as fully secure storage by themselves:

- secret values are visible to users or workloads that have permission to read them;
- base64 does not protect against unauthorized access;
- access control must be enforced with RBAC;
- in production, encryption at rest for `etcd` should be enabled;
- for stronger secret management, an external system such as Vault is preferred.

---

## 2. Helm Secret Integration

### Updated Chart Structure

The Helm chart from Lab 10 was extended with a Secret template:

```text
k8s/devops-info-service/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── service.yaml
    ├── secrets.yaml
    └── serviceaccount.yaml
```

### Secret Values in `values.yaml`

The chart stores placeholder secret values in `values.yaml`. Real credentials should not be committed to Git and should instead be passed during installation or upgrade.

```yaml
secrets:
  enabled: true
  data:
    APP_USERNAME: "change-me"
    APP_PASSWORD: "change-me"
```

### Secret Template

The file `templates/secrets.yaml` renders a Kubernetes Secret from Helm values.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-info-service.fullname" . }}-secret
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
type: Opaque
stringData:
  {{- range $key, $value := .Values.secrets.data }}
  {{ $key }}: {{ $value | quote }}
  {{- end }}
```

This approach uses `stringData`, which allows plain text values in the template. Kubernetes converts them into base64-encoded `data` when the Secret is created.

### Consuming Secrets in the Deployment

The application Deployment consumes all secret keys through `envFrom` and `secretRef`.

```yaml
envFrom:
  - secretRef:
      name: {{ include "devops-info-service.fullname" . }}-secret
```

This makes the secret values available inside the container as environment variables.

### Installing the Chart with Secret Overrides

```bash
helm upgrade --install dev-release k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --set secrets.data.APP_USERNAME=SECRET \
  --set secrets.data.APP_PASSWORD=OHHH_SECRET
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> helm upgrade --install dev-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml --set secrets.data.APP_USERNAME=SECRET --set secrets.data.APP_PASSWORD=OHHH_SECRET
Release "dev-release" does not exist. Installing it now.
NAME: dev-release
LAST DEPLOYED: Sat Apr  4 16:49:01 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get secrets                    
NAME                                     TYPE                 DATA   AGE
app-credentials                          Opaque               2      7m11s
dev-release-devops-info-service-secret   Opaque               2      23s
sh.helm.release.v1.dev-release.v1        helm.sh/release.v1   1      37s
```

### Verifying Secret Injection in the Pod

```bash
kubectl get pods
kubectl exec -it <pod-name> -- printenv | grep APP_
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl exec -it dev-release-devops-info-service-f68c6c5df-znhlz -- env
PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOSTNAME=dev-release-devops-info-service-f68c6c5df-znhlz
TERM=xterm
APP_PASSWORD=OHHH_SECRET
APP_USERNAME=SECRET
PYTHONUNBUFFERED=1
DEV_RELEASE_DEVOPS_INFO_SERVICE_SERVICE_PORT=80
DEV_RELEASE_DEVOPS_INFO_SERVICE_PORT_80_TCP_PROTO=tcp
KUBERNETES_PORT_443_TCP_PORT=443
KUBERNETES_PORT_443_TCP_ADDR=10.96.0.1
DEV_RELEASE_DEVOPS_INFO_SERVICE_PORT=tcp://10.104.154.66:80
DEV_RELEASE_DEVOPS_INFO_SERVICE_PORT_80_TCP_ADDR=10.104.154.66
KUBERNETES_SERVICE_PORT=443
DEVOPS_INFO_SERVICE_SERVICE_HOST=10.109.206.39
DEVOPS_INFO_SERVICE_PORT_80_TCP_PROTO=tcp
DEVOPS_INFO_SERVICE_PORT_80_TCP_PORT=80
DEVOPS_INFO_SERVICE_PORT_80_TCP_ADDR=10.109.206.39
DEV_RELEASE_DEVOPS_INFO_SERVICE_SERVICE_PORT_HTTP=80
KUBERNETES_SERVICE_PORT_HTTPS=443
KUBERNETES_PORT_443_TCP=tcp://10.96.0.1:443
DEVOPS_INFO_SERVICE_SERVICE_PORT_HTTP=80
DEV_RELEASE_DEVOPS_INFO_SERVICE_PORT_80_TCP=tcp://10.104.154.66:80
DEV_RELEASE_DEVOPS_INFO_SERVICE_PORT_80_TCP_PORT=80
KUBERNETES_SERVICE_HOST=10.96.0.1
KUBERNETES_PORT_443_TCP_PROTO=tcp
DEVOPS_INFO_SERVICE_SERVICE_PORT=80
DEVOPS_INFO_SERVICE_PORT=tcp://10.109.206.39:80
DEVOPS_INFO_SERVICE_PORT_80_TCP=tcp://10.109.206.39:80
DEV_RELEASE_DEVOPS_INFO_SERVICE_SERVICE_HOST=10.104.154.66
KUBERNETES_PORT=tcp://10.96.0.1:443
GPG_KEY=7169605F62C751356D054A26A821E680E5FA6305
PYTHON_VERSION=3.13.11
PYTHON_SHA256=16ede7bb7cdbfa895d11b0642fa0e523f291e6487194d53cf6d3b338c3a17ea2      
PYTHONDONTWRITEBYTECODE=1
PIP_DISABLE_PIP_VERSION_CHECK=1
PIP_NO_CACHE_DIR=1
HOST=0.0.0.0
PORT=5000
DEBUG=FALSE
HOME=/
```

### Ensuring Secrets Are Not Exposed in Pod Description

```bash
kubectl describe pod <pod-name>
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl describe pod dev-release-devops-info-service-f68c6c5df-znhlz
Name:             dev-release-devops-info-service-f68c6c5df-znhlz
Namespace:        default
Priority:         0
Service Account:  default
Node:             minikube/192.168.49.2
Start Time:       Sat, 04 Apr 2026 16:55:26 +0300
Labels:           app.kubernetes.io/instance=dev-release
                  app.kubernetes.io/name=devops-info-service
                  pod-template-hash=f68c6c5df
Annotations:      <none>
Status:           Running
IP:               10.244.0.10
IPs:
  IP:           10.244.0.10
Controlled By:  ReplicaSet/dev-release-devops-info-service-f68c6c5df
Containers:
  devops-info-service:
    Container ID:   docker://8735bae6ab9c351b1f7e63325e7ed29bc6be7e1522866c41d72bbb653b936bc8
    Image:          devops-info-service:dev
    Image ID:       docker-pullable://wkwtfigo/devops-info-service@sha256:b7ca743554e5f473c5eb6a5b21eec6fbdbb988a5eba3d3ff46c31540140fb254
    Port:           5000/TCP (http)
    Host Port:      0/TCP (http)
    State:          Running
      Started:      Sat, 04 Apr 2026 16:55:27 +0300
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     100m
      memory:  128Mi
    Requests:
      cpu:      50m
      memory:   64Mi
    Liveness:   http-get http://:5000/health delay=10s timeout=2s period=10s #success=1 #failure=6
    Readiness:  http-get http://:5000/health delay=3s timeout=2s period=5s #success=1 #failure=6
    Startup:    http-get http://:5000/health delay=0s timeout=2s period=5s #success=1 #failure=30
    Environment Variables from:
      dev-release-devops-info-service-secret  Secret  Optional: false
    Environment:
      PYTHONUNBUFFERED:  1
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-f8kz2 (ro) 
Conditions:
ltiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
ltiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    Optional:                false
    DownwardAPI:             true
QoS Class:                   Burstable
Node-Selectors:              <none>
Tolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:
  Type     Reason     Age                  From               Message
  ----     ------     ----                 ----               -------
  Normal   Scheduled  2m9s                 default-scheduler  Successfully assigned default/dev-release-devops-info-service-f68c6c5df-znhlz to minikube
  Normal   Pulled     2m8s                 kubelet            Container image "devops-info-service:dev" already present on machine
  Normal   Created    2m8s                 kubelet            Created container: devops-info-service
  Normal   Started    2m7s                 kubelet            Started container devops-info-service
  Warning  Unhealthy  100s (x6 over 2m5s)  kubelet            Startup probe failed: Get "http://10.244.0.10:5000/health": dial tcp 10.244.0.10:5000: connect: connection refused
```

When secrets are injected through `secretRef`, Kubernetes does not print the actual values in `kubectl describe pod`. This is safer than placing credentials directly in plain-text environment variable definitions.

---

## 3. Resource Management

### Resource Limits Configuration

The application uses explicit CPU and memory requests and limits.

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "200m"
    memory: "256Mi"
```

These values are defined through Helm values so that different environments can override them.

### Requests vs Limits

- **Requests** define the minimum resources Kubernetes reserves for the container. They are used by the scheduler to decide where the Pod can run.
- **Limits** define the maximum resources the container is allowed to consume.

In this lab:

- `100m CPU` and `128Mi memory` as requests keep the application lightweight and schedulable in minikube;
- `200m CPU` and `256Mi memory` as limits prevent a single container from consuming too many local cluster resources.

### Choosing Appropriate Values

For this application, low values are appropriate because the service is small and intended for local or educational deployment. In a real environment, resource values should be based on:

- actual runtime measurements;
- expected traffic volume;
- startup behavior;
- memory usage under load;
- cluster capacity and multi-tenant constraints.

A common strategy is to start conservatively, observe real metrics, and then tune requests and limits based on monitoring data.

---

## 4. Vault Integration

### Installing Vault via Helm

Vault was installed in development mode together with the injector.

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

### Verifying Vault Installation

```bash
kubectl get pods
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> helm install vault C:\Users\zagur\Projects\vault-helm --set "server.dev.enabled=true" --set "injector.enabled=true"        
NAME: vault
LAST DEPLOYED: Sat Apr  4 17:14:43 2026
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
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods                       
NAME                                              READY   STATUS    RESTARTS   AGE  
dev-release-devops-info-service-f68c6c5df-znhlz   1/1     Running   0          19m  
devops-info-service-7464447d6f-6nrlf              1/1     Running   0          33m  
devops-info-service-7464447d6f-6wqxl              1/1     Running   0          33m  
devops-info-service-7464447d6f-m6tbn              1/1     Running   0          33m  
vault-0                                           1/1     Running   0          8s   
vault-agent-injector-75998c9b76-dtzxm             1/1     Running   0          8s   
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods -l app.kubernetes.io/name=vault
NAME      READY   STATUS    RESTARTS   AGE
vault-0   1/1     Running   0          24s
```

### Configuring Vault

Vault was configured from inside the Vault pod.

```bash
kubectl exec -it vault-0 -- /bin/sh
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl exec -it vault-0 -- /bin/sh
/ $ vault secrets enable -path=secret kv-v2
Error enabling: Error making API request.

URL: POST http://127.0.0.1:8200/v1/sys/mounts/secret
Code: 400. Errors:

* path is already in use at secret/
/ $ vault kv put secret/myapp/config username="NO" password="NO"
====== Secret Path ======
secret/data/myapp/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-04T14:15:41.78128972Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
/ $ vault kv get secret/myapp/config
====== Secret Path ======
secret/data/myapp/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-04T14:15:41.78128972Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1

====== Data ======
Key         Value
---         -----
password    NO
username    NO
```

Inside the pod:

```bash
vault secrets enable -path=secret kv-v2
vault kv put secret/myapp/config username="NO" password="NO"
vault kv get secret/myapp/config
```

This creates a KV v2 secret engine and stores application credentials under `secret/myapp/config`.

### Configuring Kubernetes Authentication

```bash
vault auth enable kubernetes

vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
```

```bash
/ $ vault auth enable kubernetes
Success! Enabled kubernetes auth method at: kubernetes/
/ $ vault write auth/kubernetes/config \
>   kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
Success! Data written to: auth/kubernetes/config
```

### Policy Configuration

A policy was created to allow read access to the application secret path.

Applying the policy:

```bash
vault policy write myapp-policy /tmp/myapp-policy.hcl
vault policy read myapp-policy
```

```bash
/ $ cat <<'EOF' > /tmp/myapp-policy.hcl
> path "secret/data/myapp/config" {
>   capabilities = ["read"]
> }
> EOF
/ $ vault policy write myapp-policy /tmp/myapp-policy.hcl
Success! Uploaded policy: myapp-policy
/ $ vault policy read myapp-policy
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

### Role Configuration

A Vault role binds the policy to the application's Kubernetes service account.

```bash
vault write auth/kubernetes/role/myapp-role \
  bound_service_account_names="dev-release-devops-info-service" \
  bound_service_account_namespaces="default" \
  policies="myapp-policy" \
  ttl="1h"
```

Sanitized role verification:

```bash
vault read auth/kubernetes/role/myapp-role
```

```bash
/ $ vault write auth/kubernetes/role/myapp-role \
>   bound_service_account_names="dev-release-devops-info-service" \
>   bound_service_account_namespaces="default" \
>   policies="myapp-policy" \
>   ttl="1h"
WARNING! The following warnings were returned from Vault:

  * Role myapp-role does not have an audience configured. While audiences are       
  not required, consider specifying one if your use case would benefit from
  additional JWT claim verification.

/ $ vault read auth/kubernetes/role/myapp-role
Key                                         Value
---                                         -----
alias_name_source                           serviceaccount_uid
bound_service_account_names                 [dev-release-devops-info-service]       
bound_service_account_namespace_selector    n/a
bound_service_account_namespaces            [default]
policies                                    [myapp-policy]
token_bound_cidrs                           []
token_explicit_max_ttl                      0s
token_max_ttl                               0s
token_no_default_policy                     false
token_num_uses                              0
token_period                                0s
token_policies                              [myapp-policy]
token_ttl                                   1h
token_type                                  default
ttl                                         1h
/ $ exit
```

### Enabling Vault Agent Injection

The Deployment was updated with Vault annotations so that Vault Agent injects the secret into the Pod as a file.

```yaml
metadata:
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/role: "myapp-role"
    vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
```

### Verifying Secret Injection

After redeploying the application, the injected secret can be verified inside the Pod:

```bash
kubectl get pods
kubectl exec -it <pod-name> -- ls -R /vault
kubectl exec -it <pod-name> -- cat /vault/secrets/config
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods
NAME                                               READY   STATUS    RESTARTS   AGE
dev-release-devops-info-service-56f6b66787-dlnlm   2/2     Running   0          54s
devops-info-service-7464447d6f-6nrlf               1/1     Running   0          39m
devops-info-service-7464447d6f-6wqxl               1/1     Running   0          39m
devops-info-service-7464447d6f-m6tbn               1/1     Running   0          39m
vault-0                                            1/1     Running   0          5m46s
vault-agent-injector-75998c9b76-dtzxm              1/1     Running   0          5m46s
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl exec -it dev-release-devops-info-service-56f6b66787-dlnlm -- ls -R /vault
Defaulted container "devops-info-service" out of: devops-info-service, vault-agent, vault-agent-init (init)  
/vault:
secrets

/vault/secrets:
config
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl exec -it dev-release-devops-info-service-56f6b66787-dlnlm -- cat /vault/secrets/config
Defaulted container "devops-info-service" out of: devops-info-service, vault-agent, vault-agent-init (init)  
data: map[password:NO username:NO]
metadata: map[created_time:2026-04-04T14:15:41.78128972Z custom_metadata:<nil> deletion_time: destroyed:false version:1]
PS C:\Users\zagur\DevOps\DevOps-Core-Course>
```

### Sidecar Injection Pattern

Vault Agent Injector uses a mutating admission webhook to modify the Pod definition when it is created. Instead of storing credentials directly inside the application manifest, the Pod receives a Vault Agent sidecar or init-container based injection workflow. That agent authenticates to Vault using the Pod's service account token and retrieves the allowed secrets according to the configured policy and role.

This pattern is safer than hardcoding secrets in manifests because the application does not need to store secret values in Git, and the secret source of truth remains Vault.

---

## 5. Security Analysis

### Kubernetes Secrets vs Vault

#### Kubernetes Secrets

Advantages:

- simple and built into Kubernetes;
- easy to use with `kubectl`, manifests, and Helm;
- sufficient for basic labs and small internal environments.

Disadvantages:

- base64 encoding is not encryption;
- secrets are stored in the Kubernetes control plane and `etcd`;
- secret rotation is manual unless additional tooling is used;
- access is limited only by Kubernetes permissions.

#### HashiCorp Vault

Advantages:

- dedicated secret management platform;
- supports fine-grained access policies;
- secrets can be injected at runtime;
- better suited for rotation, auditing, and centralized management;
- applications do not need hardcoded credentials in manifests.

Disadvantages:

- more complex to install and operate;
- requires authentication setup, policies, and injector configuration;
- higher operational overhead for small local projects.

### When to Use Each Approach

Kubernetes Secrets are acceptable for simple development clusters, local experiments, and small internal workloads where operational simplicity is more important than advanced secret lifecycle management.

Vault is the better choice for production or security-sensitive environments, especially when you need centralized secret control, auditability, runtime delivery, rotation, and strong separation between deployment configuration and sensitive values.

### Production Recommendations

For a real production deployment, I would recommend:

- never storing real secret values in Git;
- keeping only placeholders in `values.yaml`;
- restricting secret access with RBAC;
- enabling encryption at rest for `etcd`;
- using Vault or another dedicated external secret manager;
- sanitizing logs and documentation so credentials are never exposed;
- planning for secret rotation and short-lived credentials where possible.

---

## Conclusion

This lab demonstrated two levels of secret management in Kubernetes. First, native Kubernetes Secrets provide a basic way to store and inject sensitive values. Second, HashiCorp Vault provides a stronger production-oriented approach by moving secret storage and access control into a dedicated system and injecting secrets at runtime.

The final result is a Helm-based application deployment that supports:

- native Kubernetes Secret creation;
- Helm-managed secret templating;
- configurable CPU and memory requests/limits;
- Vault-based secret injection into Pods;
- improved security practices compared with hardcoded credentials.
