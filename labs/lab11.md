# Lab 11 — Kubernetes Secrets & HashiCorp Vault

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Secret%20Management-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-Vault%20%7C%20K8s%20Secrets-informational)

> Secure your Kubernetes applications by implementing proper secret management with native Secrets and HashiCorp Vault integration.

## Overview

Secret management is critical for production Kubernetes deployments. Hardcoded credentials in code or config files are a security nightmare. This lab teaches you how to properly manage sensitive data using Kubernetes native Secrets and enterprise-grade HashiCorp Vault.

**What You'll Learn:**
- Kubernetes Secrets creation and consumption
- Base64 encoding vs actual encryption
- Helm-based secret management
- HashiCorp Vault installation and configuration
- Kubernetes authentication with Vault
- Sidecar injection pattern for secrets

**Building On:** Your Helm chart from Lab 10 will be extended with secret management capabilities.

**Tech Stack:** Kubernetes Secrets | HashiCorp Vault 1.18+ | Vault Helm 0.28+ | Vault Agent Injector

---

## Tasks

### Task 1 — Kubernetes Secrets Fundamentals (2 pts)

**Objective:** Understand how Kubernetes Secrets work and their security model.

**Requirements:**

1. **Create a Secret Using kubectl**
   - Create a secret named `app-credentials` with:
     - `username` key
     - `password` key
   - Use the imperative `kubectl create secret` command

2. **Examine the Secret**
   - View the secret in YAML format
   - Decode the base64-encoded values
   - Understand what "encoding" vs "encryption" means

3. **Understand Security Implications**
   - Research: Are Kubernetes Secrets encrypted at rest by default?
   - What is etcd encryption and when should you enable it?

<details>
<summary>💡 Hints</summary>

**Creating Secrets:**
There are multiple ways to create secrets:
- `kubectl create secret generic` - from literals or files
- `kubectl create secret docker-registry` - for image pull secrets
- `kubectl create secret tls` - for TLS certificates

**Useful Commands:**
```bash
# Create from literals
kubectl create secret generic <name> --from-literal=key=value

# View secret
kubectl get secret <name> -o yaml

# Decode base64 (Linux/Mac)
echo "<base64-string>" | base64 -d
```

**Security Model:**
Kubernetes Secrets are base64-encoded, NOT encrypted by default. Anyone with API access can decode them. For production:
- Enable etcd encryption at rest
- Use RBAC to limit secret access
- Consider external secret managers (Vault, AWS Secrets Manager, etc.)

**Resources:**
- [Kubernetes Secrets Concepts](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Encrypting Secret Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)

</details>

---

### Task 2 — Helm-Managed Secrets (3 pts)

**Objective:** Integrate secrets into your Helm chart and inject them into your application.

**Requirements:**

1. **Create Secret Template**
   - Add `templates/secrets.yaml` to your Helm chart
   - Define secret values in `values.yaml` (with placeholder defaults)
   - Use proper templating for secret name and labels

2. **Inject Secrets as Environment Variables**
   - Update your deployment to consume the secret
   - Use `envFrom` with `secretRef` for all keys
   - OR use individual `env` entries with `secretKeyRef`

3. **Verify Secret Injection**
   - Deploy the updated chart
   - Exec into the pod and verify environment variables
   - Ensure secrets are not visible in `kubectl describe pod`

4. **Add Resource Limits**
   - Configure CPU and memory requests/limits in your deployment
   - Use values.yaml for configurability
   - Apply Kubernetes resource management best practices

<details>
<summary>💡 Hints</summary>

**Secret Template Structure:**
Your `templates/secrets.yaml` should:
- Use the standard `v1` API and `Secret` kind
- Include proper metadata with templated name and labels
- Reference values from `values.yaml`
- Use `stringData` for plain text (auto-encoded) or `data` for pre-encoded

**Consuming Secrets in Deployment:**
There are two patterns for environment variables:

Pattern 1 - All keys from secret:
```yaml
envFrom:
  - secretRef:
      name: {{ include "mychart.fullname" . }}-secret
```

Pattern 2 - Specific keys:
```yaml
env:
  - name: DATABASE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: secret-name
        key: password
```

**Resource Limits:**
```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "200m"
```

**Security Note:**
Never commit real secrets to Git! Use:
- Placeholder values in `values.yaml`
- `--set` flag during install
- External secret management (next task)

