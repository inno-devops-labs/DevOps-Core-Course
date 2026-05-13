# Documentation

## Application Changes

### Description of visits counter implementation

visits counter is a global integer that increases every time / endpoint is called. it writes the value into a file (visits) so it can survive pod restarts via pvc.

### New endpoint documentation

/visits returns the current stored counter value from data/visits file

### Local testing evidence with Docker

Here you can see the counter value persistence across restarts.
![](./../docs/screenshots/lab12-shots/counter.png)

## ConfigMap Implementation

### ConfigMap template structure

Helm ConfigMap loads a local config.json file via .Files.Get, so the whole json is injected into the cluster as one config object

### config.json content

it contains basic app metadata like name, environment, and feature flags (debug, metrics) plus log level settings

### How ConfigMap is mounted as file

the ConfigMap is mounted as a volume at /config, so inside the container we can read /config/config.json as a normal file.

### How ConfigMap provides environment variables

by using envFrom: configMapRef to inject keys like APP_NAME, APP_ENV, and LOG_LEVEL directly as environment variables.


### Verification outputs

- File content inside pod (cat /config/config.json)

```bash
(devops) fountainer@Veronicas-MacBook-Air app_python % kubectl exec mysecretrelease-app-python-696f97599c-5llgh -- cat /config/config.json
Defaulted container "app-python" out of: app-python, vault-agent, vault-agent-init (init)
{
  "app_name": "my-app",
  "environment": "dev",
  "feature_flags": {
    "debug": true,
    "metrics": true
  },
  "settings": {
    "log_level": "info"
  }
}%   
```

- Environment variables in pod

```bash
(devops) fountainer@Veronicas-MacBook-Air app_python % kubectl exec mysecretrelease-app-python-696f97599c-5llgh -- printenv | grep APP_   
Defaulted container "app-python" out of: app-python, vault-agent, vault-agent-init (init)
APP_ENV=dev
APP_NAME=my-app
MYSECRETRELEASE_APP_PYTHON_SERVICE_SERVICE_PORT=80
MYSECRETRELEASE_APP_PYTHON_SERVICE_PORT_80_TCP=tcp://10.103.123.105:80
MYSECRETRELEASE_APP_PYTHON_SERVICE_PORT_80_TCP_PROTO=tcp
MYSECRETRELEASE_APP_PYTHON_SERVICE_PORT_80_TCP_PORT=80
MYSECRETRELEASE_APP_PYTHON_SERVICE_SERVICE_HOST=10.103.123.105
MYSECRETRELEASE_APP_PYTHON_SERVICE_PORT=tcp://10.103.123.105:80
MYSECRETRELEASE_APP_PYTHON_SERVICE_PORT_80_TCP_ADDR=10.103.123.105
(devops) fountainer@Veronicas-MacBook-Air app_python % kubectl exec mysecretrelease-app-python-696f97599c-5llgh -- printenv | grep LOG_LEVEL
Defaulted container "app-python" out of: app-python, vault-agent, vault-agent-init (init)
LOG_LEVEL=info
(devops) fountainer@Veronicas-MacBook-Air app_python % 
```


## Persistent Volume

### PVC configuration explanation

PVC requests a small storage size (100Mi) and creates a persistent volume that is mounted into the pod at /app/data to store the visits file.

### Access modes and storage class discussion

ReadWriteOnce is used because only one pod needs to write to the volume, and storageClass is optional so it uses the cluster default.

### Volume mount configuration

the volume is mounted into the container at /app/data, and the app writes visits file there so data stays after pod restarts/recreations

### Persistence test evidence:

```bash
(devops) fountainer@Veronicas-MacBook-Air app_python % kubectl exec mysecretrelease-app-python-7b6579656c-z6r7b -- cat /app/data/visits
Defaulted container "app-python" out of: app-python, vault-agent, vault-agent-init (init)
22%                                                                                                                                             
(devops) fountainer@Veronicas-MacBook-Air app_python % kubectl delete pod mysecretrelease-app-python-7b6579656c-z6r7b
pod "mysecretrelease-app-python-7b6579656c-z6r7b" deleted
(devops) fountainer@Veronicas-MacBook-Air app_python % kubectl get pod
NAME                                          READY   STATUS    RESTARTS      AGE
mysecretrelease-app-python-7b6579656c-b2tzf   2/2     Running   0             60s
vault-0                                       1/1     Running   3 (84m ago)   8d
vault-agent-injector-848dd747d7-qvgl2         1/1     Running   3 (85m ago)   8d
(devops) fountainer@Veronicas-MacBook-Air app_python % kubectl exec mysecretrelease-app-python-7b6579656c-b2tzf -- cat /app/data/visits
Defaulted container "app-python" out of: app-python, vault-agent, vault-agent-init (init)
22%                                                                                                                                             
(devops) fountainer@Veronicas-MacBook-Air app_python % 
```

## ConfigMap vs Secret

### When to use ConfigMap

ConfigMap is used for non-sensitive configuration like app name, environment, log level, and feature flags.

### When to use Secret

secret is used for sensitive data like username, password, or anything that should not be visible in plain text

### Key differences

configMap is plain text and not encrypted, while Secret is base64 encoded and used for sensitive data.

## Additional Outputs:

### kubectl get configmap,pvc output

```bash
(devops) fountainer@Veronicas-MacBook-Air app_python % kubectl get configmap,pvc
NAME                                          DATA   AGE
configmap/kube-root-ca.crt                    1      22d
configmap/mysecretrelease-app-python-config   1      7m2s
configmap/mysecretrelease-app-python-env      3      7m2s

NAME                                                    STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/mysecretrelease-app-python-data   Bound    pvc-42d4685f-8463-4434-8959-0bacd5d972b6   100Mi      RWO            standard       <unset>                 7m2s
(devops) fountainer@Veronicas-MacBook-Air app_python % 
```


