#01-variables.tf
variable "env_names" {
  description = "Environments, one for staging and one for production"
  type        = set(string)
  default     = ["staging", "production"]
}

variable "key_name" {
  type    = string
  default = "Please export an environment variable TF_VAR_key_name with the name of the public key on your Cumulus"
}

variable "identity_file" {
  type    = string
  default = "Please export an environment variable TF_VAR_identity_file with the path to your key for ansible machine (path of the .pem file)."
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

variable "teammate_public_keys" {
  description = "List of public SSH-keys for member access."
  type        = list(string)
  default     = ["Key1, key2, key3"] 
}

