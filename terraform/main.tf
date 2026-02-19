terraform {
  required_providers {
    aws = {
      source  = "hc-registry.website.k2.cloud/c2devel/rockitcloud"
      version = "~> 25.2"
    }
  }
}


provider "aws" {
  region                      = var.region
  access_key                  = var.access_key
  secret_key                  = var.secret_key
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    ec2 = var.ec2_url
    iam = var.iam_url
  }
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
  tags       = { Name = "lab04-vpc" }
}

# Subnet
resource "aws_subnet" "subnet" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnet_cidr
  availability_zone = var.az
  tags              = { Name = "lab04-subnet" }
}

# Internet Gateway + Route
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "lab04-igw" }
}

resource "aws_route_table" "rt" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = { Name = "lab04-rt" }
}

resource "aws_route_table_association" "rta" {
  subnet_id      = aws_subnet.subnet.id
  route_table_id = aws_route_table.rt.id
}

# Security Group
resource "aws_security_group" "ext" {
  name        = "lab04-ext"
  description = "Allow SSH/HTTP/custom"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "lab04-ext-sg" }
}

resource "aws_security_group" "int" {
  name   = "lab04-int"
  vpc_id = aws_vpc.main.id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "lab04-int-sg" }
}

# Key pair resource
data "aws_key_pair" "labkey" {
  key_name   = var.pubkey_name
}

# Elastic IP
resource "aws_eip" "web_eip" {
  vpc        = true
  depends_on = [aws_internet_gateway.igw]
  tags       = { Name = "lab04-eip" }
}

# EC2 Instance
resource "aws_instance" "vm" {
  ami                    = var.vm_template
  instance_type          = var.vm_instance_type
  subnet_id              = aws_subnet.subnet.id
  vpc_security_group_ids = [aws_security_group.ext.id, aws_security_group.int.id]
  key_name               = data.aws_key_pair.labkey.key_name

  root_block_device {
    volume_size           = var.vm_volume_size
    volume_type           = "gp2"
    delete_on_termination = true
  }

  tags = { Name = "lab04-vm" }
}

# Associate EIP with instance
resource "aws_eip_association" "assoc" {
  instance_id   = aws_instance.vm.id
  allocation_id = aws_eip.web_eip.id
}
