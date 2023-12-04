#! python3

# This script is used to generate the terraform variables definitions and documentation.
# This is particularly helpful since most of the variables are nested in submodules
# (See modules and dependencies in /deploy/infrastructure).

from os import listdir
from os.path import isfile, join, abspath, dirname, exists
from typing import Dict, List, Tuple
import hcl2

DEFINITIONS_PATH = join(abspath(dirname(__file__)), "definitions")
GENERATED_TFVARS_MD_FILENAME = "TFVARS.md"
GENERATED_VARIABLES_FILENAME = "variables.tf"
INTERNAL_VARIABLES_FILENAME = "variables_internal.tf"
GENERATED_COMMENT = """
# This file has been automatically generated by /deploy/infrastructure/utils/generate_terraform_variables.py.
# Please do not modify manually.
"""

# Variables per project
# For all */terraform-*
GLOBAL_VARIABLES = [
    "app_hostname",
    "crdb_hostname_suffix"
]

# dependencies/terraform-commons-dss
COMMONS_DSS_VARIABLES = GLOBAL_VARIABLES + [
    "image",
    "image_pull_secret",
    "authorization",
    "enable_scd",
    "should_init",
    "desired_rid_db_version",
    "desired_scd_db_version",
    "crdb_locality",
    "crdb_external_nodes",
    "kubernetes_namespace",
]

# dependencies/terraform-*-kubernetes
COMMON_KUBERNETES_VARIABLES = GLOBAL_VARIABLES + [
    "cluster_name",
    "node_count",
]

# dependencies/terraform-google-kubernetes
GOOGLE_KUBERNETES_VARIABLES = [
    "google_project_name",
    "google_zone",
    "google_dns_managed_zone_name",
    "google_machine_type",
] + COMMON_KUBERNETES_VARIABLES

# modules/terraform-google-dss
GOOGLE_MODULE_VARIABLES = (
    GOOGLE_KUBERNETES_VARIABLES
    + [
        "google_kubernetes_storage_class",
    ]
    + COMMONS_DSS_VARIABLES
)

# dependencies/terraform-aws-kubernetes
AWS_KUBERNETES_VARIABLES = [
    "aws_region",
    "aws_instance_type",
    "aws_route53_zone_id",
    "aws_iam_path",
    "aws_iam_permissions_boundary"
] + COMMON_KUBERNETES_VARIABLES

# modules/terraform-aws-dss
AWS_MODULE_VARIABLES = (
    AWS_KUBERNETES_VARIABLES + ["aws_kubernetes_storage_class"] + COMMONS_DSS_VARIABLES
)

PROJECT_VARIABLES = {
    "../modules/terraform-aws-dss": list(
        dict.fromkeys(AWS_MODULE_VARIABLES)
    ),  # Preserves the items order.
    "../modules/terraform-google-dss": list(
        dict.fromkeys(GOOGLE_MODULE_VARIABLES)
    ),  # Preserves the items order.
    "../dependencies/terraform-aws-kubernetes": AWS_KUBERNETES_VARIABLES,
    "../dependencies/terraform-google-kubernetes": GOOGLE_KUBERNETES_VARIABLES,
    "../dependencies/terraform-commons-dss": COMMONS_DSS_VARIABLES,
}


def is_example_project(path: str) -> bool:
    """
    Return if the path corresponds to a project which requires example files.
    """
    return "/modules/" in path


def load_tf_definitions() -> Dict[str, str]:
    """
    Load terraform variables definitions and return a dictionary
    where keys are the variable name and the value the content of the file.
    """
    variables = [
        f.replace(".tf", "")
        for f in listdir(DEFINITIONS_PATH)
        if isfile(join(DEFINITIONS_PATH, f))
    ]
    result = {}
    for variable in variables:
        with open(join(DEFINITIONS_PATH, f"{variable}.tf")) as f:
            result[variable] = f.read()
    return result


