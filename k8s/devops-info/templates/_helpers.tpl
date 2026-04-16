{{/*
Build the container image reference.
*/}}
{{- define "devops-info.image" -}}
{{- printf "%s:%s" .Values.image.repository (default .Chart.AppVersion .Values.image.tag) -}}
{{- end }}

{{/*
Build the in-cluster health endpoint URL used by the smoke-test hook.
*/}}
{{- define "devops-info.healthURL" -}}
{{- printf "http://%s:%v%s" (include "common.fullname" .) .Values.service.port .Values.hookJobs.postInstall.path -}}
{{- end }}

{{/*
Render the common application environment variables from values.yaml.
*/}}
{{- define "devops-info.envVars" -}}
{{- toYaml .Values.env -}}
{{- end }}

{{/*
Resolve the application Secret name.
*/}}
{{- define "devops-info.secretName" -}}
{{- default (printf "%s-secret" (include "common.fullname" .)) .Values.secret.name -}}
{{- end }}
