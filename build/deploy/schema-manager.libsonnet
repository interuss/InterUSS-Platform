local base = import 'base.libsonnet';
local volumes = import 'volumes.libsonnet';
local defaultdb_schema = import "db-schemas/defaultdb.libsonnet";

local rid_schema_vol = {
  name: 'db-rid-schema',
  configMap: {
    defaultMode: 420,
    name: 'db-rid-schema',
  },
};
local rid_schema_mount = {
  name: 'db-rid-schema',
  readOnly: false,
  mountPath: '/db-schemas/defaultdb',
};

{
  all(metadata): {
    assert metadata.cockroach.shouldInit == true && metadata.cockroach.JoinExisting == [] : "If shouldInit is True, JoinExisiting should be empty",
    rid_schema: base.ConfigMap(metadata, 'db-rid-schema') {
      data: defaultdb_schema.data
    },
    RIDSchemaManager: if metadata.cockroach.shouldInit then base.Job(metadata, 'rid-schema-manager') {
      spec+: {
        template+: {
          spec+: {
            volumes_: {
              client_certs: volumes.volumes.client_certs,
              ca_certs: volumes.volumes.ca_certs,
              rid_schema: rid_schema_vol,
            },
            soloContainer:: base.Container('schema-manager') {
              image: metadata.schema_manager.image,
              args_:: {
                cockroach_host: 'cockroachdb-balanced.' + metadata.namespace,
                cockroach_port: metadata.cockroach.grpc_port,
                cockroach_ssl_mode: 'verify-full',
                cockroach_user: 'root',
                cockroach_ssl_dir: '/cockroach/cockroach-certs',
                db_version: metadata.schema_manager.desired_rid_db_version,
                schemas_dir: rid_schema_mount.mountPath,

              },
              volumeMounts: volumes.mounts.caCert + volumes.mounts.clientCert + [rid_schema_mount],
            },
          },
        },
      },
    } else null,
  },
}