def parse_definition(variable_name: str, tf_definition: str) -> Tuple[str, str, str]:
    """
    Parse the tf content (hcl format) and retrieve the description field, variable_type and the default_value.
    """
    hcl_declaration = hcl2.loads(tf_definition)
    variables = hcl_declaration.get("variable")
    if len(variables) > 1:
        raise ValueError(
            f"More than one variable in {variable_name} definition file is not allowed. Content: {tf_definition}"
        )

    declared_var_name = list(variables[0].keys())[0]
    if declared_var_name != variable_name:
        raise ValueError(
            f"File name ({variable_name}) and variable name declaration ({declared_var_name}) do not match. Stop."
        )

    value_type = variables[0].get(declared_var_name).get("type", None)
    if value_type is None:
        raise ValueError(f"Type field required for variable {variable_name}.")
    value_type = value_type[
        2:-1
    ]  # Value type format includes a ${...} wrapper. This removes the wrapper.

    default_value = variables[0].get(declared_var_name).get("default", None)

    if value_type == "bool":
        default_value = str(default_value).lower()

    if value_type == "string" and default_value is not None:
        default_value = f'"{default_value}"'

    description = variables[0].get(declared_var_name).get("description", None)
    if description is None:
        raise ValueError(f"Description field required for variable {variable_name}.")

    return description, value_type, default_value


def write_file(filepath: str, content: str) -> None:
    print("*****")
    print("** " + filepath)
    print(content)
    with open(filepath, "wt") as file:
        file.write(content)


def comment(content: str) -> str:
    """
    This prefix the possibly multiline content with # to generate a commented block.
    """
    if content is None:
        return ""
    commented_lines = "\n".join([f"# {l}" for l in content.split("\n")])
    return commented_lines


def get_variables_tf_content(variables: List[str], definitions: Dict[str, str]) -> str:
    """
    Generate the content of variables.tf (Terraform definitions) based
    on the `variables` list. `variables` contains the variables names to
    include in the content. `definitions` contains the definitions of all
    available variables.
    returns the content of a tf file with the definitions of the variables.
    """
    content = GENERATED_COMMENT + "\n"
    for v in variables:
        if v not in definitions.keys():
            raise ValueError(f"{v} definition not found")
        content += definitions[v] + "\n\n"
    return content


def get_tfvars_md_content(
    project_name: str,
    variables: List[str],
    definitions: Dict[str, str],
    has_internal_vars: bool,
) -> str:
    content = f"<!-- {GENERATED_COMMENT} -->\n\n"
    content += "# Terraform variables\n\n"
    content += (
        "The following sections describe the variables of this terraform module.\n\n"
    )

    content += f"## {project_name}\n\n"

    for v in variables:
        description, value_type, default_value = parse_definition(v, definitions[v])
        content += f"### {v}\n\n"
        content += f"*Type: `{value_type}`*\n\n"
        content += (
            f"**Default: {default_value}**\n\n" if default_value is not None else ""
        )
        tabbed_description = "\n".join([d.strip() for d in description.split("\n")])
        content += f"{tabbed_description}\n\n\n"

    if has_internal_vars:
        content += f"## Internal variables\n\n"
        content += f"This module requires additional variables, see [{INTERNAL_VARIABLES_FILENAME}](./{INTERNAL_VARIABLES_FILENAME}) for details"

    return content


def has_internal_variables(path: str) -> bool:
    """Check if internal variables are declared."""
    return exists(join(path, INTERNAL_VARIABLES_FILENAME))


def write_files(definitions: Dict[str, str]):
    """
    Generate by project the variables tf file and the example tfvars for example projects.
    """
    for path, variables in PROJECT_VARIABLES.items():
        project_name = path.split("/")[-1]

        # Generate variables.tf definition
        var_filename = join(path, GENERATED_VARIABLES_FILENAME)
        content = get_variables_tf_content(variables, definitions)
        write_file(var_filename, content)

        if is_example_project(path):
            # Generate TFVARS.md documentation only for example projects
            tfvars_md_filename = join(path, GENERATED_TFVARS_MD_FILENAME)

            content = get_tfvars_md_content(
                project_name, variables, definitions, has_internal_variables(path)
            )
            write_file(tfvars_md_filename, content)


if __name__ == "__main__":
    definitions = load_tf_definitions()
    write_files(definitions)
