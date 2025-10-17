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

##############################
# Security Group
##############################
resource "aws_security_group" "traffic_db" {
  name        = "traffic-db"
  description = "Allow PostgreSQL access"

  ingress {
    description = "PostgreSQL access"
    from_port   = 5432
    to_port     = 5432
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
# Launch Template
##############################
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_launch_template" "db_template" {
  name_prefix   = "db-launch-"
  image_id      = data.aws_ami.ubuntu.id
  instance_type = "t3.medium"

  vpc_security_group_ids = [aws_security_group.traffic_db.id]

  user_data = base64encode(<<-EOF
              #!/bin/bash
              sudo apt-get update -y
              sudo apt-get install -y postgresql postgresql-contrib

              sudo -u postgres psql -c "CREATE USER monitoring_user WITH PASSWORD 'isis2503';"
              sudo -u postgres createdb -O monitoring_user monitoring_db

              echo "host all all 0.0.0.0/0 trust" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
              echo "listen_addresses='*'" | sudo tee -a /etc/postgresql/16/main/postgresql.conf
              echo "max_connections=2000" | sudo tee -a /etc/postgresql/16/main/postgresql.conf

              sudo systemctl restart postgresql

              sudo -u postgres psql -d monitoring_db -c "CREATE TABLE Users (username TEXT, password TEXT);"

              for i in $(seq 1 2000); do
                sudo -u postgres psql -d monitoring_db -c "INSERT INTO Users (username, password) VALUES ('$i', '$i');"
              done
              EOF
  )
}

##############################
# Auto Scaling Group
##############################
resource "aws_autoscaling_group" "db_asg" {
  name                      = "db-asg"
  max_size                 = 2
  min_size                 = 1
  desired_capacity         = 1
  vpc_zone_identifier      = data.aws_subnets.default_vpc_subnets.ids
  health_check_type        = "EC2"
  health_check_grace_period = 300

  launch_template {
    id      = aws_launch_template.db_template.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "db-instance"
    propagate_at_launch = true
  }
}

resource "aws_autoscaling_policy" "cpu_scale_up" {
  name                   = "scale-up-policy"
  autoscaling_group_name = aws_autoscaling_group.db_asg.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }

    target_value = 80.0
  }
}

##############################
# Load Balancer (TCP - NLB)
##############################
resource "aws_lb" "db_nlb" {
  name               = "db-nlb"
  load_balancer_type = "network"
  subnets            = data.aws_subnets.default_vpc_subnets.ids
}

resource "aws_lb_target_group" "db_tg" {
  name        = "db-target-group"
  port        = 5432
  protocol    = "TCP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "instance"
}

resource "aws_lb_listener" "db_listener" {
  load_balancer_arn = aws_lb.db_nlb.arn
  port              = 5432
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.db_tg.arn
  }
}

resource "aws_autoscaling_attachment" "asg_to_tg" {
  autoscaling_group_name = aws_autoscaling_group.db_asg.name
  alb_target_group_arn   = aws_lb_target_group.db_tg.arn
}