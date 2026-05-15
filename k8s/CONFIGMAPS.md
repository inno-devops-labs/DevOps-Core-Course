Lab 12 — ConfigMaps \& Persistent Volumes



Task 1 — Application Persistence Upgrade

Visit Counter Implementation

The application now tracks visit count with:



Counter stored in file: /data/visits



New endpoint: GET /visits returns current count



Root endpoint GET / increments counter and shows count in response



Thread-safe implementation with file locking



Local Testing with Docker Compose

cd app\_python

docker compose up --build



In another terminal:

curl http://localhost:5000/ -UseBasicParsing

curl http://localhost:5000/visits -UseBasicParsing

curl http://localhost:5000/ -UseBasicParsing

docker compose restart

curl http://localhost:5000/visits -UseBasicParsing



Evidence

curl http://localhost:5000/visits -UseBasicParsing

{"count":4,"file\_path":"/data/visits","message":"Total visits: 4","persistent":true}



Task 2 — ConfigMap Implementation



ConfigMap Templates

File-based ConfigMap (templates/configmap.yaml):



apiVersion: v1

kind: ConfigMap

metadata:

name: {{ include "devops-info-service.fullname" . }}-config

data:

config.json: |

{{ .Files.Get "files/config.json" | indent 4 }}



Environment ConfigMap:



apiVersion: v1

kind: ConfigMap

metadata:

name: {{ include "devops-info-service.fullname" . }}-env

data:

APP\_ENV: {{ .Values.configmap.env.APP\_ENV | quote }}

LOG\_LEVEL: {{ .Values.configmap.env.LOG\_LEVEL | quote }}



ConfigMap Verification

kubectl get configmap

NAME DATA AGE

devops-info-service-config 1 5m

devops-info-service-env 2 5m



kubectl exec -it deployment/devops-info-service -- cat /config/config.json

{

"app\_name": "devops-info-service",

"environment": "development",

"features": {

"visits\_counter": true,

"metrics": false

}

}



kubectl exec -it deployment/devops-info-service -- env | findstr "APP\_ENV"

APP\_ENV=development



kubectl exec -it deployment/devops-info-service -- env | findstr "LOG\_LEVEL"

LOG\_LEVEL=DEBUG



Task 3 — Persistent Volumes



PVC Template

apiVersion: v1

kind: PersistentVolumeClaim

metadata:

name: {{ include "devops-info-service.fullname" . }}-data

spec:

accessModes:



ReadWriteOnce

resources:

requests:

storage: {{ .Values.persistence.size }}



Values Configuration

persistence:

enabled: true

accessMode: ReadWriteOnce

size: 100Mi

storageClass: ""



Deployment Volume Mount

volumeMounts:



name: data

mountPath: /data

volumes:



name: data

persistentVolumeClaim:

claimName: {{ include "devops-info-service.fullname" . }}-data



PVC Verification

kubectl get pvc

NAME STATUS VOLUME CAPACITY ACCESS MODES STORAGECLASS AGE

devops-info-service-data Bound pvc-xxx 100Mi RWO standard 10m



Persistence Test

Before pod deletion (count = 4):



curl http://localhost:8080/visits -UseBasicParsing

{"count":4,"file\_path":"/data/visits","message":"Total visits: 4","persistent":true}



Delete pod:



kubectl get pods

NAME READY STATUS RESTARTS AGE

devops-info-service-7646d97b44-zjj8j 1/1 Running 0 4m47s



kubectl delete pod devops-info-service-7646d97b44-zjj8j

pod "devops-info-service-7646d97b44-zjj8j" deleted



kubectl get pods -w

NAME READY STATUS RESTARTS AGE

devops-info-service-7646d97b44-v789t 1/1 Running 0 34s



After pod restart (count preserved = 4):



curl http://localhost:8080/visits -UseBasicParsing

{"count":4,"file\_path":"/data/visits","message":"Total visits: 4","persistent":true}



Task 4 — Health Check Verification



curl http://localhost:8080/health -UseBasicParsing

{

"config\_file": true,

"status": "healthy",

"timestamp": "2026-05-15T04:01:37.093496+00:00",

"uptime\_seconds": 69,

"visits\_file": true

}



ConfigMap vs Secret Comparison

Aspect	ConfigMap	Secret

Content	Non-sensitive config (JSON, flags, log level)	Passwords, tokens, TLS keys

API storage	Plaintext in etcd	Base64 in API (not encrypted)

Use case	Feature flags, config.json, env for non-secret settings	Credentials, TLS material

Conclusion

Lab 12 completed with all requirements:



Application upgraded with visit counter and /visits endpoint



ConfigMap mounted as file at /config/config.json



ConfigMap provides environment variables (APP\_ENV, LOG\_LEVEL)



PVC created and mounted at /data



Visit counter persists across pod deletion and restart



Health check confirms config\_file and visits\_file are present

