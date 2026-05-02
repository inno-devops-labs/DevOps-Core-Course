# Lab 15 — StatefulSet & Persistent Storage

## StatefulSet Overview

Почему StatefulSet:
- стабильные имена pod: `lab15-devops-info-python-0/1/2`;
- стабильная DNS-идентичность через headless service;
- отдельный PVC на каждый pod через `volumeClaimTemplates`.

Deployment vs StatefulSet:
- Deployment: stateless, pod-ы взаимозаменяемые, имена со случайным суффиксом.
- StatefulSet: stateful, pod-ы упорядочены, имеют фиксированные ordinal-имена и собственные PVC.

## Реализация в Helm chart

Файлы:
- [statefulset.yaml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/devops-info-python/templates/statefulset.yaml)
- [service-headless.yaml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/devops-info-python/templates/service-headless.yaml)
- [deployment.yaml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/devops-info-python/templates/deployment.yaml) (render только при `statefulset.enabled=false`)
- [pvc.yaml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/devops-info-python/templates/pvc.yaml) (не используется в StatefulSet-режиме)
- [_helpers.tpl](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/devops-info-python/templates/_helpers.tpl) (валидации конфликтующих режимов)

Дополнительная защита:
- `statefulset.enabled=true` несовместим с `persistence.existingClaim` (fail-fast), потому что StatefulSet должен создавать per-pod PVC.

## Resource Verification (Task 4)

Проверка выполнена 2026-05-01 в namespace `lab15`.

Команда:

```bash
kubectl get po,sts,svc,pvc -n lab15
```

Фактический вывод:

```text
NAME                             READY   STATUS    RESTARTS   AGE
pod/lab15-devops-info-python-0   1/1     Running   0          118s
pod/lab15-devops-info-python-1   1/1     Running   0          4m35s
pod/lab15-devops-info-python-2   1/1     Running   0          11s

NAME                                        READY   AGE
statefulset.apps/lab15-devops-info-python   3/3     5m

NAME                                        TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/lab15-devops-info-python            ClusterIP   10.96.245.240   <none>        80/TCP    4m55s
service/lab15-devops-info-python-headless   ClusterIP   None            <none>        80/TCP    5m

NAME                                                           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-volume-lab15-devops-info-python-0   Bound    pvc-d161c7cc-5e12-4231-afbd-e238d9310495   100Mi      RWO            standard       <unset>                 5m
persistentvolumeclaim/data-volume-lab15-devops-info-python-1   Bound    pvc-e0b0dec5-1a8f-492d-84a9-5ee92dd2308e   100Mi      RWO            standard       <unset>                 4m35s
persistentvolumeclaim/data-volume-lab15-devops-info-python-2   Bound    pvc-ba38c011-1004-46f5-95f6-59eac9597695   100Mi      RWO            standard       <unset>                 4m15s
```

## Network Identity (Task 3)

Команда:

```bash
kubectl exec -n lab15 lab15-devops-info-python-0 -- sh -lc 'nslookup lab15-devops-info-python-1.lab15-devops-info-python-headless || getent hosts lab15-devops-info-python-1.lab15-devops-info-python-headless'
```

Фактический вывод:

```text
10.244.1.57     lab15-devops-info-python-1.lab15-devops-info-python-headless.lab15.svc.cluster.local
```

Подтверждение: pod-1 резолвится по стабильному DNS-имени через headless service.

## Per-Pod Storage Evidence (Task 3)

Чтобы получить разные счетчики, были сделаны разные количества вызовов `/` на pod-0 и pod-1.

Команды:

```bash
kubectl port-forward -n lab15 pod/lab15-devops-info-python-0 19081:3000
kubectl port-forward -n lab15 pod/lab15-devops-info-python-1 19082:3000
curl -s http://127.0.0.1:19081/
curl -s http://127.0.0.1:19081/
curl -s http://127.0.0.1:19082/
curl -s http://127.0.0.1:19081/visits
curl -s http://127.0.0.1:19082/visits
```

Фактические `/visits` ответы:

```json
{"count":2,"path":"/data/visits","timestamp":"2026-05-01T15:15:47.826256+00:00"}
```

```json
{"count":1,"path":"/data/visits","timestamp":"2026-05-01T15:15:47.840033+00:00"}
```

Подтверждение: данные изолированы между pod-ами (`2` vs `1`).

## Persistence Test (Task 3)

Команды:

```bash
kubectl exec -n lab15 lab15-devops-info-python-0 -- cat /data/visits
kubectl delete pod -n lab15 lab15-devops-info-python-0
kubectl rollout status statefulset/lab15-devops-info-python -n lab15 --timeout=180s
kubectl exec -n lab15 lab15-devops-info-python-0 -- cat /data/visits
```

Фактический результат:

```text
before: 2
after:  2
```

Подтверждение: значение в PVC сохранилось после удаления pod и его пересоздания.

## Bonus — Update Strategies

### 1) Partitioned RollingUpdate

Команда:

```bash
helm upgrade lab15 ./k8s/devops-info-python -n lab15 \
  --set service.type=ClusterIP \
  --set service.nodePort=null \
  --set statefulset.updateStrategy.type=RollingUpdate \
  --set statefulset.updateStrategy.rollingUpdate.partition=2 \
  --set config.logLevel=DEBUG
```

До апдейта (revision):

```text
NAME                         REV
lab15-devops-info-python-0   lab15-devops-info-python-5c647c59d7
lab15-devops-info-python-1   lab15-devops-info-python-5c647c59d7
lab15-devops-info-python-2   lab15-devops-info-python-5c647c59d7
```

После апдейта с `partition=2`:

```text
NAME                         REV
lab15-devops-info-python-0   lab15-devops-info-python-5c647c59d7
lab15-devops-info-python-1   lab15-devops-info-python-5c647c59d7
lab15-devops-info-python-2   lab15-devops-info-python-566f74897f
```

Статус StatefulSet:

```text
currentRevision: lab15-devops-info-python-5c647c59d7
updateRevision:  lab15-devops-info-python-566f74897f
partition: 2
```

Подтверждение: обновился только pod с ordinal `2`.

### 2) OnDelete Strategy

Команда:

```bash
helm upgrade lab15 ./k8s/devops-info-python -n lab15 \
  --set service.type=ClusterIP \
  --set service.nodePort=null \
  --set statefulset.updateStrategy.type=OnDelete \
  --set config.logLevel=WARNING
```

До ручного удаления pod:

```text
NAME                         REV
lab15-devops-info-python-0   lab15-devops-info-python-5c647c59d7
lab15-devops-info-python-1   lab15-devops-info-python-5c647c59d7
lab15-devops-info-python-2   lab15-devops-info-python-566f74897f
```

Статус StatefulSet:

```text
currentRevision: lab15-devops-info-python-5c647c59d7
updateRevision:  lab15-devops-info-python-5f98dc8c45
type: OnDelete
```

После `kubectl delete pod -n lab15 lab15-devops-info-python-2`:

```text
NAME                         REV
lab15-devops-info-python-0   lab15-devops-info-python-5c647c59d7
lab15-devops-info-python-1   lab15-devops-info-python-5c647c59d7
lab15-devops-info-python-2   lab15-devops-info-python-5f98dc8c45
```

Подтверждение: при `OnDelete` pod-ы не обновляются автоматически, пока не удалены вручную.
