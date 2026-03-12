terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_vpc" "lab04" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name    = "${var.project_name}-vpc"
    Project = var.project_name
    Lab     = "lab04"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.lab04.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = {
    Name    = "${var.project_name}-public-subnet"
    Project = var.project_name
    Lab     = "lab04"
  }
}

resource "aws_internet_gateway" "lab04" {
  vpc_id = aws_vpc.lab04.id

  tags = {
    Name    = "${var.project_name}-igw"
    Project = var.project_name
    Lab     = "lab04"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.lab04.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.lab04.id
  }

  tags = {
    Name    = "${var.project_name}-public-rt"
    Project = var.project_name
    Lab     = "lab04"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "vm" {
  name        = "${var.project_name}-sg"
  description = "Security group for Lab 04 VM"
  vpc_id      = aws_vpc.lab04.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_cidr_blocks
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "App port"
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

  tags = {
    Name    = "${var.project_name}-sg"
    Project = var.project_name
    Lab     = "lab04"
  }
}

resource "aws_key_pair" "lab04" {
  key_name   = var.key_pair_name
  public_key = file(pathexpand(var.ssh_public_key_path))

  tags = {
    Project = var.project_name
    Lab     = "lab04"
  }
}

resource "aws_instance" "vm" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.vm.id]
  key_name                    = aws_key_pair.lab04.key_name
  associate_public_ip_address = true

  tags = {
    Name    = "${var.project_name}-vm"
    Project = var.project_name
    Lab     = "lab04"
  }
}
