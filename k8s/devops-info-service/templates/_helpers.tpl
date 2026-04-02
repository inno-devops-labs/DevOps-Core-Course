{{/*
Chart-local wrappers around the shared library helpers.
*/}}
{{- define "devops-info-service.name" -}}
{{- include "common-lib.name" . -}}
{{- end -}}

{{- define "devops-info-service.fullname" -}}
{{- include "common-lib.fullname" . -}}
{{- end -}}

{{- define "devops-info-service.labels" -}}
{{- include "common-lib.labels" . -}}
{{- end -}}

{{- define "devops-info-service.selectorLabels" -}}
{{- include "common-lib.selectorLabels" . -}}
{{- end -}}

{{- define "devops-info-service.preInstallJobName" -}}
{{- printf "%s-pre-install" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "devops-info-service.postInstallJobName" -}}
{{- printf "%s-post-install" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
