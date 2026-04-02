{{/*
Build the container image reference.
*/}}
{{- define "devops-info-app2.image" -}}
{{- printf "%s:%s" .Values.image.repository (default .Chart.AppVersion .Values.image.tag) -}}
{{- end }}
