# Lab 13 — GitOps with ArgoCD

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-GitOps-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-ArgoCD%202.13-informational)

> Implement GitOps continuous deployment using ArgoCD for declarative, version-controlled Kubernetes deployments.

## Overview

GitOps is the practice of using Git as the single source of truth for declarative infrastructure and applications. ArgoCD is a declarative, GitOps continuous delivery tool for Kubernetes that automatically syncs your cluster state with your Git repository.

**What You'll Learn:**
- GitOps principles and benefits
- ArgoCD installation and configuration
- Application deployment via ArgoCD
- Multi-environment deployment patterns
- Auto-sync and self-healing mechanisms
- Sync policies and strategies

**Building On:** Your Helm chart from Labs 10-12 will be deployed and managed by ArgoCD.

**Tech Stack:** ArgoCD 2.13+ | Kubernetes | Helm | GitOps

---

## Tasks

### Task 1 — ArgoCD Installation & Setup (2 pts)

**Objective:** Install ArgoCD and access the management interface.

**Requirements:**

1. **Install ArgoCD via Helm**
   - Add the ArgoCD Helm repository
   - Create a dedicated namespace for ArgoCD
   - Install ArgoCD with appropriate configuration
   - Wait for all components to be ready

2. **Access ArgoCD UI**
   - Set up port forwarding to the ArgoCD server
   - Retrieve the initial admin password
   - Log in to the ArgoCD web interface
   - Explore the UI layout and features

3. **Install ArgoCD CLI**
   - Install the `argocd` CLI tool for your platform
   - Log in via CLI
   - Verify connection with basic commands

<details>
<summary>💡 Hints</summary>

**Installation Commands:**
```bash
# Add Helm repo
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# Create namespace and install
kubectl create namespace argocd
helm install argocd argo/argo-cd --namespace argocd

# Wait for pods
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s
```

**Accessing UI:**
```bash
# Port forward (keep running)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get initial password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Access at https://localhost:8080
# Username: admin
```

