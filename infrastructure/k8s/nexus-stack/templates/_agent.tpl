{{/*
=============================================================================
NEXUS AGENT TEMPLATE
=============================================================================
Reusable template for all specialist agents.
Usage: {{ include "nexus.agentDeployment" (dict "name" "jira-agent" "config" .Values.jiraAgent "context" .) }}
=============================================================================
*/}}

{{- define "nexus.agentDeployment" -}}
{{- $name := .name }}
{{- $config := .config }}
{{- $context := .context }}
{{- $port := .port }}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "nexus.componentName" (dict "component" $name "context" $context) }}
  labels:
    {{- include "nexus.componentLabels" (dict "component" $name "context" $context) | nindent 4 }}
spec:
  {{- if not $config.autoscaling.enabled }}
  replicas: {{ $config.replicas }}
  {{- end }}
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      {{- include "nexus.componentSelectorLabels" (dict "component" $name "context" $context) | nindent 6 }}
  template:
    metadata:
      annotations:
        {{- with $config.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
        checksum/secret: {{ include (print $.Template.BasePath "/secrets.yaml") $context | sha256sum | trunc 8 }}
      labels:
        {{- include "nexus.componentSelectorLabels" (dict "component" $name "context" $context) | nindent 8 }}
    spec:
      {{- include "nexus.imagePullSecrets" (dict "global" $context.Values.global "imageConfig" $config.image) | nindent 6 }}
      serviceAccountName: {{ include "nexus.serviceAccountName" $context }}
      securityContext:
        {{- toYaml $context.Values.podSecurityContext | nindent 8 }}
      terminationGracePeriodSeconds: 30
      
      containers:
        - name: {{ $name }}
          image: {{ include "nexus.image" (dict "imageConfig" $config.image "global" $context.Values.global "Chart" $context.Chart) }}
          imagePullPolicy: {{ include "nexus.imagePullPolicy" (dict "imageConfig" $config.image "global" $context.Values.global) }}
          
          securityContext:
            {{- toYaml $context.Values.containerSecurityContext | nindent 12 }}
          
          ports:
            - name: http
              containerPort: {{ $port }}
              protocol: TCP
          
          env:
            # Redis URL
            - name: REDIS_URL
              value: {{ include "nexus.redisUrl" $context }}
            
            # OpenTelemetry
            {{- if $context.Values.observability.tracing.enabled }}
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: {{ $context.Values.observability.tracing.endpoint }}
            {{- end }}
            
            # User-defined environment variables
            {{- range $key, $value := $config.env }}
            - name: {{ $key }}
              value: {{ $value | quote }}
            {{- end }}
          
          envFrom:
            {{- if $config.secrets }}
            - secretRef:
                name: {{ include "nexus.componentName" (dict "component" $name "context" $context) }}-secrets
            {{- end }}
          
          {{- include "nexus.startupProbe" (dict "port" "http" "path" "/health") | nindent 10 }}
          {{- include "nexus.livenessProbe" (dict "port" "http" "path" "/health") | nindent 10 }}
          {{- include "nexus.readinessProbe" (dict "port" "http" "path" "/health") | nindent 10 }}
          
          resources:
            {{- toYaml $config.resources | nindent 12 }}
          
          {{- include "nexus.lifecycle" $context | nindent 10 }}
          
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      
      volumes:
        - name: tmp
          emptyDir: {}
      
      {{- with $config.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      
      {{- with $config.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      
      {{- if $context.Values.global.highAvailability.enabled }}
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    {{- include "nexus.componentSelectorLabels" (dict "component" $name "context" $context) | nindent 20 }}
                topologyKey: kubernetes.io/hostname
      {{- end }}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ include "nexus.componentName" (dict "component" $name "context" $context) }}
  labels:
    {{- include "nexus.componentLabels" (dict "component" $name "context" $context) | nindent 4 }}
spec:
  type: {{ $config.service.type | default "ClusterIP" }}
  ports:
    - port: {{ $config.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "nexus.componentSelectorLabels" (dict "component" $name "context" $context) | nindent 4 }}
{{- if $config.autoscaling.enabled }}
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "nexus.componentName" (dict "component" $name "context" $context) }}
  labels:
    {{- include "nexus.componentLabels" (dict "component" $name "context" $context) | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "nexus.componentName" (dict "component" $name "context" $context) }}
  minReplicas: {{ $config.autoscaling.minReplicas }}
  maxReplicas: {{ $config.autoscaling.maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ $config.autoscaling.targetCPUUtilizationPercentage | default 70 }}
{{- end }}
{{- if $config.pdb.enabled }}
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ include "nexus.componentName" (dict "component" $name "context" $context) }}
  labels:
    {{- include "nexus.componentLabels" (dict "component" $name "context" $context) | nindent 4 }}
spec:
  minAvailable: {{ $config.pdb.minAvailable | default 1 }}
  selector:
    matchLabels:
      {{- include "nexus.componentSelectorLabels" (dict "component" $name "context" $context) | nindent 6 }}
{{- end }}
{{- end }}

