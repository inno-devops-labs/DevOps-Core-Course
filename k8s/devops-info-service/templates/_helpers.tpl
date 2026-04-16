{{/*
Expand the name of the chart.
*/}}
{{- define "devops-info-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
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
Create chart name and version as used by the chart label.
*/}}
{{- define "devops-info-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "devops-info-service.labels" -}}
{{ include "common-lib.labels" . }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "devops-info-service.selectorLabels" -}}
{{ include "common-lib.selectorLabels" . }}
{{- end }}

{{/*
Service account name.
*/}}
{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.name }}
{{- .Values.serviceAccount.name }}
{{- else }}
{{- include "devops-info-service.fullname" . }}
{{- end }}
{{- end }}

{{/*
Secret name.
*/}}
{{- define "devops-info-service.secretName" -}}
{{- if .Values.secret.name }}
{{- .Values.secret.name }}
{{- else }}
{{- printf "%s-secret" (include "devops-info-service.fullname" .) }}
{{- end }}
{{- end }}

{{/*
ConfigMap name for file-based config.
*/}}
{{- define "devops-info-service.configMapName" -}}
{{- printf "%s-config" (include "devops-info-service.fullname" .) }}
{{- end }}

{{/*
ConfigMap name for env vars.
*/}}
{{- define "devops-info-service.envConfigMapName" -}}
{{- printf "%s-env" (include "devops-info-service.fullname" .) }}
{{- end }}

{{/*
PVC name for persistent data.
*/}}
{{- define "devops-info-service.pvcName" -}}
{{- printf "%s-data" (include "devops-info-service.fullname" .) }}
{{- end }}

{{/*
Named template for common environment variables.
*/}}
{{- define "devops-info-service.commonEnv" -}}
- name: APP_ENV
  value: {{ .Values.env.appEnv | quote }}
- name: LOG_LEVEL
  value: {{ .Values.env.logLevel | quote }}
- name: VISITS_FILE
  value: {{ printf "%s/visits" .Values.persistence.mountPath | quote }}
- name: CONFIG_FILE
  value: {{ printf "%s/%s" .Values.config.mountPath .Values.config.fileName | quote }}
{{- end }}