**CLI Installation:**
- **macOS:** `brew install argocd`
- **Linux:** Download from GitHub releases
- Check [ArgoCD CLI Installation](https://argo-cd.readthedocs.io/en/stable/cli_installation/)

**CLI Login:**
```bash
argocd login localhost:8080 --insecure
# Use admin and the password retrieved above
```

**Resources:**
- [ArgoCD Getting Started](https://argo-cd.readthedocs.io/en/stable/getting_started/)
- [ArgoCD Helm Chart](https://github.com/argoproj/argo-helm/tree/main/charts/argo-cd)

</details>

---

### Task 2 — Application Deployment (3 pts)

**Objective:** Deploy your application using ArgoCD's declarative Application resource.

**Requirements:**

1. **Create ArgoCD Application Manifest**
   - Create `k8s/argocd/` directory
   - Create `application.yaml` defining your app
   - Specify:
     - Source: Your Git repository and path to Helm chart
     - Destination: Target cluster and namespace
     - Sync policy: Manual initially

2. **Deploy the Application**
   - Apply the Application manifest
   - Observe the application in ArgoCD UI
   - Understand the sync status indicators

3. **Perform Initial Sync**
   - Trigger manual sync via UI or CLI
   - Watch the deployment progress
   - Verify all resources are created
   - Access your application

4. **Test GitOps Workflow**
   - Make a change to your Helm chart (e.g., replica count)
   - Commit and push to your repository
   - Observe ArgoCD detecting the drift
   - Sync the changes

<details>
<summary>💡 Hints</summary>

**Application Manifest Structure:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/<username>/<repo>.git
    targetRevision: <branch>
    path: <path-to-helm-chart>
    helm:
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

**Key Fields:**
- `repoURL`: Your GitHub repository URL
- `targetRevision`: Branch name (e.g., `main`, `lab13`)
- `path`: Path to Helm chart within repo (e.g., `k8s/app-python`)
- `destination.namespace`: Where to deploy

**Apply and Sync:**
```bash
kubectl apply -f k8s/argocd/application.yaml

# CLI sync
argocd app sync python-app

# Check status
argocd app get python-app
```

**Sync Status:**
- **Synced:** Cluster matches Git
- **OutOfSync:** Git has changes not applied
- **Unknown:** Unable to determine state
- **Healthy/Degraded/Progressing:** Application health

**Resources:**
- [ArgoCD Application Specification](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/)
- [Sync Options](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/)

</details>

---

### Task 3 — Multi-Environment Deployment (3 pts)

**Objective:** Deploy your application to multiple environments (dev/prod) with different configurations.

**Requirements:**

1. **Create Namespaces**
   - Create `dev` and `prod` namespaces
   - These will host separate instances of your app

2. **Create Environment-Specific Applications**
   - Create `application-dev.yaml` using `values-dev.yaml`
   - Create `application-prod.yaml` using `values-prod.yaml`
   - Different replica counts, resource limits per environment

3. **Enable Auto-Sync for Dev**
   - Configure automatic sync for the dev environment
   - Add `automated` sync policy
   - Enable `selfHeal` and `prune` options

4. **Keep Prod Manual**
   - Production remains manual sync
   - Understand why this is a best practice
   - Document the deployment workflow difference

5. **Verify Both Environments**
   - Both apps visible in ArgoCD UI
   - Different configurations applied
   - Resources deployed to correct namespaces

<details>
<summary>💡 Hints</summary>

**Create Namespaces:**
```bash
kubectl create namespace dev
kubectl create namespace prod
```

**Dev Application with Auto-Sync:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: python-app-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/<username>/<repo>.git
    targetRevision: <branch>
    path: <path-to-helm-chart>
    helm:
      valueFiles:
        - values-dev.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

**Prod Application (Manual):**
```yaml
# Similar but without automated sync policy
syncPolicy:
  syncOptions:
    - CreateNamespace=true
  # No automated block = manual sync
```

**Sync Policy Options:**
- `automated`: Enable auto-sync
- `prune`: Delete resources removed from Git
- `selfHeal`: Revert manual cluster changes
- Without `automated`: Manual sync required

**Why Manual for Prod?**
- Change review before deployment
- Controlled release timing
- Compliance requirements
- Rollback planning

**Verification:**
```bash
kubectl get pods -n dev
kubectl get pods -n prod
argocd app list
```

</details>

---

### Task 4 — Self-Healing & Sync Policies (2 pts)

**Objective:** Test and understand ArgoCD's self-healing and drift detection capabilities.

**Requirements:**

1. **Test Self-Healing (Dev Environment)**
   - Manually scale the deployment:
     ```bash
     kubectl scale deployment <name> -n dev --replicas=5
     ```
   - Observe ArgoCD detecting the drift
   - Watch it automatically revert to Git-defined state
   - Document the behavior with timestamps

2. **Test Pod Deletion**
   - Delete a pod in dev namespace
   - Observe Kubernetes recreating the pod
   - Note: This is Kubernetes behavior, not ArgoCD
   - Understand the difference between:
     - Kubernetes self-healing (pod recreation)
     - ArgoCD self-healing (configuration drift)

3. **Test Configuration Drift**
   - Manually edit a resource (e.g., add a label)
   - Observe ArgoCD diff view
   - Watch self-heal revert the change

4. **Document Sync Behavior**
   - Explain when ArgoCD syncs vs when Kubernetes heals
   - What triggers ArgoCD sync?
   - What is the sync interval?

<details>
<summary>💡 Hints</summary>

**Self-Healing Test:**
```bash
# Scale manually
kubectl scale deployment python-app-dev -n dev --replicas=5

# Watch ArgoCD revert (if selfHeal enabled)
kubectl get pods -n dev -w

# Check ArgoCD status
argocd app get python-app-dev
```

**View Drift:**
```bash
argocd app diff python-app-dev
```

**Pod Deletion Test:**
```bash
# Delete a pod
kubectl delete pod -n dev -l app.kubernetes.io/name=python-app

# Kubernetes recreates it immediately (ReplicaSet controller)
kubectl get pods -n dev -w
```

**Key Difference:**
- **Kubernetes Self-Healing:** ReplicaSet/Deployment ensures desired pod count
- **ArgoCD Self-Healing:** Reverts cluster state to match Git state

**Sync Interval:**
ArgoCD polls Git every 3 minutes by default. You can also:
- Use webhooks for immediate sync
- Manually trigger sync
- Configure different intervals

**Resources:**
- [Automated Sync Policy](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/)
- [Self Heal](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/#automatic-self-healing)

</details>

**Documentation Required in `k8s/ARGOCD.md`:**

1. **ArgoCD Setup**
   - Installation verification
   - UI access method
   - CLI configuration

2. **Application Configuration**
   - Application manifests
   - Source and destination configuration
   - Values file selection

3. **Multi-Environment**
   - Dev vs Prod configuration differences
   - Sync policy differences and rationale
   - Namespace separation

4. **Self-Healing Evidence**
   - Manual scale test with before/after
   - Pod deletion test
   - Configuration drift test
   - Explanation of behaviors

5. **Screenshots**
   - ArgoCD UI showing both applications
   - Sync status
   - Application details view

---

## Bonus Task — ApplicationSet (2.5 pts)

**Objective:** Use ApplicationSet to generate multiple applications from a single template.

**Requirements:**

1. **Understand ApplicationSet**
   - Research ApplicationSet generators
   - Understand use cases (multi-cluster, multi-tenant, mono-repo)

2. **Implement List Generator**
   - Create an ApplicationSet that generates both dev and prod apps
   - Use the List generator to define environment-specific parameters
   - Replace individual Application manifests

3. **Implement Git Directory Generator (Optional)**
   - If you have multiple apps in your repo
   - Use Git directory generator to auto-discover apps

4. **Document the Pattern**
   - Benefits of ApplicationSet over individual Applications
   - When to use which generator type
   - Scaling considerations

<details>
<summary>💡 Hints</summary>

**ApplicationSet with List Generator:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: python-app-set
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - env: dev
            namespace: dev
            valuesFile: values-dev.yaml
            autoSync: true
          - env: prod
            namespace: prod
            valuesFile: values-prod.yaml
            autoSync: false
  template:
    metadata:
      name: 'python-app-{{env}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/<username>/<repo>.git
        targetRevision: <branch>
        path: <path-to-helm-chart>
        helm:
          valueFiles:
            - '{{valuesFile}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        # Conditional sync policy based on env
        # Note: This requires templating tricks or separate ApplicationSets
```

**Git Directory Generator:**
```yaml
generators:
  - git:
      repoURL: https://github.com/<username>/<repo>.git
      revision: HEAD
      directories:
        - path: k8s/*
```

**Generators Available:**
- List: Explicit list of parameters
- Cluster: Multi-cluster deployments
- Git: Based on Git files/directories
- Matrix: Combine multiple generators
- Merge: Merge generator outputs

**Resources:**
- [ApplicationSet Documentation](https://argo-cd.readthedocs.io/en/stable/user-guide/application-set/)
- [Generators](https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Generators/)

</details>

**Bonus Documentation:**
- ApplicationSet manifest
- Generator configuration explanation
- Generated Applications screenshot
- Comparison with individual Applications

---

## Checklist

### Task 1 — ArgoCD Installation & Setup (2 pts)
- [ ] ArgoCD installed via Helm
- [ ] All pods running in argocd namespace
- [ ] UI accessible via port-forward
- [ ] Admin password retrieved
- [ ] CLI installed and logged in

### Task 2 — Application Deployment (3 pts)
- [ ] `k8s/argocd/` directory created
- [ ] Application manifest created
- [ ] Application visible in ArgoCD UI
- [ ] Initial sync completed
- [ ] App accessible and working
- [ ] GitOps workflow tested

### Task 3 — Multi-Environment Deployment (3 pts)
- [ ] Dev and prod namespaces created
- [ ] Dev application with auto-sync
- [ ] Prod application with manual sync
- [ ] Different configurations per environment
- [ ] Both apps deployed and verified

### Task 4 — Self-Healing & Documentation (2 pts)
- [ ] Manual scale test performed
- [ ] Self-healing observed
- [ ] Pod deletion test performed
- [ ] Configuration drift test done
- [ ] `k8s/ARGOCD.md` complete

### Bonus — ApplicationSet (2.5 pts)
- [ ] ApplicationSet manifest created
- [ ] Multiple apps generated from template
- [ ] Generator configuration documented
- [ ] Benefits documented

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Installation** | 2 pts | ArgoCD running, UI/CLI accessible |
| **App Deployment** | 3 pts | Application manifest, sync working |
| **Multi-Environment** | 3 pts | Dev/prod with different configs |
| **Self-Healing** | 2 pts | Tests performed, documented |
| **Bonus** | 2.5 pts | ApplicationSet implementation |
| **Total** | 12.5 pts | 10 pts required + 2.5 pts bonus |

**Grading:**
- **10/10:** Full GitOps workflow, multi-env, self-healing documented
- **8-9/10:** ArgoCD works, minor issues with multi-env or docs
- **6-7/10:** Basic app deployment, missing multi-env or self-healing
- **<6/10:** ArgoCD not properly configured, apps not syncing

---

## Resources

<details>
<summary>📚 Official Documentation</summary>

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [ArgoCD Operator Manual](https://argo-cd.readthedocs.io/en/stable/operator-manual/)
- [Application CRD](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/)
- [Sync Policies](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/)

</details>

<details>
<summary>🎓 GitOps Concepts</summary>

- [GitOps Principles](https://opengitops.dev/)
- [GitOps Working Group](https://github.com/gitops-working-group/gitops-working-group)
- [ArgoCD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)

</details>

<details>
<summary>🛠️ Advanced Topics</summary>

- [ApplicationSet](https://argo-cd.readthedocs.io/en/stable/user-guide/application-set/)
- [Sync Waves](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/)
- [Resource Hooks](https://argo-cd.readthedocs.io/en/stable/user-guide/resource_hooks/)
- [Notifications](https://argo-cd.readthedocs.io/en/stable/operator-manual/notifications/)

</details>

---

## Looking Ahead

- **Lab 14:** Progressive delivery with Argo Rollouts
- **Lab 15:** StatefulSets for stateful applications
- **Lab 16:** Monitoring your GitOps deployments

---

**Good luck!** 🔄

> **Remember:** GitOps means Git is the source of truth. Any changes should go through Git, not direct `kubectl` commands. ArgoCD ensures your cluster always matches what's in Git.