**Resources:**
- [Managing Secrets with kubectl](https://kubernetes.io/docs/tasks/configmap-secret/managing-secret-using-kubectl/)
- [Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)

</details>

---

### Task 3 — HashiCorp Vault Integration (3 pts)

**Objective:** Deploy HashiCorp Vault and configure it to inject secrets into your application.

**Requirements:**

1. **Install Vault via Helm**
   - Add HashiCorp Helm repository
   - Install Vault in dev mode (for learning purposes)
   - Verify all Vault pods are running

2. **Configure Vault**
   - Enable KV secrets engine (v2)
   - Create a secret path for your application
   - Store at least two key-value pairs

3. **Configure Kubernetes Authentication**
   - Enable Kubernetes auth method in Vault
   - Create a policy that grants read access to your secret path
   - Create a role bound to your application's service account

4. **Enable Vault Agent Injection**
   - Add Vault annotations to your deployment
   - Configure the agent to inject secrets as files
   - Verify secrets are available inside the pod at the expected path

<details>
<summary>💡 Hints</summary>

**Installing Vault:**
```bash
# Add repo
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Install in dev mode (NOT for production!)
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

**Vault Configuration Steps:**
1. Exec into Vault pod: `kubectl exec -it vault-0 -- /bin/sh`
2. Vault is auto-initialized in dev mode
3. Use `vault` CLI inside the pod

**Key Vault Commands:**
```bash
# Enable KV v2
vault secrets enable -path=secret kv-v2

# Create secret
vault kv put secret/myapp/config username="admin" password="secret123"

# Enable K8s auth
vault auth enable kubernetes

# Configure K8s auth (get values from your cluster)
vault write auth/kubernetes/config \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
```

**Policy and Role:**
You need to:
1. Create a policy that allows reading from your secret path
2. Create a role that binds the policy to your service account

**Vault Agent Annotations:**
Add these to your deployment's pod template:
```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "your-role"
  vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
```

**Resources:**
- [Vault Helm Chart](https://developer.hashicorp.com/vault/docs/platform/k8s/helm)
- [Vault K8s Sidecar Tutorial](https://developer.hashicorp.com/vault/tutorials/kubernetes/kubernetes-sidecar)
- [Agent Annotations](https://developer.hashicorp.com/vault/docs/platform/k8s/injector/annotations)

</details>

---

### Task 4 — Documentation (2 pts)

**Objective:** Document your secret management implementation.

**Create `k8s/SECRETS.md` with:**

1. **Kubernetes Secrets**
   - Output of creating and viewing your secret
   - Decoded secret values demonstration
   - Explanation of base64 encoding vs encryption

2. **Helm Secret Integration**
   - Chart structure showing secrets.yaml
   - How secrets are consumed in deployment
   - Verification output (env vars in pod, excluding actual values)

3. **Resource Management**
   - Resource limits configuration
   - Explanation of requests vs limits
   - How to choose appropriate values

4. **Vault Integration**
   - Vault installation verification (`kubectl get pods`)
   - Policy and role configuration (sanitized)
   - Proof of secret injection (show file exists, path structure)
   - Explanation of the sidecar injection pattern

5. **Security Analysis**
   - Comparison: K8s Secrets vs Vault
   - When to use each approach
   - Production recommendations

---

## Bonus Task — Vault Agent Templates (2.5 pts)

**Objective:** Use Vault Agent templating to render secrets in custom formats.

**Requirements:**

1. **Implement Template Annotation**
   - Use `vault.hashicorp.com/agent-inject-template-*` annotation
   - Render secrets as a configuration file (e.g., `.env` format or JSON)
   - Include multiple secrets in a single rendered file

2. **Dynamic Secret Rotation**
   - Research how Vault Agent handles secret updates
   - Document the refresh mechanism
   - Explain `vault.hashicorp.com/agent-inject-command` annotation

3. **Named Templates for Environment Variables**
   - Create a named template in `_helpers.tpl` for common environment variables
   - Use `include` to reference it in your deployment
   - Demonstrate DRY principle in Helm charts

<details>
<summary>💡 Hints</summary>

**Template Annotation Example:**
```yaml
vault.hashicorp.com/agent-inject-template-config: |
  {{- with secret "secret/data/myapp/config" -}}
  DATABASE_URL={{ .Data.data.db_url }}
  API_KEY={{ .Data.data.api_key }}
  {{- end -}}
```

**Named Template Pattern:**
In `_helpers.tpl`:
```yaml
{{- define "mychart.envVars" -}}
- name: APP_ENV
  value: {{ .Values.environment }}
- name: LOG_LEVEL
  value: {{ .Values.logLevel }}
{{- end -}}
```

In deployment:
```yaml
env:
  {{- include "mychart.envVars" . | nindent 12 }}
```

**Resources:**
- [Vault Agent Templates](https://developer.hashicorp.com/vault/docs/platform/k8s/injector/annotations#vault-hashicorp-com-agent-inject-template)
- [Helm Named Templates](https://helm.sh/docs/chart_template_guide/named_templates/)

</details>

**Bonus Documentation:**
- Template annotation configuration
- Rendered secret file content
- Named template implementation
- Benefits of templating approach

---

## Checklist

### Task 1 — Kubernetes Secrets Fundamentals (2 pts)
- [ ] Secret created via kubectl
- [ ] Secret viewed and decoded
- [ ] Security implications understood and documented

### Task 2 — Helm-Managed Secrets (3 pts)
- [ ] `templates/secrets.yaml` created
- [ ] Secrets defined in `values.yaml`
- [ ] Deployment updated to consume secrets
- [ ] Environment variables verified in pod
- [ ] Resource limits configured

### Task 3 — HashiCorp Vault Integration (3 pts)
- [ ] Vault installed via Helm
- [ ] KV secrets engine configured
- [ ] Kubernetes auth method enabled
- [ ] Policy and role created
- [ ] Vault Agent injection working
- [ ] Secrets accessible in pod

### Task 4 — Documentation (2 pts)
- [ ] `k8s/SECRETS.md` complete
- [ ] All sections documented with evidence
- [ ] Security analysis included

### Bonus — Vault Agent Templates (2.5 pts)
- [ ] Template annotation implemented
- [ ] Custom format rendering working
- [ ] Named templates in `_helpers.tpl`
- [ ] Documentation complete

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **K8s Secrets** | 2 pts | Create, view, decode, understand security |
| **Helm Secrets** | 3 pts | Template, inject, verify, resource limits |
| **Vault Integration** | 3 pts | Install, configure, auth, inject |
| **Documentation** | 2 pts | Complete SECRETS.md with evidence |
| **Bonus** | 2.5 pts | Templates, named templates, rotation |
| **Total** | 12.5 pts | 10 pts required + 2.5 pts bonus |

**Grading:**
- **10/10:** Working Vault injection, proper Helm secrets, good documentation
- **8-9/10:** Vault working, minor issues with docs or config
- **6-7/10:** K8s secrets work, Vault partially configured
- **<6/10:** Secrets not properly implemented, missing Vault setup

---

## Resources

<details>
<summary>📚 Official Documentation</summary>

- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [HashiCorp Vault](https://developer.hashicorp.com/vault/docs)
- [Vault Helm Chart](https://developer.hashicorp.com/vault/docs/platform/k8s/helm)
- [Vault K8s Injector](https://developer.hashicorp.com/vault/docs/platform/k8s/injector)

</details>

<details>
<summary>🎓 Tutorials</summary>

- [Vault on Kubernetes Deployment Guide](https://developer.hashicorp.com/vault/tutorials/kubernetes/kubernetes-raft-deployment-guide)
- [Injecting Secrets into Kubernetes Pods](https://developer.hashicorp.com/vault/tutorials/kubernetes/kubernetes-sidecar)
- [Kubernetes Auth Method](https://developer.hashicorp.com/vault/docs/auth/kubernetes)

</details>

<details>
<summary>🔐 Security Best Practices</summary>

- [Kubernetes Secrets Best Practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)
- [Encrypting Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [External Secrets Operator](https://external-secrets.io/) - Alternative approach

</details>

---

## Looking Ahead

- **Lab 12:** ConfigMaps for non-sensitive configuration and persistent storage
- **Lab 13:** ArgoCD will deploy your secured Helm charts via GitOps
- **Lab 14:** Progressive delivery with Argo Rollouts
- **Lab 15:** StatefulSets with persistent storage

---

**Good luck!** 🔐

> **Remember:** Never commit real secrets to version control. Use placeholder values and inject real secrets at deployment time. In production, always use an external secret manager like Vault.
