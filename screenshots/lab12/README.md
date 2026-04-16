# Lab12 Screenshot Checklist

Place runtime screenshots for lab12 in this folder:

1. `01-get-configmap-pvc.png`  
   `kubectl get configmap,pvc`

2. `02-config-file-in-pod.png`  
   `kubectl exec <pod> -- cat /config/config.json`

3. `03-env-vars-in-pod.png`  
   `kubectl exec <pod> -- printenv | grep -E "APP_ENV|LOG_LEVEL|VISITS_FILE"`

4. `04-visits-before-delete.png`  
   `kubectl exec <pod> -- cat /data/visits` (before pod deletion)

5. `05-delete-pod.png`  
   `kubectl delete pod <pod>`

6. `06-visits-after-recreate.png`  
   `kubectl exec <new-pod> -- cat /data/visits` (after pod recreated)

To capture all outputs as text in one file, run:

```powershell
powershell -ExecutionPolicy Bypass -File k8s/scripts/capture-lab12-runtime-evidence.ps1
```

Generated output:
- `k8s/lab12-evidence/runtime-k8s.txt`

If the host cannot start Docker/Minikube, the script still writes:
- `Status: COMPLETED WITH ERRORS`
- concrete error details to help debug environment issues
