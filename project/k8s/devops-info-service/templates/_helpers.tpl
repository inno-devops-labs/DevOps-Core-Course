{{/*
Expand the name of the chart.
*/}}
{{- define "devops-info-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
Truncated at 63 chars because Kubernetes name fields are limited to this.
*/}}
{{- define "devops-info-service.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used in the chart label.
*/}}
{{- define "devops-info-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "devops-info-service.labels" -}}
helm.sh/chart: {{ include "devops-info-service.chart" . }}
{{ include "devops-info-service.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "devops-info-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-info-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Service account name for pods (Vault K8s auth binds to this name).
*/}}
{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "devops-info-service.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Non-sensitive container environment variables (DRY; include in deployment).
*/}}
{{- define "devops-info-service.containerEnv" -}}
- name: HOST
  value: {{ .Values.application.host | quote }}
- name: PORT
  value: {{ .Values.application.port | toString | quote }}
- name: VISITS_FILE
  value: "/data/visits"
{{- end }}

{{/*
Lab 16 — Init containers (download + wait-for-service patterns).
Rendered list is empty when initContainers.enabled=false.
*/}}
{{- define "devops-info-service.initContainers" -}}
{{- if .Values.initContainers.enabled }}
{{- if .Values.initContainers.download.enabled }}
- name: init-download
  image: {{ .Values.initContainers.download.image }}
  command: ['sh', '-c', 'wget -O {{ .Values.initContainers.download.targetFile }} {{ .Values.initContainers.download.url }}']
  volumeMounts:
    - name: workdir
      mountPath: /work-dir
{{- end }}
{{- if .Values.initContainers.waitForService.enabled }}
- name: init-wait-for-service
  image: {{ .Values.initContainers.waitForService.image }}
  command:
    - sh
    - -c
    - |
      DEADLINE=$(($(date +%s) + {{ .Values.initContainers.waitForService.timeoutSeconds }}))
      until nc -z {{ .Values.initContainers.waitForService.service }} {{ .Values.initContainers.waitForService.port }} 2>/dev/null; do
        echo "waiting for {{ .Values.initContainers.waitForService.service }}:{{ .Values.initContainers.waitForService.port }}..."
        [ $(date +%s) -ge $DEADLINE ] && echo "timeout" && exit 1
        sleep 2
      done
      echo "service reachable"
{{- end }}
{{- end }}
{{- end }}

{{/*
Lab 16 — Volume entry for the init-download shared workdir.
*/}}
{{- define "devops-info-service.initContainerVolumes" -}}
{{- if and .Values.initContainers.enabled .Values.initContainers.download.enabled }}
- name: workdir
  emptyDir: {}
{{- end }}
{{- end }}

{{/*
Lab 16 — Main container mount for the shared workdir (so app can read what init-download fetched).
*/}}
{{- define "devops-info-service.initContainerVolumeMounts" -}}
{{- if and .Values.initContainers.enabled .Values.initContainers.download.enabled }}
- name: workdir
  mountPath: /work-dir
{{- end }}
{{- end }}
