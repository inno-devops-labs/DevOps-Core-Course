# Lab 11 — Kubernetes Secrets & HashiCorp Vault

**Student:** Alexander Rozanov  
**Email:** al.rozanov@innopolis.university  
**Group:** CBS-02  

---

## 1. Repository Layout

This lab is implemented in the following repository locations:

- `k8s/app-python-chart/values.yaml` — default chart configuration extended with secret and Vault settings
- `k8s/app-python-chart/templates/secrets.yaml` — Kubernetes Secret template for application credentials
- `k8s/app-python-chart/templates/serviceaccount.yaml` — dedicated service account for Vault integration
- `k8s/app-python-chart/templates/deployment.yaml` — deployment updated to consume Kubernetes Secret and optionally enable Vault injection
- `k8s/app-python-chart/templates/_helpers.tpl` — helper templates for common names and secret/service account naming
- `k8s/SECRETS.md` — documentation file required by the assignment
- `k8s/docs/screenshots/` — screenshots with terminal evidence

The lab extends the Helm chart from Lab 10 and keeps using the Python application image:

```text
akakii98/devops-info-python:latest
```

---

## 2. Lab Objective

The purpose of this lab was to add proper secret management to the Kubernetes deployment created earlier. Two approaches were implemented:

1. **Native Kubernetes Secrets** for storing and injecting application credentials.
2. **HashiCorp Vault** for external secret storage and dynamic injection into pods through the Vault Agent Injector sidecar pattern.

This workflow demonstrates the difference between simple platform-native secret delivery and a more production-oriented external secret management approach.

---

## 3. Task 1 — Kubernetes Secrets Fundamentals

The first task focused on creating and examining a native Kubernetes Secret. A secret named `app-credentials` was created with two keys:

- `username`
- `password`

The secret was created using the imperative `kubectl create secret generic` workflow. After creation, the resource was inspected in YAML format to confirm that the values were stored under the `data:` section.

The stored values were then decoded with `base64 -d`. This demonstrates an important point of the Kubernetes security model: **native Secret values are encoded, not meaningfully encrypted by default**. Base64 only changes the representation of the data and should not be treated as confidential storage by itself.

For production systems, additional controls are required:
- encryption of secret data at rest in etcd,
- RBAC restrictions for secret access,
- audit and rotation procedures,
- or use of an external secret manager such as Vault.

### Evidence — Secret creation
![Secret creation](screenshots/task_1_creds_create.png)

### Evidence — Secret YAML output
![Secret YAML output](screenshots/task_1_get_creds.png)

### Evidence — Base64 decoding
![Decoded secret values](screenshots/task_1_creds_decode.png)

---

## 4. Task 2 — Helm-Managed Secrets

The Helm chart from Lab 10 was extended with a dedicated secret template:

- `k8s/app-python-chart/templates/secrets.yaml`

The chart now supports application credentials through the `secret:` section in `values.yaml`. Placeholder defaults are kept in version-controlled values, while real secret values can be passed during installation with `--set`, which avoids storing live credentials inside the repository.

A dedicated `ServiceAccount` template was also added because it is later required for Vault authentication.

The application deployment was updated so that:
- standard configuration such as `PORT` still comes from chart values,
- secret keys are injected through `envFrom.secretRef`,
- resource requests and limits remain configurable from Helm values,
- health probes from previous labs are preserved.

The chart was validated with `helm lint` and `helm template`, and then installed or upgraded in the target namespace. The resulting release and Kubernetes resources confirm that the Secret, ServiceAccount, Deployment, and Service were rendered correctly.

Validation inside the running pod showed that the secret values were available as environment variables. At the same time, the `kubectl describe pod` output did not print the actual credential values directly, which is the expected behavior when environment variables are sourced from a Secret reference.

### Evidence — Helm validation
![Helm lint and template output](screenshots/task_2_helm_lint_tempalte.png)

### Evidence — Helm upgrade with secret values
![Helm upgrade output](screenshots/task_2_helm_upgrade.png)

### Evidence — Release and resource status
![Helm status and Kubernetes resources](screenshots/task_2_helm_status_check.png)

### Evidence — Secret verification inside the pod
![Exec and describe pod output](screenshots/task_2_exec_describe.png)

---

## 5. Task 3 — HashiCorp Vault Integration

