resource "aws_security_group" "devops_lab4_sg" {
  name = "devops-lab4-sg"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
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

resource "aws_instance" "devops-lab4" {
  ami = "ami-0b6c6ebed2801a5cb"

  tags = {
    Name = "DevOpsLab4"
  }
  
  instance_type = "t2.micro"
  key_name = "vockey"
  vpc_security_group_ids = [aws_security_group.devops_lab4_sg.id]
  
  root_block_device {
    volume_size = 16
  }
}
