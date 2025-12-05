terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.19.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

##############################
# VPC + SUBNET DISCOVERY
##############################
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default_vpc_subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name   = "availability-zone"
    values = ["us-east-1a","us-east-1b","us-east-1c","us-east-1f"]
  }
}

locals {
  ec2_subnet_id = element(data.aws_subnets.default_vpc_subnets.ids, 0)
}

##############################
# UBUNTU AMI
##############################
data "aws_ami" "ubuntu" {
  owners      = ["099720109477"] # Canonical
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

##############################
# SECURITY GROUPS
##############################

# PostgreSQL server SG
resource "aws_security_group" "traffic_db" {
  name        = "traffic-db"
  description = "Access to PostgreSQL host"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "PostgreSQL"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
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

  tags = { Name = "traffic_db_instance" }
}

# Django App SG (exposes port 80) -> manejador de INVENTARIO
resource "aws_security_group" "app_sg" {
  name        = "arquisoft-app-sg"
  description = "Allow HTTP and SSH"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
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

  tags = { Name = "arquisoft_app_sg" }
}

# Traffic manejador SG -> manejador de PEDIDOS
resource "aws_security_group" "traffic_manejador" {
  name        = "traffic_manejador"
  description = "Allow port 8090 and SSH"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "Manejador app port"
    from_port   = 8090
    to_port     = 8090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
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

  tags = { Name = "traffic_manejador" }
}

##############################
# EC2 INSTANCES
##############################

# PostgreSQL INSTANCE
resource "aws_instance" "db_server" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.micro"
  subnet_id                   = local.ec2_subnet_id
  vpc_security_group_ids      = [aws_security_group.traffic_db.id]
  associate_public_ip_address = true

  tags = { Name = "traffic_db_server" }

  user_data = templatefile("${path.module}/db_user_data.sh.tpl", {
    vpc_cidr    = data.aws_vpc.default.cidr_block
    db_name     = "db_proyect"
    db_user     = "Administrator"
    db_password = "Arquisoft2502"
  })
}

# INVENTARIO: Django + Gunicorn + Nginx (branch sprint4-manejador-inventario)
resource "aws_instance" "app_server" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.medium"
  subnet_id                   = local.ec2_subnet_id
  vpc_security_group_ids      = [aws_security_group.app_sg.id]
  associate_public_ip_address = true

  tags = {
    Name = "arquisoft_inventario"
  }

  user_data = templatefile("${path.module}/app_user_data.sh.tpl", {
    repo_url    = "https://github.com/SSUAREZD/ProyectoArquisoftHermonitos.git"
    branch      = "sprint4-manejador-inventario"
    db_host     = aws_instance.db_server.private_ip
    db_name     = "db_proyect"
    db_user     = "Administrator"
    db_password = "Arquisoft2502"
    db_port     = 5432
  })
}

# PEDIDOS: manejador-pedidos Django (branch sprint4-manejador-pedidos)
resource "aws_instance" "manejador" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.medium"
  subnet_id                   = local.ec2_subnet_id
  vpc_security_group_ids      = [aws_security_group.traffic_manejador.id]
  associate_public_ip_address = true

  tags = {
    Name = "traffic_manejador_pedidos"
  }

  user_data = templatefile("${path.module}/manejador_user_data.sh.tpl", {
    repo_url      = "https://github.com/SSUAREZD/ProyectoArquisoftHermonitos.git"
    branch        = "sprint4-manejador-pedidos"
    db_host       = aws_instance.db_server.private_ip
    db_name       = "db_proyect"
    db_user       = "Administrator"
    db_password   = "Arquisoft2502"
    db_port       = 5432
    # usar IP PRIVADA para consumo interno en la VPC
    inventario_url = "http://${aws_instance.app_server.private_ip}"
  })
}

##############################
# OUTPUTS
##############################
output "db_public_ip" {
  value = aws_instance.db_server.public_ip
}

output "app_public_ip" {
  value = aws_instance.app_server.public_ip
}

output "manejador_public_ip" {
  value = aws_instance.manejador.public_ip
}
