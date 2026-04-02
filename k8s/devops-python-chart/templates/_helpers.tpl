{{/*
Expand the name of the chart.
*/}}
{{- define "devops-python-chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this.
If release name contains the chart name it will be used as a full name.
*/}}
{{- define "devops-python-chart.fullname" -}}
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
Create chart name and version as used by the chart label.
*/}}
{{- define "devops-python-chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels — includes version and managed-by, can change on upgrade.
*/}}
{{- define "devops-python-chart.labels" -}}
helm.sh/chart: {{ include "devops-python-chart.chart" . }}
{{ include "devops-python-chart.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels — MUST be stable and immutable after first install.
Used in Deployment spec.selector.matchLabels (immutable field in Kubernetes).
Only app name and instance — never chart version or managed-by.
*/}}
{{- define "devops-python-chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-python-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
