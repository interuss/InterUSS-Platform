local base = import 'base.libsonnet';
local volumes = import 'volumes.libsonnet';
local cloud_providers = import 'cloud_providers.libsonnet';

local awsLoadBalancer(metadata) = base.AWSLoadBalancerWithManagedCert(metadata, 'gateway', [metadata.backend.ipName], metadata.backend.certName) {
  app:: 'core-service',
  spec+: {
    ports: [{
      port: 443,
      targetPort: metadata.backend.port,
      protocol: "TCP",
      name: "http",
    }]
  }
};

{
  GoogleManagedCertIngress(metadata): {
    local certName = 'https-certificate',
    ingress: base.Ingress(metadata, 'https-ingress') {
      metadata+: {
        annotations+: {
          'networking.gke.io/managed-certificates': certName,
          'kubernetes.io/ingress.global-static-ip-name': metadata.backend.ipName,
          'kubernetes.io/ingress.allow-http': 'false',
        },
      },
      spec: {
        defaultBackend: {
          service: {
            name: 'core-service',
            port: {
              number: metadata.backend.port,
            }
          }
        },
      },
    },
    managedCert: base.ManagedCert(metadata, certName) {
      spec: {
        domains: [
          metadata.backend.hostname,
        ],
      },
    },
    service: base.Service(metadata, 'core-service') {
      app:: 'core-service',
      port:: metadata.backend.port,
      type:: 'NodePort',
      enable_monitoring:: false,
    },
  },

  CloudNetwork(metadata): {
    google: if metadata.cloud_provider.name == "google" then $.GoogleManagedCertIngress(metadata),
    aws_loadbalancer: if metadata.cloud_provider.name == "aws" then awsLoadBalancer(metadata)
  },

  all(metadata): {
    network: $.CloudNetwork(metadata),

    deployment: base.Deployment(metadata, 'core-service') {
      apiVersion: 'apps/v1',
      kind: 'Deployment',
      metadata+: {
        namespace: metadata.namespace,
      },
      spec+: {
        template+: {
          spec+: {
            volumes: volumes.backendVolumes,
            soloContainer:: base.Container('core-service') {
              image: metadata.backend.image,
              imagePullPolicy: 'Always',
              ports: [
                {
                  containerPort: metadata.backend.port,
                  name: 'http',
                },
              ],
              volumeMounts: volumes.backendMounts,
              command: ['core-service'],
              args_:: {
                addr: ':' + metadata.backend.port,
                gcp_prof_service_name: metadata.backend.prof_grpc_name,
                cockroach_host: 'cockroachdb-balanced.' + metadata.namespace,
                cockroach_port: metadata.cockroach.grpc_port,
                cockroach_ssl_mode: 'verify-full',
                cockroach_user: 'root',
                cockroach_ssl_dir: '/cockroach/cockroach-certs',
                garbage_collector_spec: '@every 30m',
                public_key_files: std.join(",", metadata.backend.pubKeys),
                jwks_endpoint: metadata.backend.jwksEndpoint,
                jwks_key_ids: std.join(",", metadata.backend.jwksKeyIds),
                dump_requests: metadata.backend.dumpRequests,
                accepted_jwt_audiences: metadata.backend.hostname,
                locality: metadata.cockroach.locality,
                enable_scd: metadata.enableScd,
              },
              readinessProbe: {
                httpGet: {
                  path: '/healthy',
                  port: metadata.backend.port,
                },
              },
            },
          },
        },
      },
    },
  },
}
