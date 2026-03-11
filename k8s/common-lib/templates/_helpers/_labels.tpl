{{/*
Common labels
Usage: {{ include "common-lib.labels.standard" (dict "ctx" $ "name" .Chart.Name "selectorLabels" (include "app.selectorLabels" .)) }}
*/}}
{{- define "common-lib.labels.standard" -}}
{{- $ctx := .ctx -}}
helm.sh/chart: {{ include "common-lib.names.chart" $ctx }}
{{ include "common-lib.labels.selector" . }}
{{- if $ctx.Chart.AppVersion }}
app.kubernetes.io/version: {{ $ctx.Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ $ctx.Release.Service }}
{{- end }}

{{/*
Selector labels
Usage: {{ include "common-lib.labels.selector" (dict "name" .Chart.Name "ctx" $) }}
*/}}
{{- define "common-lib.labels.selector" -}}
{{- $name := .name | default .ctx.Chart.Name -}}
app.kubernetes.io/name: {{ $name }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
{{- end }}
