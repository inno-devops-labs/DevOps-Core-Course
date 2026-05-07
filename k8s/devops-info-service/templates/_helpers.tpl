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
Preview service name for blue-green strategy.
*/}}
{{- define "devops-info-service.previewServiceName" -}}
{{- printf "%s-preview" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Headless Service name for StatefulSet stable network identity (DNS per pod).
*/}}
{{- define "devops-info-service.headlessName" -}}
{{- printf "%s-headless" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" }}
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
Common environment variables (DRY principle)
*/}}
{{- define "devops-info-service.envVars" -}}
- name: HOST
  value: {{ .Values.service.host | default "0.0.0.0" | quote }}
- name: PORT
  value: {{ .Values.service.targetPort | toString | quote }}
- name: DEBUG
  value: {{ .Values.debug | default "false" | quote }}
{{- end }}
