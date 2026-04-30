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
Resolve container image with optional digest.
*/}}
{{- define "devops-info-service.image" -}}
{{- if .Values.image.digest -}}
{{- printf "%s@%s" .Values.image.repository .Values.image.digest -}}
{{- else -}}
{{- printf "%s:%s" .Values.image.repository (.Values.image.tag | default .Chart.AppVersion) -}}
{{- end -}}
{{- end }}

{{/*
Standard env vars passed to the application container.
*/}}
{{- define "devops-info-service.envVars" -}}
- name: HOST
  value: {{ .Values.appConfig.host | quote }}
- name: PORT
  value: {{ .Values.appConfig.port | quote }}
- name: DEBUG
  value: {{ .Values.appConfig.debug | quote }}
- name: APP_ENV
  value: {{ .Values.appConfig.appEnv | quote }}
- name: LOG_LEVEL
  value: {{ .Values.appConfig.logLevel | quote }}
- name: VISITS_FILE
  value: {{ printf "%s/%s" .Values.persistence.mountPath .Values.persistence.visitsFileName | quote }}
{{- end }}

{{/*
ConfigMap names.
*/}}
{{- define "devops-info-service.configFileConfigMapName" -}}
{{ .Values.configMap.file.name | default (include "devops-info-service.fullname" .) }}-config
{{- end }}

{{- define "devops-info-service.configEnvMapName" -}}
{{ .Values.configMap.env.name | default (include "devops-info-service.fullname" .) }}-env
{{- end }}

{{/*
Service account name helper.
*/}}
{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{ .Values.serviceAccount.name | default (include "devops-info-service.fullname" .) }}
{{- else -}}
{{ .Values.serviceAccount.name | default "default" }}
{{- end -}}
{{- end }}

{{/*
Validation placeholder for optional persistence checks.
*/}}
{{- define "devops-info-service.persistenceValidation" -}}
{{- if and .Values.persistence.enabled (not .Values.persistence.mountPath) -}}
{{- fail "persistence.mountPath must be set when persistence is enabled" -}}
{{- end -}}
{{- end }}
