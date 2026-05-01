# Documentation

## StatefulSet Overview

### Why StatefulSet

It is used when pods need stable identity and storage, like each pod keeping its own data and name even after restart.

### Differences from Deployment

Key differences:
- deployment pods are interchangeable and can change names/storage after restarts, while statefulset pods have fixed names (pod-0, pod-1) and their own persistent storage.

When to use Deployment vs StatefulSet: 
- deployment is used for stateless apps (like web servers), and statefulset for apps that need stable data and identity (like databases).

Examples of stateful workloads: 
- databases like mysql/postgresql, message queues, systems like elasticsearch

### Headless Services

What is a headless service (clusterIP: None)?
- a service without a cluster ip that lets you directly access individual pods instead of load balancing

How DNS works with StatefulSets? 
- each pod gets its own dns name like pod-0.service-name.namespace.svc.cluster.local, and they can be addressed individually

## Resource Verification

### Output of kubectl get pod,sts,svc,pvc

## Network Identity

### DNS resolution outputs

## Per-Pod Storage Evidence 

### Different visit counts per pod

## Persistence Test

### data survives pod deletion