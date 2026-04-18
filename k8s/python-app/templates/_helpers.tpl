{{/*
Expand the base application name.
*/}}
{{- define "python-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a chart identifier for labels.
*/}}
{{- define "python-app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a release-qualified resource name.
*/}}
{{- define "python-app.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Labels used for selectors.
*/}}
{{- define "python-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "python-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Standard labels applied to all resources.
*/}}
{{- define "python-app.labels" -}}
helm.sh/chart: {{ include "python-app.chart" . }}
{{ include "python-app.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Resolve the service account name used by the workload.
*/}}
{{- define "python-app.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "python-app.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/*
Resolve the managed secret name.
*/}}
{{- define "python-app.secretName" -}}
{{- default (printf "%s-secret" (include "python-app.fullname" .)) .Values.secrets.name -}}
{{- end -}}

{{/*
Resolve the preview service name used by blue-green rollouts.
*/}}
{{- define "python-app.previewServiceName" -}}
{{- printf "%s-%s" (include "python-app.fullname" .) .Values.rollout.blueGreen.previewServiceSuffix | trunc 63 | trimSuffix "-" -}}
{{- end -}}
