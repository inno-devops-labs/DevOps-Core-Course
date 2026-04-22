# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet Overview

StatefulSets are used for workloads that need:
- stable pod identity;
- stable per-pod storage;
- ordered deployment, scaling, and termination.

Unlike a Deployment, a StatefulSet gives each pod a predictable ordinal name such as `app-0`, `app-1`, and `app-2`. Each pod also gets its own PersistentVolumeClaim created from `volumeClaimTemplates`, so storage is isolated per pod and survives pod recreation.

For this lab, a separate Helm release was used instead of replacing the Lab 14 rollout. This avoids conflicts between progressive-delivery resources and stateful workload resources.

A headless Service is also required for StatefulSets. With `clusterIP: None`, Kubernetes creates DNS records for each pod, which makes stable pod-to-pod addressing possible.

## 2. Resource Verification

Commands used:

```bash
kubectl create namespace stateful
helm upgrade --install stateful-release k8s/devops-info-service -n stateful -f k8s/devops-info-service/values-stateful.yaml
kubectl get po,sts,svc,pvc -n stateful
```

Successful deployment output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl create namespace stateful
>> 
namespace/stateful created
PS C:\Users\zagur\DevOps\DevOps-Core-Course> helm upgrade --install stateful-release k8s/devops-info-service -n stateful -f k8s/devops-info-service/values-stateful.yaml
>> 
Release "stateful-release" has been upgraded. Happy Helming!
NAME: stateful-release
LAST DEPLOYED: Wed Apr 22 19:03:02 2026
NAMESPACE: stateful
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
S C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get po,sts,svc,pvc -n stateful
NAME                                         READY   STATUS    RESTARTS   AGE
pod/stateful-release-devops-info-service-0   2/2     Running   0          20m
pod/stateful-release-devops-info-service-1   2/2     Running   0          22m
pod/stateful-release-devops-info-service-2   2/2     Running   0          22m

NAME                                                    READY   AGE
statefulset.apps/stateful-release-devops-info-service   3/3     30m

NAME                                                    TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/stateful-release-devops-info-service            NodePort    10.108.159.203   <none>        80:30082/TCP   32m
service/stateful-release-devops-info-service-headless   ClusterIP   None             <none>        80/TCP         32m

NAME                                                                       STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-volume-stateful-release-devops-info-service-0   Bound    pvc-b5679153-a456-4e07-a8c8-aed6bb9b3d59   100Mi      RWO            standard       <unset>                 30m
persistentvolumeclaim/data-volume-stateful-release-devops-info-service-1   Bound    pvc-a9ab46e1-05c5-4d2c-a552-978de38dbc7e   100Mi      RWO            standard       <unset>                 22m
persistentvolumeclaim/data-volume-stateful-release-devops-info-service-2   Bound    pvc-7f6649ee-3a3b-4ad5-87e8-b922ff2e5b55   100Mi      RWO            standard       <unset>                 22m
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

Verification summary:
- the StatefulSet created three ordered pods: `-0`, `-1`, and `-2`;
- the headless Service `stateful-release-devops-info-service-headless` was created correctly with `clusterIP: None`;
- the main Service remained available for external access;
- three PVCs with ordinal suffixes were created for the StatefulSet pods.

## 3. Network Identity

The headless Service gives each pod a stable DNS name.

DNS naming pattern:

```text
<statefulset-pod-name>.<headless-service-name>.<namespace>.svc.cluster.local
```

In this lab, the pod names were:
- `stateful-release-devops-info-service-0`
- `stateful-release-devops-info-service-1`
- `stateful-release-devops-info-service-2`

Сommands used:

```bash
kubectl exec -n stateful stateful-release-devops-info-service-0 -- python -c "import socket; print(socket.gethostbyname('stateful-release-devops-info-service-1.stateful-release-devops-info-service-headless.stateful.svc.cluster.local'))"
kubectl exec -n stateful stateful-release-devops-info-service-0 -- python -c "import socket; print(socket.gethostbyname('stateful-release-devops-info-service-2.stateful-release-devops-info-service-headless.stateful.svc.cluster.local'))"
```

