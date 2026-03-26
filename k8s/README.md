# Kubernetes Deployment Report

## 1. Architecture Overview

### Deployment Architecture

The Kubernetes implementation consists of a three-tier application deployment:

- **Deployment (`devops-app`)**: Manages the application pods with a replica count of 3 for high availability
- **Service (`devops-app-service`)**: Exposes the deployment using a NodePort service on port 30080
- **Pods**: Three replicas running the Flask-based `devops-info-service` container

### Component Breakdown

| Component | Type | Details |
|-----------|------|---------|
| **Application Pods** | Deployment | 3/5 replicas with RollingUpdate strategy |
| **Service** | NodePort | Port 80 → 8000 (target), NodePort 30080 |
| **Image** | Container | `saddogsec/devops-info-service:latest` |
| **Networking** | Cluster IP | Pods communicate internally on port 8000 |

### Resource Allocation Strategy

Each pod is allocated:
- **CPU**: 100m (request) to 500m (limit)
- **Memory**: 128Mi (request) to 512Mi (limit)

This allocation ensures:
- Guaranteed minimum resources for each replica
- Headroom for burst traffic handling
- Protection against resource starvation of other workloads

### Networking Flow

```
External Request (port 30080)
    ↓
NodePort Service (devops-app-service)
    ↓
ClusterIP Routing (port 80)
    ↓
Pod (port 8000)
    ↓
Flask Application
```

## 2. Manifest Files

### Deployment Manifest (`deployment.yml`)

**Key Configuration Choices:**

1. **Replicas: 3/5**
   - Ensures high availability across nodes
   - Provides fault tolerance for node failures

2. **RollingUpdate Strategy**
   ```yaml
   maxUnavailable: 1
   maxSurge: 1
   ```
   - Allows continuous availability during updates
   - Maximum downtime: 0 pods (one becomes unavailable, one becomes available)

3. **Security Context**
   ```yaml
   runAsNonRoot: true
   runAsUser: 1000
   fsGroup: 1000
   ```
   - Prevents running as root for security
   - Ensures proper file system permissions

4. **Environment Variables**
   - `APP_ENV: production` - Sets application environment
   - `LOG_LEVEL: info` - Configurable logging verbosity
   - `PORT: 8000` - Application port

### Service Manifest (`service.yml`)

**Key Configuration Choices:**

1. **Type: NodePort**
   - Exposes service on each node's IP at port 30080
   - Enables external access without LoadBalancer
   - Cost-effective for development/testing environments

2. **Port Mapping**
   - `port: 80` - Internal service port
   - `targetPort: 8000` - Container port
   - `nodePort: 30080` - External access port

3. **Labels and Selectors**
   - Ensures proper service discovery
   - Matches deployment pod labels for routing

## 3. Deployment Evidence

### Initial Deployment

```bash
kubectl apply -f deployment.yml
deployment.apps/devops-app created
```

### Deployment Progress

```bash
kubectl get deployments
NAME         READY   UP-TO-DATE   AVAILABLE   AGE
devops-app   0/3     3            0           8s
devops-app   3/3     3            3           53s
```

### Running Pods

```bash
kubectl get pods
NAME                          READY   STATUS    RESTARTS   AGE
devops-app-598dc5b58c-g8mrs   1/1     Running   0          58s
devops-app-598dc5b58c-jjcmw   1/1     Running   0          58s
devops-app-598dc5b58c-s4d7d   1/1     Running   0          58s
```

### Deployment Details

**Deployment Configuration:**
```
Name:                   devops-app
Namespace:              default
Replicas:               3 desired | 3 updated | 3 total | 3 available
StrategyType:           RollingUpdate
RollingUpdateStrategy:  1 max unavailable, 1 max surge
```

**Container Configuration:**
```
Image:      saddogsec/devops-info-service:latest
Port:       8000/TCP
Resources:
  Requests: cpu: 100m, memory: 128Mi
  Limits:   cpu: 500m, memory: 512Mi
```

### Application Verification

**Service Access Test:**
```bash
curl -v http://192.168.56.21:30080
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "framework": "Flask",
    "description": "DevOps course info service"
  },
  "endpoints": [
    {"method": "GET", "path": "/", "description": "Service information"},
    {"method": "GET", "path": "/health", "description": "Health check"}
  ],
  "runtime": {
    "current_time": "2026-03-26T11:32:26.784Z",
    "uptime_human": "0 hours, 8 minutes",
    "uptime_seconds": 511
  },
  "system": {
    "hostname": "devops-app-598dc5b58c-jjcmw",
    "architecture": "x86_64",
    "cpu_count": 2,
    "platform": "Linux",
    "python_version": "3.12.13"
  }
}
```

## 4. Operations Performed

### Deployment Commands

```bash
# Apply deployment
kubectl apply -f deployment.yml

# Monitor deployment progress
kubectl get deployments
kubectl get pods

# View detailed deployment configuration
kubectl describe deployment devops-app
```

### Scaling Demonstration

**Scaling from 3 to 5 replicas:**

```bash
kubectl get pods -w
NAME                          READY   STATUS              RESTARTS   AGE
devops-app-598dc5b58c-62qnh   0/1     ContainerCreating   0          5s
devops-app-598dc5b58c-jh6q5   0/1     ContainerCreating   0          5s
devops-app-598dc5b58c-g8mrs   1/1     Running             0          25m
devops-app-598dc5b58c-jjcmw   1/1     Running             0          25m
devops-app-598dc5b58c-s4d7d   1/1     Running             0          25m
devops-app-598dc5b58c-62qnh   1/1     Running             0          16s
devops-app-598dc5b58c-jh6q5   1/1     Running             0          16s
```

