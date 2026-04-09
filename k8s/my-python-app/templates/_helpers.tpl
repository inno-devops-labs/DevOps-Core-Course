{{/*
Expand the name of the chart.
*/}}
{{- define "my-python-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "my-python-app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Chart version and app version
*/}}
{{- define "my-python-app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "my-python-app.labels" -}}
helm.sh/chart: {{ include "my-python-app.chart" . }}
{{ include "my-python-app.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "my-python-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "my-python-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Named template for common environment variables (bonus)
*/}}
{{- define "my-python-app.envVars" -}}
- name: APP_ENV
  value: {{ .Values.environment | default "production" }}
- name: LOG_LEVEL
  value: {{ .Values.logLevel | default "info" }}
{{- end }}