# Lab 15 - StatefulSets and Persistent Storage

This document describes the base StatefulSet implementation for Lab 15.
All command outputs below are mock outputs created for reporting purposes.

---

## 1) StatefulSet Overview

- StatefulSet is used for workloads that need stable identities and per-pod storage.
- Pod names are stable and ordered (pod-0, pod-1, pod-2, ...).
- Each pod gets its own PVC via volumeClaimTemplates.
- A headless Service provides stable DNS records for each pod.

---

## 2) Resource Verification

```bash
azizvundirov@MacBook-Pro-Aziz ~/Documents/IU_STUDY/DevOps-Core-Course (lab15)$ kubectl get po,sts,svc,pvc
NAME                         READY   STATUS    RESTARTS   AGE
pod/lab15-myapp-0            1/1     Running   0          4m
pod/lab15-myapp-1            1/1     Running   0          4m
pod/lab15-myapp-2            1/1     Running   0          4m
pod/lab15-myapp-3            1/1     Running   0          4m
pod/lab15-myapp-4            1/1     Running   0          4m

NAME                         READY   AGE
statefulset.apps/lab15-myapp  5/5     4m

NAME                             TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/lab15-myapp              NodePort    10.96.12.34    <none>        80:30080/TCP   4m
service/lab15-myapp-headless     ClusterIP   None           <none>        80/TCP         4m

NAME                                               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-volume-lab15-myapp-0    Bound    pvc-0a1b2c3d-1111-2222-3333-444455556666   100Mi      RWO            standard       4m
persistentvolumeclaim/data-volume-lab15-myapp-1    Bound    pvc-0a1b2c3d-7777-8888-9999-aaaa55556666   100Mi      RWO            standard       4m
persistentvolumeclaim/data-volume-lab15-myapp-2    Bound    pvc-0a1b2c3d-bbbb-cccc-dddd-eeee55556666   100Mi      RWO            standard       4m
persistentvolumeclaim/data-volume-lab15-myapp-3    Bound    pvc-0a1b2c3d-ffff-0000-1111-222255556666   100Mi      RWO            standard       4m
persistentvolumeclaim/data-volume-lab15-myapp-4    Bound    pvc-0a1b2c3d-3333-4444-5555-666655556666   100Mi      RWO            standard       4m
```

---

## 3) Network Identity (Headless Service)

DNS pattern:
`<pod-name>.<headless-service>.<namespace>.svc.cluster.local`

```bash
azizvundirov@MacBook-Pro-Aziz ~/Documents/IU_STUDY/DevOps-Core-Course (lab15)$ nslookup lab15-myapp-1.lab15-myapp-headless.default.svc.cluster.local
Name:    lab15-myapp-1.lab15-myapp-headless.default.svc.cluster.local
Address: 10.244.1.9
```

---

## 4) Per-Pod Storage Evidence

Each pod keeps its own counter:

```bash
azizvundirov@MacBook-Pro-Aziz ~/Documents/IU_STUDY/DevOps-Core-Course (lab15)$ curl localhost:8080/visits
{"visits": 4}

azizvundirov@MacBook-Pro-Aziz ~/Documents/IU_STUDY/DevOps-Core-Course (lab15)$ curl localhost:8081/visits
{"visits": 1}

azizvundirov@MacBook-Pro-Aziz ~/Documents/IU_STUDY/DevOps-Core-Course (lab15)$ curl localhost:8082/visits
{"visits": 7}
```

---

## 5) Persistence Test

Counter is preserved after pod restart:

```bash
azizvundirov@MacBook-Pro-Aziz ~/Documents/IU_STUDY/DevOps-Core-Course (lab15)$ kubectl exec lab15-myapp-0 -- cat /data/visits
4

azizvundirov@MacBook-Pro-Aziz ~/Documents/IU_STUDY/DevOps-Core-Course (lab15)$ kubectl delete pod lab15-myapp-0
pod "lab15-myapp-0" deleted

azizvundirov@MacBook-Pro-Aziz ~/Documents/IU_STUDY/DevOps-Core-Course (lab15)$ kubectl exec lab15-myapp-0 -- cat /data/visits
4
```
