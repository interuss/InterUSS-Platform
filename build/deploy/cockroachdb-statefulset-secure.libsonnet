// kube.libsonnet is an import from bitnami, we would not maintain this import this way.
local kube = import "kube.libsonnet"; 
local common = import "common.libsonnet";

local crLabels = {
  metadata+: {
    labels: {
      app: "cockroachdb",
    }
  }
};

{
  meta: {
    svcAccount: kube.ServiceAccount("cockroachdb") + crLabels,
  },

  StatefulSet: kube.StatefulSet("cockroachdb") + crLabels {
    local dbHostnameSuffix_ = self.dbHostnameSuffix,
    local locality_ = self.locality,
    local namespace_ = self.namespace,
    dbHostnameSuffix:: error "must supply db hostname suffix",
    locality:: error "must supply locality",
    namespace: "default-ns",   # TODO: set namespace better.
    spec+: {
      serviceName: "cockroachdb",
      replicas: 3,  # default number of replicas.
      template+: {
        spec+: {
          volumes: common.cockroach.volumes,
          containers_:: {
            cockroachdb: kube.Container("cockroachdb") {
              // TODO stub this.
              image: "cockroachdb",
              volumeMounts:: [
                {
                  name: "certs",
                  mountPath: "/cockroach/cockroach-certs"
                },
                {
                  name: "datadir",
                  mountPath: "/cockroach/cockroach-data",
                },
              ],
              ports: [
                {
                  containerPort: common.cockroach.grpc_port,
                  targetPort: common.cockroach.http_port,
                },
              ],
              livenessProbe: {
                httpGet: {
                  path: "/health",
                  port: "http",
                  scheme: "HTTPS",
                },
                initialDelaySeconds: 30,
                periodSeconds: 5,
              },
              readinessProbe: {
                httpGet: {
                  path: "/health?ready=1",
                  port: "http",
                  scheme: "HTTPS",
                },
                initialDelaySeconds: 10,
                periodSeconds: 5,
                failureThreshold: 2
              },
              command: [
                "/bin/bash",
                "-ecx",
                ">-",
                "exec /cockroach/cockroach start",
              ],
              args_:: {
                "certs-dir": "/cockroach-certs",
                "advertise-addr": "${HOSTNAME##*-}." + dbHostnameSuffix_,
                join: "cockroachdb-0.cockroachdb." + namespace_ + ".svc.cluster.local",
                logtostderr: true,
                "locality-advertise-addr": "zone=" + locality_ +"@$(hostname -f)",
                "http-addr": "0.0.0.0",
                cache: "25%",
                "max-sql-memory": "25%",
              },
            },
          },
        },
      }
    },
  },
}

#         command:
#           - "/bin/bash"
#           - "-ecx"
#           # The use of qualified `hostname -f` is crucial:
#           # Other nodes aren't able to look up the unqualified hostname.
#           - >-
#             exec /cockroach/cockroach start
#             --logtostderr
#             --certs-dir "/cockroach/cockroach-certs"
#             --advertise-addr "$(printenv EXTERNAL_HOSTNAME_FOR_$HOSTNAME)"
#             --locality-advertise-addr "zone={{ .Values.Locality }}@$(hostname -f)"
#             --http-addr 0.0.0.0
#             --join "{{ range $index := list 0 1 2 -}}
#                 {{- if ne $index 0 }},{{ end -}}
#                 cockroachdb-{{ $index }}.cockroachdb.{{ $.Values.Namespace }}.svc.cluster.local:{{ $.Values.CockroachPort }}
#               {{- end -}}
#               {{- if .Values.JoinExisting -}}
#                 ,{{ join "," .Values.JoinExisting -}}
#               {{ end }}"
#             --locality "zone={{ .Values.Locality }}"
#             --cache 25%
#             --max-sql-memory 25%
#       # No pre-stop hook is required, a SIGTERM plus some time is all that's
#       # needed for graceful shutdown of a node.
#       terminationGracePeriodSeconds: 60
#       volumes:
#       - name: datadir
#         persistentVolumeClaim:
#           claimName: datadir
#       - name: certs
#         secret:
#           secretName: cockroachdb.node
#           defaultMode: 256
#   podManagementPolicy: Parallel
#   updateStrategy:
#     type: RollingUpdate
#   volumeClaimTemplates:
#   - metadata:
#       name: datadir
#     spec:
#       storageClassName: {{ .Values.StorageClass }}
#       accessModes:
#         - "ReadWriteOnce"
#       resources:
#         requests:
#           storage: {{ .Values.StorageSize }}





