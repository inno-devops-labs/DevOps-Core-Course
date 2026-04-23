{{/*
Expand the name of the chart.
*/}}
{{- define "devops-info.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "devops-info.fullname" -}}
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
{{- define "devops-info.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "devops-info.labels" -}}
helm.sh/chart: {{ include "devops-info.chart" . }}
{{ include "devops-info.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "devops-info.selectorLabels" -}}
app: devops-info
app.kubernetes.io/name: {{ include "devops-info.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Generate pre-install hook job name
*/}}
{{- define "devops-info.preInstallHookName" -}}
{{- printf "%s-pre-install" (include "devops-info.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Generate post-install hook job name
*/}}
{{- define "devops-info.postInstallHookName" -}}
{{- printf "%s-post-install" (include "devops-info.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Service account name
*/}}
{{- define "devops-info.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default "devops-info-sa" .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Secret resource name
*/}}
{{- define "devops-info.secretName" -}}
{{- default (printf "%s-secret" (include "devops-info.fullname" .)) .Values.secret.name }}
{{- end }}

{{/*
ConfigMap resource names
*/}}
{{- define "devops-info.configFileMapName" -}}
{{- printf "%s-config" (include "devops-info.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "devops-info.configEnvMapName" -}}
{{- printf "%s-env" (include "devops-info.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
PVC resource name
*/}}
{{- define "devops-info.pvcName" -}}
{{- printf "%s-data" (include "devops-info.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Preview service name (blue-green rollouts)
*/}}
{{- define "devops-info.previewServiceName" -}}
{{- printf "%s-%s" (include "devops-info.fullname" .) .Values.service.preview.suffix | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Headless service name (stateful workloads)
*/}}
{{- define "devops-info.headlessServiceName" -}}
{{- printf "%s-headless" (include "devops-info.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
