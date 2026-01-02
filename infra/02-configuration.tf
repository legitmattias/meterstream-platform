#02-configuration.tf
resource "null_resource" "wait_ssh" {
  for_each = var.env_names
  connection {
    type        = "ssh"
    user        = var.user
    private_key = file(var.identity_file)
    host        = openstack_networking_floatingip_v2.the_floatip[each.key].address
  }
  provisioner "remote-exec" {
    inline = ["echo 'Connection successful to ${each.key} server'"]
  }
  triggers = { always_run = timestamp() }
  depends_on = [
    openstack_networking_floatingip_associate_v2.fip_1
  ]
}