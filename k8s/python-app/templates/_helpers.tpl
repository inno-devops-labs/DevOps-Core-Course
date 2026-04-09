{{/*
Chart-specific helpers for Lab 11 additions.
*/}}
{{- define "python-app.secretName" -}}
{{- if .Values.secret.name -}}
{{- .Values.secret.name -}}
{{- else -}}
{{- printf "%s-secret" (include "common.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "python-app.serviceAccountName" -}}
{{- if .Values.serviceAccount.name -}}
{{- .Values.serviceAccount.name -}}
{{- else if .Values.serviceAccount.create -}}
{{- printf "%s-sa" (include "common.fullname" .) -}}
{{- else -}}
default
{{- end -}}
{{- end -}}

{{/*
Named template used by the deployment to keep common environment entries DRY.
*/}}
{{- define "python-app.envVars" -}}
{{- range $name, $value := .Values.env }}
- name: {{ $name }}
  value: {{ $value | quote }}
{{- end }}
{{- end -}}

{{/*
Vault Agent template rendered into /vault/secrets/app.env.
*/}}
{{- define "python-app.vaultTemplate" -}}
{{`{{- with secret "`}}{{ .Values.vault.secretPath }}{{`" -}}`}}
APP_USERNAME={{`{{ .Data.data.APP_USERNAME }}`}}
APP_PASSWORD={{`{{ .Data.data.APP_PASSWORD }}`}}
APP_API_KEY={{`{{ .Data.data.APP_API_KEY }}`}}
{{`{{- end -}}`}}
{{- end -}}
