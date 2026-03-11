{{/*
Create the name of the service account to use
*/}}
{{- define "echo-app.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "common-lib.names.fullname" (dict "ctx" $ "name" .Chart.Name)) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
