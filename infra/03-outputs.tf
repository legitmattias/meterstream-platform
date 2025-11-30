#03-outputs.tf
output "cluster_ips" {
  value = {
    for env in var.env_names : env => openstack_networking_floatingip_v2.the_floatip[env].address
  }
}

output "ssh_commands" {
  value = [
    for env in var.env_names : "ssh -i ${var.identity_file} ${var.user}@${openstack_networking_floatingip_v2.the_floatip[env].address}"
  ]
}