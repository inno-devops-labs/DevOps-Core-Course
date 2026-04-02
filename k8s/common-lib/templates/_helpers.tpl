{{/*
Expand the name of the chart.
*/}}
{{- define "common.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create chart identifier string for helm.sh/chart label.
*/}}
{{- define "common.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "common.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Common labels for all resources.
*/}}
{{- define "common.labels" -}}
helm.sh/chart: {{ include "common.chart" . }}
{{ include "common.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels used for pod matching.
*/}}
{{- define "common.selectorLabels" -}}
app.kubernetes.io/name: {{ include "common.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Standard pod security context for non-root execution.
*/}}
{{- define "common.podSecurityContext" -}}
runAsNonRoot: {{ .Values.securityContext.runAsNonRoot | default true }}
runAsUser: {{ .Values.securityContext.runAsUser | default 999 }}
runAsGroup: {{ .Values.securityContext.runAsGroup | default 999 }}
fsGroup: {{ .Values.securityContext.fsGroup | default 999 }}
{{- end }}

{{/*
Standard container security context.
*/}}
{{- define "common.containerSecurityContext" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: false
capabilities:
  drop:
    - ALL
{{- end }}
