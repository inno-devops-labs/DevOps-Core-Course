{{/*
Render an HTTP probe block from a values object.
*/}}
{{- define "common-lib.httpProbe" -}}
httpGet:
  path: {{ .httpGet.path | quote }}
  port: {{ .httpGet.port | quote }}
{{- with .httpGet.scheme }}
  scheme: {{ . }}
{{- end }}
{{- with .initialDelaySeconds }}
initialDelaySeconds: {{ . }}
{{- end }}
{{- with .periodSeconds }}
periodSeconds: {{ . }}
{{- end }}
{{- with .timeoutSeconds }}
timeoutSeconds: {{ . }}
{{- end }}
{{- with .successThreshold }}
successThreshold: {{ . }}
{{- end }}
{{- with .failureThreshold }}
failureThreshold: {{ . }}
{{- end }}
{{- end -}}
