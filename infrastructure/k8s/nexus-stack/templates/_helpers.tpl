{{/*
=============================================================================
Nexus Helm Chart - Template Helpers
=============================================================================
Enterprise-grade helper templates for DRY, maintainable Kubernetes manifests.
=============================================================================
*/}}

{{/*
Expand the name of the chart.
*/}}
{{- define "nexus.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this.
*/}}
{{- define "nexus.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "nexus.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
=============================================================================
LABELS
=============================================================================
*/}}

{{/*
Common labels for all resources
*/}}
{{- define "nexus.labels" -}}
helm.sh/chart: {{ include "nexus.chart" . }}
{{ include "nexus.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: nexus
{{- if .Values.global.commonLabels }}
{{ toYaml .Values.global.commonLabels }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "nexus.selectorLabels" -}}
app.kubernetes.io/name: {{ include "nexus.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Component labels - adds component-specific labels
Usage: {{ include "nexus.componentLabels" (dict "component" "orchestrator" "context" .) }}
*/}}
{{- define "nexus.componentLabels" -}}
{{ include "nexus.labels" .context }}
app.kubernetes.io/component: {{ .component }}
nexus.io/service-type: {{ .component }}
{{- end }}

{{/*
Component selector labels
Usage: {{ include "nexus.componentSelectorLabels" (dict "component" "orchestrator" "context" .) }}
*/}}
{{- define "nexus.componentSelectorLabels" -}}
{{ include "nexus.selectorLabels" .context }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{/*
Pod labels - includes common annotations for metrics
*/}}
{{- define "nexus.podLabels" -}}
{{ include "nexus.componentSelectorLabels" . }}
{{- if .context.Values.global.podLabels }}
{{ toYaml .context.Values.global.podLabels }}
{{- end }}
{{- end }}

{{/*
=============================================================================
IMAGE HELPERS
=============================================================================
*/}}

{{/*
Create the image name
Usage: {{ include "nexus.image" (dict "imageConfig" .Values.orchestrator.image "global" .Values.global "Chart" .Chart) }}
*/}}
{{- define "nexus.image" -}}
{{- $registry := .imageConfig.registry | default .global.imageRegistry | default "" -}}
{{- $repository := .imageConfig.repository -}}
{{- $tag := .imageConfig.tag | default .global.imageTag | default .Chart.AppVersion -}}
{{- if $registry -}}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- else -}}
{{- printf "%s:%s" $repository $tag -}}
{{- end -}}
{{- end }}

{{/*
Image pull policy
*/}}
{{- define "nexus.imagePullPolicy" -}}
{{- .imageConfig.pullPolicy | default .global.imagePullPolicy | default "IfNotPresent" -}}
{{- end }}

{{/*
Image pull secrets
*/}}
{{- define "nexus.imagePullSecrets" -}}
{{- $pullSecrets := list }}
{{- if .global.imagePullSecrets }}
{{- range .global.imagePullSecrets }}
{{- $pullSecrets = append $pullSecrets (dict "name" .) }}
{{- end }}
{{- end }}
{{- if .imageConfig.pullSecrets }}
{{- range .imageConfig.pullSecrets }}
{{- $pullSecrets = append $pullSecrets (dict "name" .) }}
{{- end }}
{{- end }}
{{- if $pullSecrets }}
imagePullSecrets:
{{ toYaml $pullSecrets }}
{{- end }}
{{- end }}

{{/*
=============================================================================
SERVICE ACCOUNT
=============================================================================
*/}}

{{/*
Create the name of the service account to use
*/}}
{{- define "nexus.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "nexus.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
=============================================================================
NETWORKING
=============================================================================
*/}}

{{/*
Generate service URL for inter-service communication
Usage: {{ include "nexus.serviceUrl" (dict "name" "orchestrator" "port" 8080 "context" .) }}
*/}}
{{- define "nexus.serviceUrl" -}}
{{- $fullname := include "nexus.fullname" .context -}}
http://{{ $fullname }}-{{ .name }}:{{ .port }}
{{- end }}