Output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl exec -n stateful stateful-release-devops-info-service-0 -- python -c "import socket; print(socket.gethostbyname('stateful-release-devops-info-service-1.stateful-release-devops-info-service-headless.stateful.svc.cluster.local'))"
>> 
Defaulted container "devops-info-service" out of: devops-info-service, vault-agent, vault-agent-init (init)
10.244.0.152
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl exec -n stateful stateful-release-devops-info-service-0 -- python -c "import socket; print(socket.gethostbyname('stateful-release-devops-info-service-2.stateful-release-devops-info-service-headless.stateful.svc.cluster.local'))"
Defaulted container "devops-info-service" out of: devops-info-service, vault-agent, vault-agent-init (init)
10.244.0.153
```

This confirms that:
- each pod has its own stable DNS record;
- pod `-0` can resolve pod `-1` and pod `-2` directly;
- StatefulSet networking is different from Deployment networking, where pod names are not stable.

## 4. Per-Pod Storage Evidence

Each pod writes visits to `/data/visits`, but because the StatefulSet uses `volumeClaimTemplates`, each pod has a different PVC and therefore its own counter file.

Port-forward commands:

```bash
kubectl port-forward -n stateful pod/stateful-release-devops-info-service-0 8080:5000
kubectl port-forward -n stateful pod/stateful-release-devops-info-service-1 8081:5000
kubectl port-forward -n stateful pod/stateful-release-devops-info-service-2 8082:5000
```

Requests used:

```bash
curl http://localhost:8080/visits
curl http://localhost:8081/
curl http://localhost:8081/visits
curl http://localhost:8082/
curl http://localhost:8082/visits
curl http://localhost:8080/visits
```


```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> curl http://localhost:8080/visits
{"visits":1,"visits_file":"/data/visits"}
PS C:\Users\zagur\DevOps\DevOps-Core-Course> curl http://localhost:8081/      
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"application":{"environment":"stateful","log_level":"INFO"},"config":{"config_file":"/config/config.json","loaded":true,"content":{"applicationName":"devops-info-service","environment":"stateful","settings":{"featureFlags":{"debugEndpoints":"true","showVisitsInRoot":"true"},"logLevel":"INFO"}}},"persistence":{"visits_file":"/data/visits","visits_count":1},"system":{"hostname":"stateful-release-devops-info-service-1","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":81,"uptime_human":"0 hours, 1 minutes","current_time":"2026-04-22T16:12:07.263Z","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Current visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}
PS C:\Users\zagur\DevOps\DevOps-Core-Course> curl http://localhost:8081/visits
{"visits":1,"visits_file":"/data/visits"}
PS C:\Users\zagur\DevOps\DevOps-Core-Course> curl http://localhost:8082/      
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"application":{"environment":"stateful","log_level":"INFO"},"config":{"config_file":"/config/config.json","loaded":true,"content":{"applicationName":"devops-info-service","environment":"stateful","settings":{"featureFlags":{"debugEndpoints":"true","showVisitsInRoot":"true"},"logLevel":"INFO"}}},"persistence":{"visits_file":"/data/visits","visits_count":1},"system":{"hostname":"stateful-release-devops-info-service-2","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":79,"uptime_human":"0 hours, 1 minutes","current_time":"2026-04-22T16:12:22.866Z","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Current visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}
PS C:\Users\zagur\DevOps\DevOps-Core-Course> curl http://localhost:8082/visits
{"visits":1,"visits_file":"/data/visits"}
PS C:\Users\zagur\DevOps\DevOps-Core-Course> curl http://localhost:8080/visits
{"visits":1,"visits_file":"/data/visits"}
PS C:\Users\zagur\DevOps\DevOps-Core-Course> curl http://localhost:8080/
>> curl http://localhost:8080/
>> curl http://localhost:8081/
>> curl http://localhost:8082/
>> curl http://localhost:8082/
>> curl http://localhost:8082/
>> 
>> curl http://localhost:8080/visits
>> curl http://localhost:8081/visits
>> curl http://localhost:8082/visits
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"application":{"environment":"stateful","log_level":"INFO"},"config":{"config_file":"/config/config.json","loaded":true,"content":{"applicationName":"devops-info-service","environment":"stateful","settings":{"featureFlags":{"debugEndpoints":"true","showVisitsInRoot":"true"},"logLevel":"INFO"}}},"persistence":{"visits_file":"/data/visits","visits_count":2},"system":{"hostname":"stateful-release-devops-info-service-0","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":1843,"uptime_human":"0 hours, 30 minutes","current_time":"2026-04-22T16:43:48.423Z","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Current visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"application":{"environment":"stateful","log_level":"INFO"},"config":{"config_file":"/config/config.json","loaded":true,"content":{"applicationName":"devops-info-service","environment":"stateful","settings":{"featureFlags":{"debugEndpoints":"true","showVisitsInRoot":"true"},"logLevel":"INFO"}}},"persistence":{"visits_file":"/data/visits","visits_count":3},"system":{"hostname":"stateful-release-devops-info-service-0","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":1843,"uptime_human":"0 hours, 30 minutes","current_time":"2026-04-22T16:43:48.472Z","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Current visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"application":{"environment":"stateful","log_level":"INFO"},"config":{"config_file":"/config/config.json","loaded":true,"content":{"applicationName":"devops-info-service","environment":"stateful","settings":{"featureFlags":{"debugEndpoints":"true","showVisitsInRoot":"true"},"logLevel":"INFO"}}},"persistence":{"visits_file":"/data/visits","visits_count":2},"system":{"hostname":"stateful-release-devops-info-service-1","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":1983,"uptime_human":"0 hours, 33 minutes","current_time":"2026-04-22T16:43:48.539Z","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Current visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"application":{"environment":"stateful","log_level":"INFO"},"config":{"config_file":"/config/config.json","loaded":true,"content":{"applicationName":"devops-info-service","environment":"stateful","settings":{"featureFlags":{"debugEndpoints":"true","showVisitsInRoot":"true"},"logLevel":"INFO"}}},"persistence":{"visits_file":"/data/visits","visits_count":2},"system":{"hostname":"stateful-release-devops-info-service-2","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":1965,"uptime_human":"0 hours, 32 minutes","current_time":"2026-04-22T16:43:48.601Z","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Current visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"application":{"environment":"stateful","log_level":"INFO"},"config":{"config_file":"/config/config.json","loaded":true,"content":{"applicationName":"devops-info-service","environment":"stateful","settings":{"featureFlags":{"debugEndpoints":"true","showVisitsInRoot":"true"},"logLevel":"INFO"}}},"persistence":{"visits_file":"/data/visits","visits_count":3},"system":{"hostname":"stateful-release-devops-info-service-2","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":1965,"uptime_human":"0 hours, 32 minutes","current_time":"2026-04-22T16:43:48.646Z","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Current visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"application":{"environment":"stateful","log_level":"INFO"},"config":{"config_file":"/config/config.json","loaded":true,"content":{"applicationName":"devops-info-service","environment":"stateful","settings":{"featureFlags":{"debugEndpoints":"true","showVisitsInRoot":"true"},"logLevel":"INFO"}}},"persistence":{"visits_file":"/data/visits","visits_count":4},"system":{"hostname":"stateful-release-devops-info-service-2","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":1965,"uptime_human":"0 hours, 32 minutes","current_time":"2026-04-22T16:43:48.697Z","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Current visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}{"visits":3,"visits_file":"/data/visits"}{"visits":2,"visits_file":"/data/visits"}{"visits":4,"visits_file":"/data/visits"}
PS C:\Users\zagur\DevOps\DevOps-Core-Course> curl http://localhost:8080/visits                                                    
{"visits":3,"visits_file":"/data/visits"}
PS C:\Users\zagur\DevOps\DevOps-Core-Course> curl http://localhost:8081/visits
{"visits":2,"visits_file":"/data/visits"}
PS C:\Users\zagur\DevOps\DevOps-Core-Course> curl http://localhost:8082/visits
{"visits":4,"visits_file":"/data/visits"}
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

Current result interpretation:
- all three pods were reachable independently;
- the hostnames in the `/` response matched the pod ordinals (`-1`, `-2`), which confirms that requests really reached different pods;

## 5. Persistence Test

Record the current value from pod `0`:

```bash
kubectl exec -n stateful stateful-release-devops-info-service-0 -- cat /data/visits
```

Delete only the pod:

```bash
kubectl delete pod -n stateful stateful-release-devops-info-service-0
kubectl get pods -n stateful -w
```

After the pod returns, check again:

```bash
kubectl exec -n stateful stateful-release-devops-info-service-0 -- cat /data/visits
```

Observed output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl exec -n stateful stateful-release-devops-info-service-0 -- cat /data/visits
Defaulted container "devops-info-service" out of: devops-info-service, vault-agent, vault-agent-init (init)
1
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl delete pod -n stateful stateful-release-devops-info-service-0
pod "stateful-release-devops-info-service-0" deleted from stateful namespace
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods -n stateful -w
NAME                                     READY   STATUS    RESTARTS   AGE
stateful-release-devops-info-service-0   1/2     Running   0          6s
stateful-release-devops-info-service-1   2/2     Running   0          2m29s
stateful-release-devops-info-service-2   2/2     Running   0          2m12s
stateful-release-devops-info-service-0   1/2     Running   0          15s
stateful-release-devops-info-service-0   2/2     Running   0          15s
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl exec -n stateful stateful-release-devops-info-service-0 -- cat /data/visits
Defaulted container "devops-info-service" out of: devops-info-service, vault-agent, vault-agent-init (init)
1
```

This confirms that deleting the pod did not delete its data. The StatefulSet recreated pod `0` with the same identity and reattached it to the same persistent volume, so the counter value remained unchanged.

## 6. Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod identity | Ephemeral, random suffix | Stable ordinal name (`-0`, `-1`, `-2`) |
| Storage | Usually shared or external | Per-pod PVC via `volumeClaimTemplates` |
| Network identity | Not stable | Stable DNS through headless Service |
| Scaling order | No identity guarantees | Ordered create/terminate |
| Typical use | Stateless apps | Stateful apps |

Deployment is suitable for stateless services where pod identity and local storage do not matter. StatefulSet is suitable for stateful services where each replica needs a stable name, stable volume, and predictable startup order.

Examples of StatefulSet workloads:
- PostgreSQL
- MongoDB
- Kafka
- RabbitMQ
- Elasticsearch

## 7. Conclusion

This lab demonstrated how StatefulSets solve problems that Deployments and Rollouts do not address. The application received:
- stable pod names;
- a headless Service for direct pod addressing;
- isolated storage per replica;
- preserved data after pod deletion.

The implementation achieved the main StatefulSet goals. The only remaining improvement would be to remove the leftover standalone PVC from the chart and to strengthen the storage-isolation evidence by generating intentionally different visit counts per pod.