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
# Data Sources to Auto-Fetch VPC/Subnets (ONE copy)
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

locals {
  ec2_subnet_id  = element(data.aws_subnets.default_vpc_subnets.ids, 0)
  rds_subnet_ids = slice(data.aws_subnets.default_vpc_subnets.ids, 0, min(3, length(data.aws_subnets.default_vpc_subnets.ids)))
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

##############################
# SG: traffic to database host
##############################
resource "aws_security_group" "traffic_db" {
  name        = "traffic-db"
  description = "PostgreSQL EC2 access"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "PostgreSQL"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # tighten later to VPC/ALB/ASG ranges
  }

  ingress {
    description = "SSH (testing)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # tighten later
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "traffic_db_instance" }
}

############################
# ALB Security Group (80)
############################
resource "aws_security_group" "alb_sg" {
  name        = "asg-alb-sg"
  description = "Allow HTTP from internet to ALB"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "asg-alb-sg" }
}

############################
# App Inventario Security Group (8080 from ALB; SSH for debug)
############################
resource "aws_security_group" "app_sg" {
  name        = "asg-app-sg"
  description = "Allow 8080 from ALB, SSH for debug"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "App port from ALB"
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  ingress {
    description = "SSH (testing)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # tighten later
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "asg-app-sg" }
}
############################
# App Pedidos Security Group (8080 from ALB; SSH for debug)
############################

resource "aws_security_group" "traffic_manejador" {
  name        = "traffic_manejador"
  description = "Ingress 8090 only; allow all egress"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "App port manejador"
    from_port   = 8090
    to_port     = 8090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH (testing)"
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

############################
# EC2 running App Pedidos
############################

resource "aws_instance" "manejador" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.medium"
  subnet_id                   = local.ec2_subnet_id
  vpc_security_group_ids      = [aws_security_group.traffic_manejador.id]
  associate_public_ip_address = true

  tags = {
    Name = "traffic_manejador"
  }

  user_data = templatefile("${path.module}/manejador_user_data.sh.tpl", {
    repo_url    = "https://github.com/SSUAREZD/ProyectoArquisoftHermonitos.git"
    branch      = "manejador-pedidos"
    db_host     = aws_instance.db_server.private_ip
    db_name     = "db_proyect"
    db_user     = "Administrator"
    db_password = "Arquisoft2502"
    db_port     = 5432
    inventario_url = "http://${aws_instance.inventario.public_ip}:8080"
  })
}

############################
# EC2 running PostgreSQL 16
############################
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


############################
# ALB + Target Group + Listener
############################
resource "aws_lb" "app_alb" {
  name               = "arquisoft-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = data.aws_subnets.default_vpc_subnets.ids

  tags = { Name = "arquisoft-alb" }
}

resource "aws_lb_target_group" "app_tg" {
  name        = "arquisoft-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "instance"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 15
    timeout             = 5
    path                = "/health"
    matcher             = "200"
  }

  tags = { Name = "arquisoft-tg" }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }
}

############################
# Launch Template (Gunicorn app)
############################
resource "aws_launch_template" "app_lt" {
  name_prefix             = "arquisoft-app-"
  image_id                = data.aws_ami.ubuntu.id      # <-- fixed
  instance_type           = "t3.medium"
  vpc_security_group_ids  = [aws_security_group.app_sg.id]
  update_default_version  = true

  user_data = base64encode(templatefile("${path.module}/app_user_data.sh.tpl", {
    repo_url    = "https://github.com/SSUAREZD/ProyectoArquisoftHermonitos.git"
    branch      = "main"
    db_host     = aws_instance.db_server.private_ip
    db_name     = "db_proyect"
    db_user     = "Administrator"
    db_password = "Arquisoft2502"
    db_port     = 5432
  }))

  tag_specifications {
    resource_type = "instance"
    tags = { Name = "arquisoft-app" }
  }
}

############################
# Auto Scaling Group
############################
resource "aws_autoscaling_group" "app_asg" {
  name                       = "arquisoft-asg"
  max_size                   = 3
  min_size                   = 1
  desired_capacity           = 1
  vpc_zone_identifier        = data.aws_subnets.default_vpc_subnets.ids
  health_check_type          = "ELB"
  health_check_grace_period  = 120
  target_group_arns          = [aws_lb_target_group.app_tg.arn]

  launch_template {
    id      = aws_launch_template.app_lt.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "arquisoft-app"
    propagate_at_launch = true
  }
}

############################
# Scale OUT: CPU > 80% for ~1 minute
############################
resource "aws_autoscaling_policy" "scale_out_one" {
  name                   = "arquisoft-scale-out-1"
  autoscaling_group_name = aws_autoscaling_group.app_asg.name
  adjustment_type        = "ChangeInCapacity"
  scaling_adjustment     = 1
  cooldown               = 180
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "arquisoft-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Scale out if avg CPU > 80% for 1 min"
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.app_asg.name
  }
  alarm_actions = [aws_autoscaling_policy.scale_out_one.arn]
}

############################
# Scale IN: CPU < 30% for 5 minutes
############################
resource "aws_autoscaling_policy" "scale_in_one" {
  name                   = "arquisoft-scale-in-1"
  autoscaling_group_name = aws_autoscaling_group.app_asg.name
  adjustment_type        = "ChangeInCapacity"
  scaling_adjustment     = -1
  cooldown               = 180
}

resource "aws_cloudwatch_metric_alarm" "cpu_low" {
  alarm_name          = "arquisoft-cpu-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 5
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Average"
  threshold           = 30
  alarm_description   = "Scale in if avg CPU < 30% for 5 min"
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.app_asg.name
  }
  alarm_actions = [aws_autoscaling_policy.scale_in_one.arn]
}

############################
# Outputs
############################
output "alb_dns_name" {
  value = aws_lb.app_alb.dns_name
}

output "db_public_ip" {
  value = aws_instance.db_server.public_ip
}

output "manejador_public_ip" {
  value = aws_instance.manejador.public_ip
}