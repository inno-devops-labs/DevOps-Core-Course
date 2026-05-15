Lab 15 — StatefulSets \& Persistent Storage



Task 1 — StatefulSet Concepts



StatefulSet Guarantees

Stable, unique network identifiers (pod-0, pod-1, pod-2)



Stable, persistent storage per pod



Ordered, graceful deployment and scaling



Ordered, automated rolling updates



StatefulSet vs Deployment

Aspect	Deployment	StatefulSet

Pod naming	Random suffix	Ordinal index (app-0, app-1)

Storage	Shared PVC or ephemeral	Each pod has its own PVC

Scaling	Parallel, unordered	Ordered (app-0, then app-1)

Network identity	Not stable	Stable DNS names

Use case	Stateless apps	Databases, message queues, stateful apps

When to use StatefulSet

Applications that need stable network identity



Distributed databases (Cassandra, MongoDB, ZooKeeper)



Message queues (Kafka, RabbitMQ)



Any application where each instance has its own storage



Headless Service

A headless service (clusterIP: None) provides DNS records for each pod directly, enabling pod-to-pod communication via stable DNS names like pod-name.service-name.namespace.svc.cluster.local



Task 2 — Convert Deployment to StatefulSet



StatefulSet Template

yaml

apiVersion: apps/v1

kind: StatefulSet

metadata:

&#x20; name: devops-info-service

spec:

&#x20; serviceName: devops-info-service-headless

&#x20; replicas: 2

&#x20; selector:

&#x20;   matchLabels:

&#x20;     app: devops-info-service

&#x20; template:

&#x20;   metadata:

&#x20;     labels:

&#x20;       app: devops-info-service

&#x20;   spec:

&#x20;     containers:

&#x20;     - name: app

&#x20;       image: devops-info-service:lab12

&#x20;       volumeMounts:

&#x20;       - name: data

&#x20;         mountPath: /data

&#x20; volumeClaimTemplates:

&#x20; - metadata:

&#x20;     name: data

&#x20;   spec:

&#x20;     accessModes:

&#x20;     - ReadWriteOnce

&#x20;     resources:

&#x20;       requests:

&#x20;         storage: 100Mi

Headless Service

yaml

apiVersion: v1

kind: Service

metadata:

&#x20; name: devops-info-service-headless

spec:

&#x20; clusterIP: None

&#x20; selector:

&#x20;   app: devops-info-service

&#x20; ports:

&#x20; - port: 80

&#x20;   targetPort: 5000

Installation

helm install devops-info-service . -f values-statefulset.yaml



Verification

kubectl get statefulset

NAME READY AGE

devops-info-service 2/2 18s



kubectl get pods

NAME READY STATUS RESTARTS AGE

devops-info-service-0 1/1 Running 0 23s

devops-info-service-1 1/1 Running 0 15s



kubectl get pvc

NAME STATUS VOLUME CAPACITY ACCESS MODES

data-devops-info-service-0 Bound pvc-xxx 100Mi RWO

data-devops-info-service-1 Bound pvc-yyy 100Mi RWO



Task 3 — Headless Service \& Pod Identity



DNS Resolution Test

kubectl exec -it devops-info-service-0 -- cat /etc/hosts

10.244.0.135 devops-info-service-0.devops-info-service-headless.default.svc.cluster.local



Cross-Pod Communication

kubectl exec -it devops-info-service-0 -- python -c "import urllib.request; print(urllib.request.urlopen('http://devops-info-service-1.devops-info-service-headless.default.svc.cluster.local:5000/health').read())"

{"config\_file":true,"status":"healthy","timestamp":"2026-05-15T05:52:36.854899+00:00","uptime\_seconds":141}



Per-Pod Storage Isolation

Pod 0 visits:

kubectl exec -it devops-info-service-0 -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000/visits').read())"

{"count":2,"file\_path":"/data/visits","message":"Total visits: 2","persistent":true}



Pod 1 visits:

kubectl exec -it devops-info-service-1 -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000/visits').read())"

{"count":1,"file\_path":"/data/visits","message":"Total visits: 1","persistent":true}



Persistence Test

Delete pod 0:

kubectl delete pod devops-info-service-0



Wait for pod to restart:

kubectl get pods -w



Check visits after restart:

kubectl exec -it devops-info-service-0 -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000/visits').read())"

{"count":2,"file\_path":"/data/visits","message":"Total visits: 2","persistent":true}



Task 4 — Update Strategies



RollingUpdate with Partition

values-statefulset.yaml:



yaml

statefulset:

&#x20; enabled: true

&#x20; updateStrategy:

&#x20;   type: RollingUpdate

&#x20;   rollingUpdate:

&#x20;     partition: 1

With partition=1, only pods with index >=1 are updated. Pod 0 remains on old version.



OnDelete Strategy

yaml

statefulset:

&#x20; enabled: true

&#x20; updateStrategy:

&#x20;   type: OnDelete

Pods are only updated when manually deleted. This gives full control over when each pod is updated.



Update Strategy Comparison

Strategy	When pods update	Use case

RollingUpdate (partition=0)	All pods sequentially	Normal updates

RollingUpdate (partition=N)	Pods with index >= N	Canary testing

OnDelete	Only when manually deleted	Maximum control

Resource Verification Summary

StatefulSet

kubectl get sts

NAME READY AGE

devops-info-service 2/2 5m



Pods

kubectl get pods -l app.kubernetes.io/instance=devops-info-service

NAME READY STATUS RESTARTS AGE

devops-info-service-0 1/1 Running 0 5m

devops-info-service-1 1/1 Running 0 5m



PVCs

kubectl get pvc

NAME STATUS CAPACITY ACCESS MODES

data-devops-info-service-0 Bound 100Mi RWO

data-devops-info-service-1 Bound 100Mi RWO



Services

kubectl get svc | findstr headless

devops-info-service-headless ClusterIP None <none> 80/TCP



Commands Reference

Install StatefulSet: helm install devops-info-service . -f values-statefulset.yaml

Get StatefulSet: kubectl get sts

Get pods: kubectl get pods -l app.kubernetes.io/instance=devops-info-service

Get PVCs: kubectl get pvc

Check DNS: kubectl exec -it devops-info-service-0 -- cat /etc/hosts

Check visits: kubectl exec -it devops-info-service-0 -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000/visits').read())"

Delete pod: kubectl delete pod devops-info-service-0

Update StatefulSet: helm upgrade devops-info-service . -f values-statefulset.yaml --set image.tag=newtag

Rollback: helm rollback devops-info-service



Conclusion



Lab 15 completed with:



StatefulSet with stable network identities (pod-0, pod-1)



Headless service for direct pod DNS resolution



VolumeClaimTemplates creating per-pod PVCs



Per-pod storage isolation proven (different visit counts)



Persistence verified after pod deletion



Ordered deployment and scaling demonstrated

