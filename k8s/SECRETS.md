# Kubernetes Secrets & HashiCorp Vault Report

## Task 1 & 2: Kubernetes Secrets

### 1. Secret Decoding

During the lab, standard Kubernetes Secrets were created. Although the values in the manifests appear to be encrypted, they are actually just Base64-encoded.

**Decoding example:**

* Username: `YWRtaW4=` → `admin`
* Password: `c3VwZXJzZWNyZXQxMjM=` → `supersecret123`

**Command to verify manually:**

```bash
echo "YWRtaW4=" | base64 --decode
```

### 2. Injecting Secrets into the Application

Secrets were injected into the application using the `envFrom` block in `deployment.yaml`. This allows the application to access them as regular environment variables.

**Result:**

When running the following command inside the container:

```bash
kubectl exec <pod-name> -- printenv
```

You can see environment variables such as `dbUsername` and `dbPassword`.

---

## Task 3: HashiCorp Vault Secret Injection

### 1. Integration Setup

For a more secure approach to secret management, HashiCorp Vault was used. Secrets are stored in an external secure storage and injected into pods dynamically using the Vault Agent Injector.

**Main steps performed:**

* Configured access policy `devops-app-policy`
* Created role `devops-app-role` bound to a ServiceAccount
* Added annotations to the Deployment to enable injection

### 2. Verifying Secret Injection

Unlike standard Kubernetes Secrets, Vault does not inject secrets directly into environment variables by default. Instead, it creates a file inside the pod's virtual filesystem.

**Verification command:**

```bash
kubectl exec <pod-name> -c devops-app -- cat /vault/secrets/config
```

**Output example:**

```bash
export DB_USER="admin"
export DB_PASS="very-secret-password"
```

---

## Task 4: Comparison and Conclusions

| Feature   | Kubernetes Secrets                 | HashiCorp Vault                       |
| --------- | ---------------------------------- | ------------------------------------- |
| Storage   | Stored in etcd (often unencrypted) | Stored in encrypted storage           |
| Security  | Base64 encoding only               | Full AES encryption                   |
| Lifecycle | Static data                        | Supports dynamic (temporary) secrets  |
| Auditing  | Limited to API server logs         | Detailed audit of every secret access |

### Why is Vault more secure?

* **Encryption by default:** Even if an attacker gains access to the server disks, they cannot read secrets without the master key.
* **Centralization:** Secrets are not duplicated across Kubernetes namespaces but stored in a single secure system.
* **Sidecar mechanism:** The application accesses secrets only at runtime using a short-lived token, reducing the attack surface.
