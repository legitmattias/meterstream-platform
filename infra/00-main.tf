#00-main.tf
resource "openstack_networking_network_v2" "the_network" {
  name           = "group_project_network"
  admin_state_up = true
}

resource "openstack_networking_subnet_v2" "the_subnet" {
  network_id = openstack_networking_network_v2.the_network.id
  cidr       = var.subnet_cidr
}

resource "openstack_networking_router_v2" "the_router" {
  name                = "group_router"
  admin_state_up      = true
  external_network_id = var.external_network_name
}

resource "openstack_networking_router_interface_v2" "router_interface_1" {
  router_id = openstack_networking_router_v2.the_router.id
  subnet_id = openstack_networking_subnet_v2.the_subnet.id
}

resource "openstack_networking_secgroup_v2" "the_secgroup" {
  name        = "sec_group_web"
}

resource "openstack_networking_secgroup_rule_v2" "secgroup_rule_webport22" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = var.ssh_port
  port_range_max    = var.ssh_port
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.the_secgroup.id
}

resource "openstack_networking_secgroup_rule_v2" "secgroup_rule_webport80" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = var.web_port
  port_range_max    = var.web_port
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = openstack_networking_secgroup_v2.the_secgroup.id
}


resource "openstack_networking_port_v2" "port_1" {
  for_each       = var.env_names 

  name           = "port_${each.key}"
  network_id     = openstack_networking_network_v2.the_network.id
  admin_state_up = true
  security_group_ids = [openstack_networking_secgroup_v2.the_secgroup.id]
  depends_on         = [openstack_networking_subnet_v2.the_subnet]
}

resource "openstack_compute_instance_v2" "the_server" {
  for_each    = var.env_names
  name        = "server-${each.key}"
  image_id    = var.image_name
  flavor_name = var.server_flavor
  key_pair    = var.key_name

  network {
    port = openstack_networking_port_v2.port_1[each.key].id
  }
  ## Copy team member keys into machine
  user_data = <<-EOF
    #!/bin/bash
    echo "Adding teammate keys..."
    %{ for key in var.teammate_public_keys ~}
    echo "${key}" >> /home/ubuntu/.ssh/authorized_keys
    %{ endfor ~}
    chown ubuntu:ubuntu /home/ubuntu/.ssh/authorized_keys
  EOF
}

resource "openstack_networking_floatingip_v2" "the_floatip" {
  for_each = var.env_names 
  pool     = var.pool_name
}

resource "openstack_networking_floatingip_associate_v2" "fip_1" {
  for_each    = var.env_names

  floating_ip = openstack_networking_floatingip_v2.the_floatip[each.key].address
  port_id     = openstack_networking_port_v2.port_1[each.key].id
}