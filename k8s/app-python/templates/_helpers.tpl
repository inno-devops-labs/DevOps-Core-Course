{{/*
Expand the name of the chart.
*/}}
{{- define "app-python.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "app-python.fullname" -}}
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
{{- define "app-python.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "app-python.labels" -}}
helm.sh/chart: {{ include "app-python.chart" . }}
{{ include "app-python.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "app-python.selectorLabels" -}}
app.kubernetes.io/name: {{ include "app-python.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "app-python.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "app-python.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Secret name
*/}}
{{- define "app-python.secretName" -}}
{{- printf "%s-secret" (include "app-python.fullname" .) -}}
{{- end }}

{{/*
Common env block
*/}}
{{- define "app-python.commonEnv" -}}
- name: HOST
  value: {{ .Values.env.host | quote }}
- name: PORT
  value: {{ .Values.env.port | quote }}
- name: DEBUG
  value: {{ .Values.env.debug | quote }}
- name: RELEASE_VERSION
  value: {{ .Values.env.releaseVersion | quote }}
{{- end }}

{{/*
File ConfigMap name
*/}}
{{- define "app-python.fileConfigMapName" -}}
{{- printf "%s-config" (include "app-python.fullname" .) -}}
{{- end }}

{{/*
Env ConfigMap name
*/}}
{{- define "app-python.envConfigMapName" -}}
{{- printf "%s-env" (include "app-python.fullname" .) -}}
{{- end }}

{{/*
PVC name
*/}}
{{- define "app-python.pvcName" -}}
{{- printf "%s-data" (include "app-python.fullname" .) -}}
{{- end }}