The third task introduced externalized secret management using HashiCorp Vault. The official HashiCorp Helm repository was added, the repository index was updated, and Vault was installed in a dedicated namespace in development mode with the injector enabled.

After deployment, the following parts were configured inside Vault:

- Kubernetes authentication method,
- KV v2 secret engine,
- a secret path for the application,
- a policy allowing read access to that path,
- a role bound to the application service account and namespace.

The application Helm chart already contained optional Vault-related values and deployment annotations. By enabling the `vault.enabled` flag during Helm upgrade, the deployment was reconfigured to request secret injection through Vault Agent Injector. This resulted in a pod with Vault-related annotations and injected secret files under the standard `/vault/secrets/` path.

Verification was performed in several ways:
- checking that Vault pods were running,
- confirming the written Vault secret data,
- rolling out the updated application deployment,
- inspecting the pod description,
- listing the injected files,
- reading the rendered secret file from `/vault/secrets/config`.

This demonstrates the sidecar injection pattern: Vault Agent authenticates to Vault on behalf of the pod, retrieves the allowed secret material, and writes it into the container filesystem without baking real credentials into the image or static deployment manifests.

### Evidence — Vault repository and installation
![Vault Helm repository and install](screenshots/task_3_helm_repo_add_update_create.png)

### Evidence — Vault pods running
![Vault Kubernetes status](screenshots/task_3_kube_stat.png)

### Evidence — Vault configuration, policy, role and secret data
![Vault configuration part 1](screenshots/task_3_vault_info_1.png)

### Evidence — Vault configuration continuation
![Vault configuration part 2](screenshots/task_3_vault_info_2.png)

### Evidence — Application upgrade with Vault enabled
![Helm upgrade and rollout status](screenshots/task_3_helm_upgrade_rollout.png)

### Evidence — Pod description with Vault integration
![Pod description after Vault injection](screenshots/task_3_kube_describe.png)

### Evidence — Injected secret file
![Reading injected secret file from /vault/secrets/config](screenshots/task_3_get_secrets_from_config.png)

---

## 6. Task 4 — Documentation

The assignment requires dedicated documentation describing the secret-management implementation. For this purpose, a separate file was prepared:

- `k8s/SECRETS.md`

It contains:
- the native Kubernetes Secret workflow,
- Helm secret templating and injection details,
- resource management notes,
- Vault deployment and configuration summary,
- security analysis and production recommendations.

This keeps the lab report focused on the performed workflow while the operational details remain close to the Kubernetes configuration itself.

---

## 7. Design Summary

### 7.1 Native Secret support in the chart
The chart now creates a standard Kubernetes `Secret` resource and allows credentials to be supplied at install or upgrade time. This provides a simple and portable way to support secret-backed deployments.

### 7.2 Secret consumption through environment variables
The deployment consumes secret data using `envFrom.secretRef`, which makes all keys from the Secret available inside the container with minimal manifest duplication.

### 7.3 Resource control preserved
CPU and memory requests/limits from previous labs were preserved and remain configurable through Helm values. This keeps the deployment aligned with Kubernetes resource management best practices.

### 7.4 Vault integration is optional and values-driven
Vault integration is controlled by chart values and pod annotations. This means the same chart can be used both with standard Kubernetes Secrets only and with Vault-backed injection enabled.

---

## 8. Security Notes

Native Kubernetes Secrets are suitable for simple local deployments and for understanding how secret references work in Kubernetes, but they are not a complete enterprise secret-management solution on their own.

HashiCorp Vault adds several important advantages:
- centralized secret storage,
- access control and policy enforcement,
- secret delivery independent from Git-managed values files,
- better alignment with production secret-management practices.

For real production usage, the preferred model is:
- minimal use of static secret values in Git,
- Kubernetes RBAC restrictions,
- etcd encryption at rest,
- centralized secret lifecycle management through Vault or an equivalent external secret system.

---

## 9. Conclusion

Lab 11 successfully extended the Helm-based Kubernetes deployment with two layers of secret management. First, native Kubernetes Secrets were created, inspected, decoded, templated in Helm, and injected into the application as environment variables. Second, HashiCorp Vault was installed and configured to inject secret material into the pod filesystem through the Vault Agent Injector.

As a result, the application deployment now demonstrates both the basic Kubernetes mechanism for handling credentials and a more advanced external secret-management workflow that is closer to real production practices.
