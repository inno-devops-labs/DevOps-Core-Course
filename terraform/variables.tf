variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "machine_type" {
  description = "Machine type (e2-micro for free tier)"
  type        = string
  default     = "e2-micro"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
}
