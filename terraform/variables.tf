variable "access_key" {
  description = "K2 Cloud access key (API)"
}

variable "secret_key" {
  description = "K2 Cloud secret key (API)"
}

variable "region" {
  description = "K2 Cloud region (e.g. ru-msk)"
}

variable "ec2_url" {
  description = "EC2 endpoint URL (override)"
}

variable "s3_url" {
  description = "S3 URL (override)"
}

variable "elb_url" {
  description = "ELB URL (override)"
}

variable "iam_url" {
  description = "IAM URL (override)"
}

variable "auto_scaling_url" {
  description = "Autoscaling URL (override)"
}

variable "aws_cloudwatch_url" {
  description = "CloudWatch URL (override)"
}

variable "pubkey_name" {
  description = "Name for the SSH key in K2 (e.g. mylab-key)"
}

variable "vpc_cidr" {
  description = "VPC CIDR (e.g. 172.16.20.0/24)"
}

variable "subnet_cidr" {
  description = "Subnet CIDR inside VPC (e.g. 172.16.20.0/24)"
}

variable "az" {
  description = "Availability zone"
}

variable "vm_template" {
  description = "Image/template ID to use for VM (e.g. cmi-21D1D81D)"
}

variable "vm_instance_type" {
  description = "Instance type to create (e.g. m5gl20.small)"
}

variable "vm_volume_size" {
  description = "Volume size in GiB"
}

variable "ssh_cidr" {
  description = "CIDR from which SSH is allowed (YOUR_IP/32 recommended)"
}
