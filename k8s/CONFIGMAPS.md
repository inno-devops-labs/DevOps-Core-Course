# ConfigMaps & Persistent Volumes

## Application Changes

The application was extended to support a visit counter. Each request to the root endpoint (`/`) increments a counter stored in a file located at `/data/visits`. A new endpoint (`/visits`) was added to return the current number of visits.

The counter is read from the file on each request, incremented, and written back. If the file does not exist, the counter starts from 0. This ensures the application can recover its state after restarts when persistent storage is used.

Local testing was performed using Docker with a mounted volume to verify that the counter persists across container restarts.

---

## ConfigMap Implementation

A ConfigMap was created to externalize application configuration.

### File-based ConfigMap

A `config.json` file is stored in the Helm chart under `files/` and loaded into a ConfigMap using Helm templating. This ConfigMap is mounted into the container at `/config/config.json`.

ConfigMap runs evidence: 
```bash
abraham_barrett@Abrahams-MacBook-Air k8s % kubectl get configmap
NAME                    DATA   AGE
devops-service-config   1      20m
devops-service-env      2      20m
kube-root-ca.crt        1      9d
abraham_barrett@Abrahams-MacBook-Air k8s % 
```
Verification:
```bash
kubectl exec <pod> -- cat /config/config.json
```
Output: 
```bash
{
  "appName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "enableMetrics": true
  }
}
```
Environment Variables ConfigMap
A second ConfigMap provides configuration as environment variables. These are injected into the container using ```envFrom```.
Verification:

```bash
kubectl exec <pod> -- printenv | grep APP_
```
Output: 
```bash
APP_ENV=dev
APP_NAME=devops-info-service
```
## Persistent Volume
A PersistentVolumeClaim (PVC) is used to store application data.
* Access mode: ReadWriteOnce
* Storage size: 100Mi
* Storage class: default (Minikube)

The PVC is mounted into the container at ```/data```, where the application stores the visits counter file.

Verification:
```bash
kubectl get pvc
kubectl exec <pod> -- cat /data/visits #output 5
```
Output
```bash
abraham_barrett@Abrahams-MacBook-Air k8s % kubectl get pvc  
NAME                  STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
devops-service-data   Bound    pvc-ea7bac47-a4d0-4340-a16e-1ff2feaf9be4   100Mi      RWO            standard       <unset>                 117s
```
```bash

```
## Persistence Test
Access the application multiple times to increase the counter:
```bash
curl localhost:30560
curl localhost:30560
```
Check the current value:
```bash
kubectl exec <pod> -- cat /data/visits
```

Output
```bash
7
```

Delete the pod:
```bash
kubectl delete pod <pod>
```
Wait for a new pod to start and verify the value again:
```bash
kubectl exec <new-pod> -- cat /data/visits
```
```bash
7
```
The counter value remains the same, confirming that data persists across pod restarts.

## ConfigMap vs Secret
* ConfigMaps are used for non-sensitive configuration data such as application settings, feature flags, and environment variables.
* Secrets are used for sensitive data such as passwords, tokens, and API keys. Unlike ConfigMaps, Secrets should be protected and ideally encrypted.
### In this project:
* ConfigMaps are used for application configuration
* Secrets (from the previous lab) are used for credentials

## Summary
ConfigMaps allow externalizing configuration from the application, making it reusable across environments. Persistent Volumes ensure that important data, such as the visit counter, is not lost when pods are restarted. Together, these features make the application more production-ready and resilient.