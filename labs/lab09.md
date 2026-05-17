# Lab 9 — Kubernetes Fundamentals

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Kubernetes-blue)
![points](https://img.shields.io/badge/points-12%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-Kubernetes-informational)

> Deploy your containerized applications to Kubernetes using declarative manifests and production best practices.

## Overview

Take your Docker images from previous labs and deploy them to Kubernetes. Learn container orchestration fundamentals, declarative configuration, and production deployment patterns.

**What You'll Learn:**
- Kubernetes core concepts and architecture
- Writing production-ready manifests
- Deployments, Services, and networking
- Health checks and resource management
- Scaling and updates

**Tech Stack:** Kubernetes 1.33+ | kubectl | minikube or kind | YAML

---

## Tasks

### Task 1 — Local Kubernetes Setup (2 pts)

**Objective:** Set up a local Kubernetes cluster and understand core concepts.

**Requirements:**

1. **Learn Kubernetes Fundamentals**
   - Study core concepts (Pods, Deployments, Services, Namespaces)
   - Understand control plane and worker node architecture
   - Learn the declarative vs imperative approach

2. **Install Tools**
   - Install `kubectl` (Kubernetes CLI)
   - Install local cluster: `minikube` OR `kind`
   - Verify installation with cluster info commands

3. **Cluster Setup**
   - Start local cluster
   - Verify all components are running
   - Explore cluster with kubectl commands

<details>
<summary>💡 Kubernetes Concepts</summary>

**Core Resources:**
- **Pod**: Smallest deployable unit, contains one or more containers
- **Deployment**: Manages replica sets and rolling updates
- **Service**: Exposes Pods as network service with stable endpoint
- **Namespace**: Virtual cluster for resource isolation

**Why Kubernetes?**
- Automatic scaling and load balancing
- Self-healing (restart failed containers)
- Rolling updates and rollbacks
- Service discovery and networking
- Resource management and scheduling

**Local Development Options:**
- **minikube**: Full-featured, runs in VM or Docker
- **kind**: Lightweight, runs in Docker containers, great for CI/CD

**Key Concepts to Research:**
- Desired state vs actual state
- Controllers and reconciliation loops
- Labels and selectors
- Declarative configuration (YAML manifests)

**Resources:**
- [What is Kubernetes](https://kubernetes.io/docs/concepts/overview/)
- [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/quick-reference/)
- [Install Tools](https://kubernetes.io/docs/tasks/tools/)

</details>

<details>
<summary>💡 Essential kubectl Commands</summary>

**Cluster Information:**
```bash
kubectl cluster-info
kubectl get nodes
kubectl get namespaces
```

**Resource Management:**
```bash
kubectl get pods
kubectl get deployments
kubectl get services
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

**Apply vs Create:**
- `kubectl apply` - Declarative, idempotent, preferred
- `kubectl create` - Imperative, fails if exists

</details>

**Documentation Required:**
- Terminal output showing successful cluster setup
- Output of `kubectl cluster-info` and `kubectl get nodes`
- Brief explanation of your chosen tool (minikube/kind) and why

---

### Task 2 — Application Deployment (3 pts)

**Objective:** Create a Deployment manifest for your Python app with production best practices.

**Requirements:**

1. **Create Deployment Manifest**
   - File: `k8s/deployment.yml`
   - Use your Docker image from Lab 2
   - Minimum 3 replicas
   - Include resource requests and limits
   - Add liveness and readiness probes
   - Use labels for organization

2. **Production Best Practices**
   - Non-root container (should already be in your image)
   - Rolling update strategy
   - Proper container port configuration
   - Environment variables if needed

<details>
<summary>💡 Deployment Manifest Structure</summary>

**Essential Sections:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: your-app-name
  labels:
    app: your-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: your-app
  template:
    metadata:
      labels:
        app: your-app
    spec:
      containers:
      - name: your-app
        image: your-dockerhub-username/your-app:latest
        # Add: ports, resources, probes
```

**Key Fields to Research:**
- `replicas`: Number of Pod copies
- `selector.matchLabels`: How Deployment finds its Pods
- `template`: Pod specification
- `resources`: CPU/memory requests and limits
- `livenessProbe`: Is container healthy?
- `readinessProbe`: Is container ready for traffic?

**Resources:**
- [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Health Checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

</details>

<details>
<summary>💡 Health Checks (Probes)</summary>

**Types of Probes:**
- **Liveness**: Restart container if failing
- **Readiness**: Remove from service if not ready
- **Startup**: For slow-starting containers

**Probe Methods:**
- HTTP GET (common for web apps)
- TCP Socket
- Exec command

**Example Configuration Pattern:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 3
```

**Note:** You may need to add `/health` endpoint to your app.

</details>

<details>
<summary>💡 Resource Management</summary>

**Why Set Resources?**
- Prevents resource starvation
- Enables proper scheduling
- Protects cluster stability

**Pattern:**
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

**CPU Units:**
- `1000m` = 1 CPU core
- `100m` = 0.1 CPU core

**Memory Units:**
- `Mi` = Mebibyte (1024-based)
- `Gi` = Gibibyte

</details>

**Test Your Deployment:**
```bash
kubectl apply -f k8s/deployment.yml
kubectl get deployments
kubectl get pods
kubectl describe deployment <name>
```

---

### Task 3 — Service Configuration (2 pts)

**Objective:** Create a Service to expose your Deployment.

**Requirements:**

1. **Create Service Manifest**
   - File: `k8s/service.yml`
   - Type: `NodePort` (for local cluster access)
   - Target your Deployment's Pods using labels
   - Expose the correct port

2. **Verify Connectivity**
   - Apply Service manifest
   - Access app using `minikube service` command or port-forward
   - Test all endpoints work

<details>
<summary>💡 Service Types</summary>

**Service Types:**
- **ClusterIP** (default): Internal cluster access only
- **NodePort**: Exposes service on each node's IP at a static port
- **LoadBalancer**: Cloud provider load balancer
- **ExternalName**: CNAME record for external service

**For Local Development:**
Use `NodePort` - allows external access without cloud provider.

**Service Manifest Pattern:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: your-app-service
spec:
  type: NodePort
  selector:
    app: your-app  # Must match Deployment labels
  ports:
    - protocol: TCP
      port: 80        # Service port
      targetPort: 8000  # Container port
      nodePort: 30080   # Optional: specific node port (30000-32767)
```

**Resources:**
- [Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Connect Applications with Services](https://kubernetes.io/docs/tutorials/services/connect-applications-service/)

</details>

<details>
<summary>💡 Accessing Your Service</summary>

**Minikube:**
```bash
minikube service <service-name>
minikube service <service-name> --url
```

**kind or other:**
```bash
kubectl port-forward service/<service-name> 8080:80
```

**Verify:**
```bash
kubectl get services
kubectl describe service <service-name>
kubectl get endpoints
```

</details>

---

### Task 4 — Scaling and Updates (2 pts)

**Objective:** Demonstrate scaling and rolling updates.

**Requirements:**

1. **Scaling**
   - Scale your deployment to 5 replicas
   - Verify all replicas are running
   - Document the process

2. **Rolling Updates**
   - Update your image tag or change a configuration
   - Apply the updated manifest
   - Watch the rollout process
   - Verify zero downtime

3. **Rollback**
   - Demonstrate rollback capability
   - Show rollout history

<details>
<summary>💡 Scaling Operations</summary>

**Declarative (Preferred):**
Edit `deployment.yml` replicas field, then:
```bash
kubectl apply -f k8s/deployment.yml
```

**Imperative (Quick Testing):**
```bash
kubectl scale deployment/<name> --replicas=5
```

**Watch Scaling:**
```bash
kubectl get pods -w
kubectl rollout status deployment/<name>
```

</details>

<details>
<summary>💡 Rolling Updates</summary>

**How Rolling Updates Work:**
- Creates new Pods with updated spec
- Waits for them to be ready
- Terminates old Pods gradually
- Ensures minimum availability

**Update Strategy:**
```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Extra pods during update
      maxUnavailable: 0  # Ensure availability
```

**Useful Commands:**
```bash
kubectl apply -f k8s/deployment.yml
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
kubectl rollout undo deployment/<name>
```

**Resources:**
- [Performing Rolling Update](https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/)

</details>

---

### Task 5 — Documentation (3 pts)

**Objective:** Document your Kubernetes implementation.

Create `k8s/README.md` with these sections:

**Required Sections:**

1. **Architecture Overview**
   - Diagram or description of your deployment architecture
   - How many Pods, which Services, networking flow
   - Resource allocation strategy

2. **Manifest Files**
   - Brief description of each manifest
   - Key configuration choices
   - Why you chose specific values (replicas, resources, etc.)

3. **Deployment Evidence**
   - `kubectl get all` output
   - `kubectl get pods,svc` with detailed view
   - `kubectl describe deployment <name>` showing replicas and strategy
   - Screenshot or curl output showing app working

4. **Operations Performed**
   - Commands used to deploy
   - Scaling demonstration output
   - Rolling update demonstration output
   - Service access method and verification

5. **Production Considerations**
   - What health checks did you implement and why?
   - Resource limits rationale
   - How would you improve this for production?
   - Monitoring and observability strategy

6. **Challenges & Solutions**
   - Issues encountered
   - How you debugged (logs, describe, events)
   - What you learned about Kubernetes

---

## Bonus Task — Ingress with TLS (2.5 pts)

**Objective:** Deploy multiple applications with Ingress routing and HTTPS.

**Requirements:**

1. **Multi-App Deployment**
   - Deploy second application (use different image or different config)
   - Create Deployment and Service for second app

2. **Ingress Controller**
   - Enable Ingress in minikube or install in kind
   - Verify Ingress controller is running

3. **Ingress Resources**
   - Create Ingress manifest with path-based routing
   - Route `/app1` to first service
   - Route `/app2` to second service

4. **TLS Configuration**
   - Generate self-signed certificate
   - Create TLS Secret
   - Configure Ingress for HTTPS

<details>
<summary>💡 Ingress Concepts</summary>

**What is Ingress?**
HTTP/HTTPS routing layer sitting in front of Services. Provides:
- URL-based routing
- TLS/SSL termination
- Virtual hosting
- Load balancing

**Ingress vs Service:**
- Service: L4 (TCP/UDP) load balancing
- Ingress: L7 (HTTP/HTTPS) routing

**Ingress Controller:**
Software that implements Ingress rules. Popular options:
- nginx-ingress (most common)
- Traefik
- HAProxy
- Cloud provider specific

**Enable in Minikube:**
```bash
minikube addons enable ingress
```

**Install in kind:**
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

**Important Note:** The Ingress NGINX controller reaches end of life in March 2026. For production deployments, consider migrating to the [Gateway API](https://gateway-api.sigs.k8s.io/), which is the future of Kubernetes traffic management.

**Resources:**
- [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Ingress Controllers](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/)
- [Set up Ingress on Minikube](https://kubernetes.io/docs/tasks/access-application-cluster/ingress-minikube/)
- [Gateway API](https://gateway-api.sigs.k8s.io/) - Next generation traffic management

</details>

<details>
<summary>💡 Path-Based Routing</summary>

**Ingress Manifest Pattern:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: apps-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: local.example.com
    http:
      paths:
      - path: /app1
        pathType: Prefix
        backend:
          service:
            name: app1-service
            port:
              number: 80
      - path: /app2
        pathType: Prefix
        backend:
          service:
            name: app2-service
            port:
              number: 80
```

**Path Types:**
- `Exact`: Exact match
- `Prefix`: Matches URL path prefix

**Testing:**
Add to `/etc/hosts`:
```
<minikube-ip> local.example.com
```

Access:
```bash
curl http://local.example.com/app1
curl http://local.example.com/app2
```

</details>

<details>
<summary>💡 TLS Configuration</summary>

**Generate Self-Signed Certificate:**
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=local.example.com/O=local.example.com"
```

**Create TLS Secret:**
```bash
kubectl create secret tls tls-secret \
  --key tls.key \
  --cert tls.crt
```

**Update Ingress:**
```yaml
spec:
  tls:
  - hosts:
    - local.example.com
    secretName: tls-secret
  rules:
  # ... your rules
```

**Test HTTPS:**
```bash
curl -k https://local.example.com/app1
```

</details>

**Documentation Required:**
- Both applications deployed and accessible via Ingress
- Ingress manifest with routing rules
- TLS configuration and certificate creation steps
- Terminal output showing all resources
- curl commands demonstrating routing works
- Explanation of Ingress benefits over NodePort Services

---

## Checklist

### Task 1 — Local Kubernetes Setup (2 pts)
- [ ] kubectl and local cluster (minikube/kind) installed
- [ ] Cluster running successfully
- [ ] Terminal output showing cluster info
- [ ] Documentation of setup process

### Task 2 — Application Deployment (3 pts)
- [ ] `k8s/deployment.yml` exists
- [ ] Uses Docker image from Lab 2
- [ ] Minimum 3 replicas configured
- [ ] Resource requests and limits defined
- [ ] Liveness and readiness probes configured
- [ ] Deployment successfully running

### Task 3 — Service Configuration (2 pts)
- [ ] `k8s/service.yml` exists
- [ ] Service type: NodePort
- [ ] Correct label selectors
- [ ] Service accessible from outside cluster
- [ ] All endpoints responding

### Task 4 — Scaling and Updates (2 pts)
- [ ] Scaling to 5 replicas demonstrated
- [ ] Rolling update performed and documented
- [ ] Rollback capability demonstrated
- [ ] Zero downtime verified

### Task 5 — Documentation (3 pts)
- [ ] `k8s/README.md` complete with all sections
- [ ] Architecture overview provided
- [ ] Terminal output evidence included
- [ ] Operations demonstrated
- [ ] Production considerations discussed
- [ ] Challenges and learnings documented

### Bonus — Ingress with TLS (2.5 pts)
- [ ] Second application deployed
- [ ] Ingress controller enabled
- [ ] Ingress manifest with path-based routing
- [ ] TLS certificate generated
- [ ] HTTPS working
- [ ] Documentation complete

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Setup** | 2 pts | Cluster running, tools installed |
| **Deployment** | 3 pts | Production-ready manifest with probes and resources |
| **Service** | 2 pts | Properly exposed and accessible |
| **Scaling & Updates** | 2 pts | Demonstrated operations |
| **Documentation** | 3 pts | Complete and thorough |
| **Bonus** | 2.5 pts | Ingress with TLS |
| **Total** | 14.5 pts | 12 pts required + 2.5 pts bonus |

**Grading:**
- **12/12:** All requirements met, excellent documentation, deep understanding
- **10-11/12:** Working deployment, good practices, solid documentation
- **8-9/12:** Basic deployment works, missing some best practices
- **<8/12:** Missing requirements, no health checks, poor documentation

---

## Resources

<details>
<summary>📚 Official Kubernetes Documentation</summary>

- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [Kubernetes Concepts](https://kubernetes.io/docs/concepts/)
- [kubectl Reference](https://kubernetes.io/docs/reference/kubectl/)
- [Kubernetes API Reference](https://kubernetes.io/docs/reference/kubernetes-api/)

</details>

<details>
<summary>🎓 Learning Resources</summary>

- [Kubernetes Basics Tutorial](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
- [Learn Kubernetes Basics](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
- [Configuration Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

</details>

<details>
<summary>🛠️ Tools</summary>

- [kubectl](https://kubernetes.io/docs/tasks/tools/) - Kubernetes CLI
- [minikube](https://minikube.sigs.k8s.io/docs/) - Local Kubernetes
- [kind](https://kind.sigs.k8s.io/) - Kubernetes in Docker
- [k9s](https://k9scli.io/) - Terminal UI for Kubernetes
- [kubectx/kubens](https://github.com/ahmetb/kubectx) - Context and namespace switcher

</details>

<details>
<summary>🔍 Debugging Resources</summary>

- [Debug Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/)
- [Debug Services](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/)
- [Troubleshooting Applications](https://kubernetes.io/docs/tasks/debug/debug-application/)

</details>

---

## Looking Ahead

- **Lab 10:** Helm charts for package management
- **Lab 11:** Secrets management with Vault
- **Lab 12:** ConfigMaps and application configuration
- **Lab 13:** ArgoCD for GitOps deployments
- **Lab 14:** Progressive delivery with Argo Rollouts
- **Lab 15:** StatefulSets for stateful applications
- **Lab 16:** Kubernetes monitoring and observability

---

**Good luck!** 🚢

> **Remember:** Kubernetes is declarative. Define desired state, let the control plane make it happen. Use health checks and resource limits from day one.
