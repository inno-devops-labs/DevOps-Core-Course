terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  required_version = ">= 1.4.0"
}

provider "aws" {
  region = "eu-north-1"
}

variable "ssh_key_name" {
  description = "Name of the AWS EC2 Key Pair"
  type        = string
}

resource "aws_instance" "vm" {
  ami                    = "ami-0974a2c5ddf10f442"
  instance_type          = "t3.micro"
  key_name               = var.ssh_key_name
  associate_public_ip_address = true

  vpc_security_group_ids = [aws_security_group.ssh.id]

  tags = {
    Name = "ubuntu-vm"
  }
}

resource "aws_security_group" "ssh" {
  name_prefix = "ubuntu-ssh-"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

output "public_ip" {
  value = aws_instance.vm.public_ip
}
