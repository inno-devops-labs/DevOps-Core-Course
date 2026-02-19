terraform {
  required_version = ">= 1.9"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_vpc" "lab04" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.project_name}-vpc"
    Project     = var.project_name
    Environment = "lab"
    ManagedBy   = "terraform"
  }
}

resource "aws_internet_gateway" "lab04" {
  vpc_id = aws_vpc.lab04.id

  tags = {
    Name        = "${var.project_name}-igw"
    Project     = var.project_name
    Environment = "lab"
    ManagedBy   = "terraform"
  }
}

resource "aws_subnet" "lab04" {
  vpc_id                  = aws_vpc.lab04.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.region}a"
  map_public_ip_on_launch = false

  tags = {
    Name        = "${var.project_name}-subnet"
    Project     = var.project_name
    Environment = "lab"
    ManagedBy   = "terraform"
  }
}

resource "aws_route_table" "lab04" {
  vpc_id = aws_vpc.lab04.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.lab04.id
  }

  tags = {
    Name        = "${var.project_name}-rt"
    Project     = var.project_name
    Environment = "lab"
    ManagedBy   = "terraform"
  }
}

resource "aws_route_table_association" "lab04" {
  subnet_id      = aws_subnet.lab04.id
  route_table_id = aws_route_table.lab04.id
}

resource "aws_security_group" "lab04" {
  name        = "${var.project_name}-sg"
  description = "Security group for Lab 04 VM"
  vpc_id      = aws_vpc.lab04.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
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
    Name        = "${var.project_name}-sg"
    Project     = var.project_name
    Environment = "lab"
    ManagedBy   = "terraform"
  }
}

resource "aws_key_pair" "lab04" {
  key_name   = var.project_name
  public_key = var.ssh_public_key

  tags = {
    Name        = "${var.project_name}-key"
    Project     = var.project_name
    Environment = "lab"
    ManagedBy   = "terraform"
  }
}

resource "aws_instance" "lab04" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.lab04.id
  vpc_security_group_ids = [aws_security_group.lab04.id]
  key_name               = aws_key_pair.lab04.key_name

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    delete_on_termination = true
  }

  tags = {
    Name        = "${var.project_name}-vm"
    Project     = var.project_name
    Environment = "lab"
    ManagedBy   = "terraform"
  }
}

resource "aws_eip" "lab04" {
  instance = aws_instance.lab04.id
  domain   = "vpc"

  tags = {
    Name        = "${var.project_name}-eip"
    Project     = var.project_name
    Environment = "lab"
    ManagedBy   = "terraform"
  }
}
