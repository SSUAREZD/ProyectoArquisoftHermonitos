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
# Data Sources to Auto-Fetch VPC/Subnets
##############################
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default_vpc_subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Pick the first subnet for EC2 (any default subnet is public)
locals {
  ec2_subnet_id  = element(data.aws_subnets.default_vpc_subnets.ids, 0)
  rds_subnet_ids = slice(data.aws_subnets.default_vpc_subnets.ids, 0, min(3, length(data.aws_subnets.default_vpc_subnets.ids)))
}

##############################
# SG: trafico a base de datos
##############################
resource "aws_security_group" "traffic_db" {
  name        = "traffic-db"
  description = "Allow PostgreSQL access"
  vpc_id = data.aws_vpc.default.id

  ingress {
    description = "PostgreSQL access"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow SSH from anywhere (for testing)"
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

##############################
# SG: trafico a servicio
##############################

resource "aws_security_group" "traffic_inventario" {
  name        = "traffic_inventario"
  description = "Ingress 8080 only; allow all egress"
  vpc_id      = data.aws_vpc.default.id
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "App port"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
  description = "SSH"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"] # or replace with your IP only
}

  tags = { Name = "traffic_inventario" }
}

############################
# RDS subnet group
############################
resource "aws_db_subnet_group" "rds" {
  name       = "rds-subnets-auto"
  subnet_ids = local.rds_subnet_ids
  tags       = { Name = "rds-subnets-auto" }
}

############################
# RDS PostgreSQL (private)
############################
resource "aws_db_instance" "postgres" {
  identifier              = "arquisoft-postgres"
  engine                  = "postgres"
  engine_version          = "13.21"        
  instance_class          = "db.t3.micro" # Menos costo: "db.t4g.micro"
  allocated_storage       = 20
  db_name                 = "db_proyect"
  username                = "Administrator"
  password                = "Arquisoft2502"
  port                    = 5432

  db_subnet_group_name    = aws_db_subnet_group.rds.name
  vpc_security_group_ids  = [aws_security_group.traffic_db.id]

  multi_az                = false
  publicly_accessible     = false         
  storage_encrypted       = true
  skip_final_snapshot     = true

  backup_retention_period = 0
  deletion_protection     = false

  tags = { Name = "arquisoft-postgres" }
}

############################
# Ubuntu AMI (latest LTS)
############################
data "aws_ami" "ubuntu" {
  owners      = ["099720109477"] # Canonical
  most_recent = true
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

############################
# EC2 for the Django app
############################
resource "aws_instance" "inventario" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.medium"
  subnet_id                   = local.ec2_subnet_id
  vpc_security_group_ids      = [aws_security_group.traffic_inventario.id]
  associate_public_ip_address = true   # default subnet is public

  tags = {
    Name = "traffic_inventario"
  }

  user_data = templatefile("${path.module}/user_data.sh.tpl", {
    repo_url    = "https://github.com/SSUAREZD/ProyectoArquisoftHermonitos.git"
    rds_host    = aws_db_instance.postgres.address
    db_name     = "db_proyect"
    db_user     = "Administrator"
    db_password = "Arquisoft2502"
    db_port     = 5432
  })
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "app_public_ip" {
  value = aws_instance.inventario.public_ip
}