**Final State (5 replicas):**
```bash
kubectl get pods
NAME                          READY   STATUS    RESTARTS   AGE
devops-app-598dc5b58c-62qnh   1/1     Running   0          37s
devops-app-598dc5b58c-g8mrs   1/1     Running   0          26m
devops-app-598dc5b58c-jh6q5   1/1     Running   0          37s
devops-app-598dc5b58c-jjcmw   1/1     Running   0          26m
devops-app-598dc5b58c-s4d7d   1/1     Running   0          26m

kubectl rollout status deployment/devops-app
deployment "devops-app" successfully rolled out
```

### Rolling Update Demonstration

**Update Deployment:**
```bash
kubectl apply -f deployment.yml
```

**Rollout Status:**
```bash
kubectl rollout status deployment/devops-app
Waiting for deployment "devops-app" rollout to finish: 2 of 3 updated replicas are available...
deployment "devops-app" successfully rolled out
```

**Revision History:**
```bash
kubectl rollout history deployment/devops-app
deployment.apps/devops-app
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

**Rollback:**
```bash
kubectl rollout undo deployment/devops-app
deployment.apps/devops-app rolled back

kubectl rollout history deployment/devops-app
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
```

### Service Access Verification

**External Access via NodePort:**
- **Node IP**: 192.168.56.21
- **NodePort**: 30080
- **Endpoint**: `http://192.168.56.21:30080`

## 5. Production Considerations

### Health Checks Implementation

**Liveness Probe:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

**Rationale:**
- `initialDelaySeconds: 30` - Allows container startup time
- `periodSeconds: 10` - Frequent health monitoring
- `failureThreshold: 3` - Tolerates 3 consecutive failures before restart
- Ensures container is restarted if it becomes unresponsive

**Readiness Probe:**
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 5
```

**Rationale:**
- `initialDelaySeconds: 5` - Quick readiness checks after container starts
- `periodSeconds: 5` - More frequent than liveness for traffic routing
- `failureThreshold: 5` - Allows longer time to become ready
- Prevents traffic routing to pods that aren't ready to serve

**Note:** The service manifest shows the health endpoint works correctly, returning JSON service information.

### Resource Limits Rationale

**CPU Allocation:**
- **Request: 100m** - Guarantees 0.1 CPU core per pod
- **Limit: 500m** - Allows burst up to 0.5 CPU cores during high load
- Rationale: Flask applications are typically I/O bound, not CPU intensive

**Memory Allocation:**
- **Request: 128Mi** - Ensures minimum memory for Python runtime
- **Limit: 512Mi** - Allows heap growth for application objects
- Rationale: Flask with minimal dependencies typically uses 50-200MB

**Protection Strategy:**
- Prevents resource starvation of other workloads
- OOMKills pods exceeding memory limits
- CPU throttling when limits are reached

### Production Improvements

**Recommended Enhancements:**

1. **Image Tagging**
   ```yaml
   # Change from:
   image: saddogsec/devops-info-service:latest
   
   # To:
   image: saddogsec/devops-info-service:v1.0.0
   ```
   - Use semantic versioning instead of `:latest`
   - Ensures reproducible deployments
   - Enables proper rollback capabilities

2. **Configuration Management**
   - Move environment variables to ConfigMaps
   - Store secrets (API keys, passwords) in Kubernetes Secrets
   - Externalize configuration for different environments

3. **High Availability**
   - Implement PodDisruptionBudget
   - Use podAntiAffinity for node distribution
   - Deploy across multiple availability zones

4. **Network Policies**
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   ```
   - Restrict ingress/egress traffic
   - Implement zero-trust networking

5. **Persistent Storage**
   - Add PersistentVolumeClaims if application needs persistence
   - Use StatefulSet for stateful applications

### Monitoring and Observability Strategy

**Metrics Collection:**
- **Prometheus** - Cluster metrics and custom application metrics
- **cAdvisor** - Container resource utilization
- **Node Exporter** - Host-level metrics

**Log Aggregation:**
- **Fluentd/Fluent Bit** - Collect logs from all pods
- **Elasticsearch** - Log storage and indexing
- **Kibana** - Log visualization and analysis
- Or use cloud providers' managed services (CloudWatch, Stackdriver)

**Distributed Tracing:**
- **Jaeger** or **Zipkin** - Track requests across microservices
- **OpenTelemetry** - Standard for observability data

**Alerting:**
- **AlertManager** - Alert routing and deduplication
- Configure alerts for:
  - Pod restarts > threshold
  - Resource utilization > threshold
  - Deployment unavailable replicas
  - High error rates

**Health Monitoring:**
- External monitoring (UptimeKuma, Pingdom)
- Synthetic transactions to verify endpoints
- SLA/SLO tracking

### Service Access Summary

The application is accessible via:
- **NodePort**: `http://<node-ip>:30080`
- All nodes in the cluster expose the service
- Load balancers or Ingress controllers can be added for production
- TLS termination at Ingress level recommended for production

## Challenges

No real challenges were encountered during the lab solution.
