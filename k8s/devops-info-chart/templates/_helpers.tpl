{{/*
Expand the name of the chart.
*/}}
{{- define "devops-info-chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
Truncate at 63 chars (DNS naming limit). If release name contains chart name it is used as a full name.
*/}}
{{- define "devops-info-chart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name+version for helm.sh/chart label.
*/}}
{{- define "devops-info-chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common application environment variables — DRY helper (Bonus Task).
Centralises env vars shared across multiple containers / templates.

Usage:
  env:
    {{- include "devops-info-chart.envVars" . | nindent 12 }}
*/}}
{{- define "devops-info-chart.envVars" -}}
- name: APP_ENV
  value: {{ .Values.appEnv | default "production" | quote }}
- name: LOG_LEVEL
  value: {{ .Values.logLevel | default "info" | quote }}
{{- end }}
