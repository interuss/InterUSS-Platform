
# This file has been automatically generated by /deploy/infrastructure/utils/generate_terraform_variables.py.
# Please do not modify manually.

variable "google_project_name" {
  type        = string
  description = "Name of the GCP project hosting the future cluster"
}

variable "google_zone" {
  type        = string
  description = <<-EOT
    GCP zone hosting the kubernetes cluster
    List of available zones: https://cloud.google.com/compute/docs/regions-zones#available

    Example: `europe-west6-a`
  EOT
}

variable "google_dns_managed_zone_name" {
  type        = string
  description = <<-EOT
    GCP DNS zone name to automatically manage DNS entries.

    Leave it empty to manage it manually.
  EOT
}

variable "google_machine_type" {
  type        = string
  description = <<-EOT
    GCP machine type used for the Kubernetes node pool.
    Example: `n2-standard-4` for production, `e2-medium` for development
  EOT
}

variable "app_hostname" {
  type        = string
  description = <<-EOT
  Fully-qualified domain name of your HTTPS Gateway ingress endpoint.

  Example: `dss.example.com`
  EOT
}

variable "crdb_hostname_suffix" {
  type        = string
  description = <<-EOT
  The domain name suffix shared by all of your CockroachDB nodes.
  For instance, if your CRDB nodes were addressable at 0.db.example.com,
  1.db.example.com and 2.db.example.com, then the value would be db.example.com.

  Example: db.example.com
  EOT
}

variable "cluster_name" {
  type        = string
  description = <<-EOT
    Name of the kubernetes cluster that will host this DSS instance (should generally describe the DSS instance being hosted)

    Example: `dss-che-1`
  EOT
}

variable "node_count" {
  type        = number
  description = <<-EOT
    Number of Kubernetes nodes which should correspond to the desired CockroachDB nodes.
    **Always 3.**

    Example: `3`
  EOT

  validation {
    condition     = var.node_count == 3
    error_message = "Node count should be 3. Only configuration supported at the moment"
  }
}

variable "google_kubernetes_storage_class" {
  type        = string
  description = <<-EOT
  GCP Kubernetes Storage Class to use for CockroachDB and Prometheus persistent volumes.
  See https://cloud.google.com/kubernetes-engine/docs/concepts/persistent-volumes for more details and
  available options.

  Example: `standard`
  EOT
}

variable "image" {
  type        = string
  description = <<EOT
  URL of the DSS docker image.


  `latest` can be used to use the latest official interuss docker image.
  Official public images are available on Docker Hub: https://hub.docker.com/r/interuss/dss/tags
  See [/build/README.md](../../../../build/README.md#docker-images) Docker images section to learn
  how to build and publish your own image.

  Example: `latest` or `docker.io/interuss/dss:v0.6.0`
  EOT
}

variable "authorization" {
  type = object({
    public_key_pem_path = optional(string)
    jwks = optional(object({
      endpoint = string
      key_id   = string
    }))
  })
  description = <<EOT
    One of `public_key_pem_path` or `jwks` should be provided but not both.

    - public_key_pem_path
      If providing the access token public key via JWKS, do not provide this parameter.
      If providing a .pem file directly as the public key to validate incoming access tokens, specify the name
      of this .pem file here as /public-certs/YOUR-KEY-NAME.pem replacing YOUR-KEY-NAME as appropriate. For instance,
      if using the provided us-demo.pem, use the path /public-certs/us-demo.pem. Note that your .pem file should built
      in the docker image or mounted manually.

      Example 1 (dummy auth):
      '''
      {
        public_key_pem_path = "/test-certs/auth2.pem"
      }
      '''
      Example 2:
      '''
      {
        public_key_pem_path = "/jwt-public-certs/us-demo.pem"
      }
      '''

    - jwks
        If providing a .pem file directly as the public key to validate incoming access tokens, do not provide this parameter.
        - endpoint
          If providing the access token public key via JWKS, specify the JWKS endpoint here.
          Example: https://auth.example.com/.well-known/jwks.json
        - key_id:
          If providing the access token public key via JWKS, specify the kid (key ID) of they appropriate key in the JWKS file referenced above.
      Example:
      '''
      {
        jwks = {
          endpoint = "https://auth.example.com/.well-known/jwks.json"
          key_id = "9C6DF78B-77A7-4E89-8990-E654841A7826"
        }
      }
      '''
  EOT

  validation {
    condition     = (var.authorization.jwks == null && var.authorization.public_key_pem_path != null) || (var.authorization.jwks != null && var.authorization.public_key_pem_path == null)
    error_message = "Public key to validate incoming access tokens shall be provided exclusively either with a .pem file or via JWKS."
  }
}

variable "enable_scd" {
  type        = bool
  description = "Set this boolean true to enable ASTM strategic conflict detection functionality"
  default     = true
}

variable "should_init" {
  type        = bool
  description = <<-EOT
    Set to false if joining an existing pool, true if creating the first DSS instance
    for a pool. When set true, this can initialize the data directories on your cluster,
    and prevent you from joining an existing pool.

    Example: `true`
    EOT
}

variable "desired_rid_db_version" {
  type        = string
  description = <<EOT
    Desired RID DB schema version.
    Use `latest` to use the latest schema version.

    Example: `4.0.0`
  EOT

  default = "latest"
}

variable "desired_scd_db_version" {
  type        = string
  description = <<EOT
    Desired SCD DB schema version.
    Use `latest` to use the latest schema version.

    Example: `3.1.0`
  EOT

  default = "latest"
}

variable "crdb_locality" {
  type        = string
  description = <<-EOT
    Unique name for your DSS instance. Currently, we recommend "<ORG_NAME>_<CLUSTER_NAME>",
    and the = character is not allowed. However, any unique (among all other participating
    DSS instances) value is acceptable.

    Example: <ORGNAME_CLUSTER_NAME>
  EOT
}

variable "crdb_external_nodes" {
  type        = list(string)
  description = <<-EOT
    Fully-qualified domain name of existing CRDB nodes outside of the cluster if you are joining an existing pool.
    Example: ["0.db.dss.example.com", "1.db.dss.example.com", "2.db.dss.example.com"]
  EOT
  default     = []
}

variable "kubernetes_namespace" {
  type        = string
  description = <<-EOT
    Namespace where to deploy Kubernetes resources. Only default is supported at the moment.

    Example: `default`
  EOT

  default = "default"

  # TODO: Adapt current deployment scripts in /build/deploy to support default is supported for the moment.
  validation {
    condition     = var.kubernetes_namespace == "default"
    error_message = "Only default namespace is supported at the moment"
  }
}

