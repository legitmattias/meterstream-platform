#01-variables.tf
variable "env_names" {
  description = "Environments, one for staging and one for production"
  type        = set(string)
  default     = ["staging", "production"]
}

variable "key_name" {
  type    = string
  default = "Key-name on Cumulus, variable set in `terraform.tfvars`"
}

variable "identity_file" {
  type    = string
  default = "Path to private key (.pem) used for SSH / Ansible, variable set in `terraform.tfvars`"
}  

variable "image_name" {
  description = "Image of choice"  
  type    = string
  default = "772b2dec-f649-4c57-bbc2-f3eaaad5f651" 
}

variable "server_flavor" {
  description = "Chosen machine resourse (we might want to downgrade)"
  type    = string
  default = "c4-r4-d80" 
}

variable "external_network_id" {
  description = "Public IP-ID (Public)"  
  type    = string
  default = "76879e07-c093-4a08-9664-c7aed800b723" 
}

variable "pool_name" {
  description = "Name of the floating IP pool"
  type    = string
  default = "public"
}

variable "subnet_cidr" {
  description = "The network range for the internal subnet"
  type    = string
  default = "192.168.2.0/24"
}

variable "web_port" {
  description = "Port to allow HTTP traffic"
  type = number
  default = 80 
}

variable "api_port" {
  description = "Port to allow GitLab access K3S-cluster"
  type = number
  default = 6443
}

variable "ssh_port" { 
  description = "ssh_port"
  type = number
  default = 22
}

variable "user" {
  description = "Default cloud user"
  type = string
  default = "ubuntu"
}

variable "teammember_public_keys" {
  description = "List of public SSH-keys for member access."
  type        = list(string)
  default     = [] 
}

