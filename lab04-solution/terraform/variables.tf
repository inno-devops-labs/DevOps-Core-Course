variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "lab04"
}

variable "instance_type" {
  description = "EC2 instance type (t2.micro for free tier)"
  type        = string
  default     = "t2.micro"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "ssh_public_key_path" {
  description = "Path to your SSH public key (~/.ssh/id_rsa.pub)"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "ssh_allowed_cidr" {
  description = "CIDR block allowed for SSH access (restrict to your IP)"
  type        = string
  default     = "0.0.0.0/0" # WARNING: Change to your IP for security (e.g., "1.2.3.4/32")
}

variable "user_data_script" {
  description = "User data script to run on instance startup"
  type        = string
  default     = <<-EOF
#!/bin/bash
set -ex

# Update system
apt-get update
apt-get upgrade -y

# Install basic tools
apt-get install -y \
  curl \
  wget \
  git \
  vim \
  htop \
  net-tools

# Install Docker (optional, for Lab 5 preparation)
apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Install Python and Ansible (for Lab 5 preparation)
apt-get install -y python3 python3-pip ansible

echo "✅ Instance setup complete"
EOF
}
