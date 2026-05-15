{{/*
Chart name
*/}}
{{- define "devops-python.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Full name
*/}}
{{- define "devops-python.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "devops-python.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-python.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "devops-python.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{ include "devops-python.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Secret resource name (Helm-managed or external)
*/}}
{{- define "devops-python.secretName" -}}
{{- if .Values.secrets.existingSecretName -}}
{{- .Values.secrets.existingSecretName -}}
{{- else -}}
{{- printf "%s-app-credentials" (include "devops-python.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Service account name
*/}}
{{- define "devops-python.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "devops-python.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/*
Non-secret container env (DRY) — Lab 11 bonus
*/}}
{{- define "devops-python.envVars" -}}
- name: HOST
  value: {{ .Values.env.HOST | quote }}
- name: PORT
  value: {{ .Values.env.PORT | quote }}
- name: LOG_FORMAT
  value: {{ .Values.env.LOG_FORMAT | quote }}
- name: VISITS_DATA_PATH
  value: {{ .Values.env.VISITS_DATA_PATH | quote }}
{{- end -}}

{{/*
Stable checksum input for env ConfigMap (Lab 12 bonus — pod restart on change)
*/}}
{{- define "devops-python.configEnvChecksum" -}}
{{- printf "%s|%s|%v" .Values.config.environment .Values.config.logLevel .Values.config.featureDebug -}}
{{- end -}}

{{- define "devops-python.analysisTemplateName" -}}
{{- printf "%s-health" (include "devops-python.fullname" .) -}}
{{- end -}}

{{/*
Lab 16 — init containers (download + wait-for-DNS). Included when .Values.initContainers.enabled
*/}}
{{- define "devops-python.initContainers" -}}
{{- if .Values.initContainers.waitForService.enabled }}
- name: wait-for-dns
  image: {{ .Values.initContainers.waitForService.image | quote }}
  command:
    - sh
    - -c
    - |
      set -e
      until nslookup "$WAIT_HOST" >/dev/null 2>&1; do
        echo "waiting for DNS: $WAIT_HOST"
        sleep 2
      done
      echo "DNS resolved for $WAIT_HOST"
  env:
    - name: WAIT_HOST
      value: {{ .Values.initContainers.waitForService.host | quote }}
  securityContext:
    allowPrivilegeEscalation: false
    runAsNonRoot: false
    runAsUser: 0
    capabilities:
      drop:
        - ALL
  resources:
    requests:
      cpu: 10m
      memory: 16Mi
    limits:
      memory: 32Mi
{{- end }}
{{- if .Values.initContainers.download.enabled }}
- name: init-download
  image: {{ .Values.initContainers.download.image | quote }}
  command:
    - sh
    - -c
    - wget -q -O /work-dir/{{ .Values.initContainers.download.filename }} {{ .Values.initContainers.download.url | quote }}
  volumeMounts:
    - name: init-workdir
      mountPath: /work-dir
  securityContext:
    allowPrivilegeEscalation: false
    runAsNonRoot: false
    runAsUser: 0
    capabilities:
      drop:
        - ALL
  resources:
    requests:
      cpu: 10m
      memory: 32Mi
    limits:
      memory: 64Mi
{{- end }}
{{- end }}

