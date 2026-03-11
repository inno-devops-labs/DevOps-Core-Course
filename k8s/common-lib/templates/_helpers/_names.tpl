{{/*
Create a default fully qualified app name.
Usage: {{ include "common-lib.names.fullname" (dict "ctx" $ "name" .Values.name) }}
*/}}
{{- define "common-lib.names.fullname" -}}
{{- $ctx := .ctx -}}
{{- $name := .name | default $ctx.Chart.Name -}}
{{- if $ctx.Values.fullnameOverride }}
{{- $ctx.Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $releaseName := $ctx.Release.Name -}}
{{- if contains $releaseName $name }}
{{- $releaseName | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" $releaseName $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version
*/}}
{{- define "common-lib.names.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}
