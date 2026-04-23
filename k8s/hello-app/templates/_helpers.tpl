{{- define "hello-app.name" -}}
{{- include "common.name" . -}}
{{- end -}}

{{- define "hello-app.fullname" -}}
{{- include "common.fullname" . -}}
{{- end -}}

{{- define "hello-app.labels" -}}
{{- include "common.labels" . -}}
{{- end -}}

{{- define "hello-app.selectorLabels" -}}
{{- include "common.selectorLabels" . -}}
{{- end -}}
