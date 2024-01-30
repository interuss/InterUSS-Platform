
# This file has been automatically generated by /deploy/infrastructure/utils/generate_terraform_variables.py.
# Please do not modify manually.

variable "aws_region" {
  type        = string
  description = <<-EOT
    AWS region
    List of available regions: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-regions
    Currently, the terraform module uses the two first availability zones of the region.

    Example: `eu-west-1`
  EOT
}

variable "aws_instance_type" {
  type        = string
  description = <<-EOT
    AWS EC2 instance type used for the Kubernetes node pool.

    Example: `m6g.xlarge` for production and `t3.medium` for development
  EOT
}

variable "aws_route53_zone_id" {
  type        = string
  description = <<-EOT
    AWS Route 53 Zone ID
    This module can automatically create DNS records in a Route 53 Zone.
    Leave empty to disable record creation.

    Example: `Z0123456789ABCDEFGHIJ`
  EOT
}

variable "aws_iam_permissions_boundary" {
  type        = string
  description = <<-EOT
    AWS IAM Policy ARN to be used for permissions boundaries on created roles.

    Example: `arn:aws:iam::123456789012:policy/GithubCIPermissionBoundaries`
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

variable "kubernetes_version" {
  type        = string
  description = <<-EOT
    Desired version of the Kubernetes cluster control plane and nodes.

    Supported versions:
      - 1.24
  EOT

  validation {
    condition     = contains(["1.24", "1.25", "1.26", "1.27", "1.28"], var.kubernetes_version)
    error_message = "Supported versions: 1.24, 1.25, 1.26, 1.27 and 1.28"
  }
}