{{/*
Generate internal service DNS name
*/}}
{{- define "nexus.serviceDns" -}}
{{- $fullname := include "nexus.fullname" .context -}}
{{ $fullname }}-{{ .name }}.{{ .context.Release.Namespace }}.svc.cluster.local
{{- end }}

{{/*
=============================================================================
SECURITY CONTEXT
=============================================================================
*/}}

{{/*
Pod security context
*/}}
{{- define "nexus.podSecurityContext" -}}
runAsNonRoot: true
runAsUser: 1000
runAsGroup: 1000
fsGroup: 1000
fsGroupChangePolicy: "OnRootMismatch"
seccompProfile:
  type: RuntimeDefault
{{- end }}

{{/*
Container security context
*/}}
{{- define "nexus.containerSecurityContext" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
runAsNonRoot: true
runAsUser: 1000
runAsGroup: 1000
capabilities:
  drop:
    - ALL
seccompProfile:
  type: RuntimeDefault
{{- end }}

{{/*
=============================================================================
PROBES
=============================================================================
*/}}

{{/*
Liveness probe configuration
Usage: {{ include "nexus.livenessProbe" (dict "port" 8080 "path" "/health") }}
*/}}
{{- define "nexus.livenessProbe" -}}
livenessProbe:
  httpGet:
    path: {{ .path | default "/health" }}
    port: {{ .port | default "http" }}
    scheme: HTTP
  initialDelaySeconds: {{ .initialDelaySeconds | default 15 }}
  periodSeconds: {{ .periodSeconds | default 20 }}
  timeoutSeconds: {{ .timeoutSeconds | default 5 }}
  successThreshold: 1
  failureThreshold: {{ .failureThreshold | default 3 }}
{{- end }}

{{/*
Readiness probe configuration
*/}}
{{- define "nexus.readinessProbe" -}}
readinessProbe:
  httpGet:
    path: {{ .path | default "/health" }}
    port: {{ .port | default "http" }}
    scheme: HTTP
  initialDelaySeconds: {{ .initialDelaySeconds | default 5 }}
  periodSeconds: {{ .periodSeconds | default 10 }}
  timeoutSeconds: {{ .timeoutSeconds | default 5 }}
  successThreshold: 1
  failureThreshold: {{ .failureThreshold | default 3 }}
{{- end }}

{{/*
Startup probe for slow-starting containers
*/}}
{{- define "nexus.startupProbe" -}}
startupProbe:
  httpGet:
    path: {{ .path | default "/health" }}
    port: {{ .port | default "http" }}
    scheme: HTTP
  initialDelaySeconds: {{ .initialDelaySeconds | default 5 }}
  periodSeconds: {{ .periodSeconds | default 5 }}
  timeoutSeconds: {{ .timeoutSeconds | default 5 }}
  successThreshold: 1
  failureThreshold: {{ .failureThreshold | default 30 }}
{{- end }}

{{/*
=============================================================================
AFFINITY & TOPOLOGY
=============================================================================
*/}}

{{/*
Pod anti-affinity for high availability
Usage: {{ include "nexus.podAntiAffinity" (dict "component" "orchestrator" "context" .) }}
*/}}
{{- define "nexus.podAntiAffinity" -}}
{{- if .context.Values.global.highAvailability.enabled }}
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app.kubernetes.io/component: {{ .component }}
              app.kubernetes.io/instance: {{ .context.Release.Name }}
          topologyKey: kubernetes.io/hostname
      - weight: 50
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app.kubernetes.io/component: {{ .component }}
              app.kubernetes.io/instance: {{ .context.Release.Name }}
          topologyKey: topology.kubernetes.io/zone
{{- end }}
{{- end }}

{{/*
Topology spread constraints
*/}}
{{- define "nexus.topologySpreadConstraints" -}}
{{- if .context.Values.global.highAvailability.enabled }}
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels:
        app.kubernetes.io/component: {{ .component }}
        app.kubernetes.io/instance: {{ .context.Release.Name }}
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels:
        app.kubernetes.io/component: {{ .component }}
        app.kubernetes.io/instance: {{ .context.Release.Name }}
{{- end }}
{{- end }}

{{/*
=============================================================================
LIFECYCLE
=============================================================================
*/}}

{{/*
Container lifecycle hooks for graceful shutdown
*/}}
{{- define "nexus.lifecycle" -}}
lifecycle:
  preStop:
    exec:
      command:
        - /bin/sh
        - -c
        - "sleep 10"
{{- end }}

{{/*
=============================================================================
INIT CONTAINERS
=============================================================================
*/}}

{{/*
Init container to wait for dependencies
Usage: {{ include "nexus.initContainerWaitFor" (dict "service" "redis" "port" 6379 "context" .) }}
*/}}
{{- define "nexus.initContainerWaitFor" -}}
- name: wait-for-{{ .service }}
  image: busybox:1.36
  imagePullPolicy: IfNotPresent
  command:
    - /bin/sh
    - -c
    - |
      echo "Waiting for {{ .service }} at {{ .host }}:{{ .port }}..."
      until nc -z {{ .host }} {{ .port }}; do
        echo "{{ .service }} not ready, sleeping..."
        sleep 2
      done
      echo "{{ .service }} is ready!"
  securityContext:
    {{- include "nexus.containerSecurityContext" . | nindent 4 }}
  resources:
    requests:
      cpu: 10m
      memory: 16Mi
    limits:
      cpu: 50m
      memory: 32Mi
{{- end }}

{{/*
=============================================================================
ANNOTATIONS
=============================================================================
*/}}

{{/*
Prometheus annotations for scraping
*/}}
{{- define "nexus.prometheusAnnotations" -}}
prometheus.io/scrape: "true"
prometheus.io/port: {{ .port | quote }}
prometheus.io/path: {{ .path | default "/metrics" | quote }}
{{- end }}

{{/*
Checksum annotation for config changes triggering rolling update
*/}}
{{- define "nexus.checksumAnnotations" -}}
checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
checksum/secret: {{ include (print $.Template.BasePath "/secrets.yaml") . | sha256sum }}
{{- end }}

{{/*
=============================================================================
REDIS & POSTGRESQL
=============================================================================
*/}}

{{/*
Redis URL based on deployment mode
*/}}
{{- define "nexus.redisUrl" -}}
{{- if .Values.redis.enabled -}}
redis://{{ .Release.Name }}-redis-master:6379
{{- else -}}
{{ .Values.externalRedis.url }}
{{- end -}}
{{- end }}

{{/*
PostgreSQL URL based on deployment mode
*/}}
{{- define "nexus.postgresUrl" -}}
{{- if .Values.postgresql.enabled -}}
postgresql://{{ .Values.postgresql.auth.username }}:$(POSTGRES_PASSWORD)@{{ .Release.Name }}-postgresql:5432/{{ .Values.postgresql.auth.database }}
{{- else -}}
{{ .Values.externalPostgresql.url }}
{{- end -}}
{{- end }}

{{/*
PostgreSQL host
*/}}
{{- define "nexus.postgresHost" -}}
{{- if .Values.postgresql.enabled -}}
{{ .Release.Name }}-postgresql
{{- else -}}
{{ .Values.externalPostgresql.host }}
{{- end -}}
{{- end }}

{{/*
=============================================================================
RESOURCE NAMES
=============================================================================
*/}}

{{/*
Generate component full name
Usage: {{ include "nexus.componentName" (dict "component" "orchestrator" "context" .) }}
*/}}
{{- define "nexus.componentName" -}}
{{ include "nexus.fullname" .context }}-{{ .component }}
{{- end }}

{{/*
Generate secret name for a component
*/}}
{{- define "nexus.secretName" -}}
{{- if .existingSecret -}}
{{ .existingSecret }}
{{- else -}}
{{ include "nexus.componentName" . }}-secrets
{{- end -}}
{{- end }}

{{/*
Generate ConfigMap name for a component
*/}}
{{- define "nexus.configMapName" -}}
{{ include "nexus.componentName" . }}-config
{{- end }}
