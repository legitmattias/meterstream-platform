[comment]: <> (README.md)   

## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 0.14.0 |
| <a name="requirement_openstack"></a> [openstack](#requirement\_openstack) | ~> 1.53.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_null"></a> [null](#provider\_null) | 3.2.4 |
| <a name="provider_openstack"></a> [openstack](#provider\_openstack) | 1.53.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [null_resource.wait_ssh](https://registry.terraform.io/providers/hashicorp/null/latest/docs/resources/resource) | resource |
| [openstack_compute_instance_v2.the_server](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/compute_instance_v2) | resource |
| [openstack_networking_floatingip_associate_v2.fip_1](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/networking_floatingip_associate_v2) | resource |
| [openstack_networking_floatingip_v2.the_floatip](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/networking_floatingip_v2) | resource |
| [openstack_networking_network_v2.the_network](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/networking_network_v2) | resource |
| [openstack_networking_port_v2.port_1](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/networking_port_v2) | resource |
| [openstack_networking_router_interface_v2.router_interface_1](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/networking_router_interface_v2) | resource |
| [openstack_networking_router_v2.the_router](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/networking_router_v2) | resource |
| [openstack_networking_secgroup_rule_v2.allow_k3s_api](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/networking_secgroup_rule_v2) | resource |
| [openstack_networking_secgroup_rule_v2.secgroup_rule_webport22](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/networking_secgroup_rule_v2) | resource |
| [openstack_networking_secgroup_rule_v2.secgroup_rule_webport80](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/networking_secgroup_rule_v2) | resource |
| [openstack_networking_secgroup_v2.the_secgroup](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/networking_secgroup_v2) | resource |
| [openstack_networking_subnet_v2.the_subnet](https://registry.terraform.io/providers/terraform-provider-openstack/openstack/latest/docs/resources/networking_subnet_v2) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_api_port"></a> [api\_port](#input\_api\_port) | Port to allow GitLab access K3S-cluster | `number` | `6443` | no |
| <a name="input_env_names"></a> [env\_names](#input\_env\_names) | Environments, one for staging and one for production | `set(string)` | <pre>[<br/>  "staging",<br/>  "production"<br/>]</pre> | no |
| <a name="input_external_network_id"></a> [external\_network\_id](#input\_external\_network\_id) | Public IP-ID (Public) | `string` | `"76879e07-c093-4a08-9664-c7aed800b723"` | no |
| <a name="input_identity_file"></a> [identity\_file](#input\_identity\_file) | n/a | `string` | `"Path to private key (.pem) used for SSH / Ansible, variable set in `terraform.tfvars`"` | no |
| <a name="input_image_name"></a> [image\_name](#input\_image\_name) | Image of choice | `string` | `"772b2dec-f649-4c57-bbc2-f3eaaad5f651"` | no |
| <a name="input_key_name"></a> [key\_name](#input\_key\_name) | n/a | `string` | `"Key-name on Cumulus, variable set in `terraform.tfvars`"` | no |
| <a name="input_pool_name"></a> [pool\_name](#input\_pool\_name) | Name of the floating IP pool | `string` | `"public"` | no |
| <a name="input_server_flavor"></a> [server\_flavor](#input\_server\_flavor) | Chosen machine resourse (we might want to downgrade) | `string` | `"c4-r4-d80"` | no |
| <a name="input_ssh_port"></a> [ssh\_port](#input\_ssh\_port) | ssh\_port | `number` | `22` | no |
| <a name="input_subnet_cidr"></a> [subnet\_cidr](#input\_subnet\_cidr) | The network range for the internal subnet | `string` | `"192.168.2.0/24"` | no |
| <a name="input_teammember_public_keys"></a> [teammember\_public\_keys](#input\_teammember\_public\_keys) | List of public SSH-keys for member access. | `list(string)` | `[]` | no |
| <a name="input_user"></a> [user](#input\_user) | Default cloud user | `string` | `"ubuntu"` | no |
| <a name="input_web_port"></a> [web\_port](#input\_web\_port) | Port to allow HTTP traffic | `number` | `80` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_cluster_ips"></a> [cluster\_ips](#output\_cluster\_ips) | 03-outputs.tf |
| <a name="output_ssh_commands"></a> [ssh\_commands](#output\_ssh\_commands) | n/a |

# Infra Setup
### Create a file named `terraform.tfvars` and add the following:
```MD  
#terraform.tfvars  
identity_file = "Path to private key (.pem) used for SSH / Ansible"  
key_name      = "Key-name on Cumulus" 
teammember_public_keys = [
    "ssh-ed25519 AAAA... teammember1@example.com",
    "ssh-ed25519 AAAA... teammember2@example.com",
]  
```
