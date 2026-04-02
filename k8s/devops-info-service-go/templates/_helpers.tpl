{{- define "devops-info-service-go.name" -}}
{{- include "common-lib.name" . -}}
{{- end -}}

{{- define "devops-info-service-go.fullname" -}}
{{- include "common-lib.fullname" . -}}
{{- end -}}

{{- define "devops-info-service-go.labels" -}}
{{- include "common-lib.labels" . -}}
{{- end -}}

{{- define "devops-info-service-go.selectorLabels" -}}
{{- include "common-lib.selectorLabels" . -}}
{{- end -}}