# apiVersion: rbac.authorization.k8s.io/v1beta1
# kind: Role
# metadata:
#   name: cockroachdb
#   namespace: {{ .Values.Namespace }}
#   labels:
#     app: cockroachdb
# rules:
# - apiGroups:
#   - ""
#   resources:
#   - secrets
#   verbs:
#   - create
#   - get
# ---
# apiVersion: rbac.authorization.k8s.io/v1beta1
# kind: ClusterRole
# metadata:
#   name: cockroachdb
#   labels:
#     app: cockroachdb
# rules:
# - apiGroups:
#   - certificates.k8s.io
#   resources:
#   - certificatesigningrequests
#   verbs:
#   - create
#   - get
#   - watch
# ---
# apiVersion: rbac.authorization.k8s.io/v1beta1
# kind: RoleBinding
# metadata:
#   name: cockroachdb
#   namespace: {{ .Values.Namespace }}
#   labels:
#     app: cockroachdb
# roleRef:
#   apiGroup: rbac.authorization.k8s.io
#   kind: Role
#   name: cockroachdb
# subjects:
# - kind: ServiceAccount
#   name: cockroachdb
#   namespace: {{ .Values.Namespace }}
# ---
# apiVersion: rbac.authorization.k8s.io/v1beta1
# kind: ClusterRoleBinding
# metadata:
#   name: cockroachdb
#   labels:
#     app: cockroachdb
# roleRef:
#   apiGroup: rbac.authorization.k8s.io
#   kind: ClusterRole
#   name: cockroachdb
# subjects:
# - kind: ServiceAccount
#   name: cockroachdb
#   namespace: default
# ---
# apiVersion: v1
# kind: Service
# metadata:
#   # This service only exists to create DNS entries for each pod in the stateful
#   # set such that they can resolve each other's IP addresses. It does not
#   # create a load-balanced ClusterIP and should not be used directly by clients
#   # in most circumstances.
#   name: cockroachdb
#   namespace: {{ .Values.Namespace }}
#   labels:
#     app: cockroachdb
#   annotations:
#     # Use this annotation in addition to the actual publishNotReadyAddresses
#     # field below because the annotation will stop being respected soon but the
#     # field is broken in some versions of Kubernetes:
#     # https://github.com/kubernetes/kubernetes/issues/58662
#     service.alpha.kubernetes.io/tolerate-unready-endpoints: "true"
#     # Enable automatic monitoring of all instances when Prometheus is running in the cluster.
#     prometheus.io/scrape: "true"
#     prometheus.io/path: "_status/vars"
#     prometheus.io/port: "{{ .Values.HttpPort }}"
# spec:
#   ports:
#   - port: {{ .Values.CockroachPort }}
#     targetPort: {{ .Values.CockroachPort }}
#     name: cockroach
#   - port: {{ .Values.HttpPort }}
#     targetPort: {{ .Values.HttpPort }}
#     name: http
#   # We want all pods in the StatefulSet to have their addresses published for
#   # the sake of the other CockroachDB pods even before they're ready, since they
#   # have to be able to talk to each other in order to become ready.
#   publishNotReadyAddresses: true
#   clusterIP: None
#   selector:
#     app: cockroachdb
# ---
# apiVersion: policy/v1beta1
# kind: PodDisruptionBudget
# metadata:
#   name: cockroachdb-budget
#   namespace: {{ .Values.Namespace }}
#   labels:
#     app: cockroachdb
# spec:
#   selector:
#     matchLabels:
#       app: cockroachdb
#   maxUnavailable: 1
# ---
# apiVersion: v1
# kind: Service
# metadata:
#   # This service is meant to be used by clients of the database. It exposes a ClusterIP that will
#   # automatically load balance connections to the different database pods.
#   name: cockroachdb-balanced
#   namespace: {{ .Values.Namespace }}
#   labels:
#     app: cockroachdb
# spec:
#   ports:
#   # The main port, served by gRPC, serves Postgres-flavor SQL, internode
#   # traffic and the cli.
#   - port: {{ .Values.CockroachPort }}
#     targetPort: {{ .Values.CockroachPort }}
#     name: cockroach
#   # The secondary port serves the UI as well as health and debug endpoints.
#   - port: {{ .Values.HttpPort }}
#     targetPort: {{ .Values.HttpPort }}
#     name: http
#   selector:
#     app: cockroachdb
#   sessionAffinity: ClientIP
# ---
