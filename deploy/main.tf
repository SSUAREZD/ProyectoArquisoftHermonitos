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
# App Security Group (8080+SSH)
# Only ALB can hit 8080; SSH is open for testing
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
  name     = "arquisoft-tg"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id
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
  name_prefix   = "arquisoft-app-"
  image_id      = local.final_ami_id
  instance_type = "t3.medium"
  vpc_security_group_ids = [aws_security_group.app_sg.id]
  update_default_version = true

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
  name                = "arquisoft-asg"
  max_size            = 3
  min_size            = 1
  desired_capacity    = 1
  vpc_zone_identifier = data.aws_subnets.default_vpc_subnets.ids
  health_check_type   = "ELB"
  health_check_grace_period = 120

  target_group_arns = [aws_lb_target_group.app_tg.arn]

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
# Scale OUT: CPU > 80% for 5 minutes
############################
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "arquisoft-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Scale out if average CPU > 80% for 1 minute"
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.app_asg.name
  }
}

resource "aws_autoscaling_policy" "scale_out_one" {
  name                   = "arquisoft-scale-out-1"
  autoscaling_group_name = aws_autoscaling_group.app_asg.name
  adjustment_type        = "ChangeInCapacity"
  scaling_adjustment     = 1
  cooldown               = 180
}

resource "aws_cloudwatch_metric_alarm" "cpu_high_alarm_action" {
  alarm_name          = "arquisoft-cpu-high-action"
  comparison_operator = aws_cloudwatch_metric_alarm.cpu_high.comparison_operator
  evaluation_periods  = aws_cloudwatch_metric_alarm.cpu_high.evaluation_periods
  metric_name         = aws_cloudwatch_metric_alarm.cpu_high.metric_name
  namespace           = aws_cloudwatch_metric_alarm.cpu_high.namespace
  period              = aws_cloudwatch_metric_alarm.cpu_high.period
  statistic           = aws_cloudwatch_metric_alarm.cpu_high.statistic
  threshold           = aws_cloudwatch_metric_alarm.cpu_high.threshold
  dimensions          = aws_cloudwatch_metric_alarm.cpu_high.dimensions
  alarm_actions       = [aws_autoscaling_policy.scale_out_one.arn]
}

############################
# Scale IN: CPU < 30% for 5 minutes
############################
resource "aws_cloudwatch_metric_alarm" "cpu_low" {
  alarm_name          = "arquisoft-cpu-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 5
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Average"
  threshold           = 30
  alarm_description   = "Scale in if average CPU < 30% for 5 minutes"
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.app_asg.name
  }
}

resource "aws_autoscaling_policy" "scale_in_one" {
  name                   = "arquisoft-scale-in-1"
  autoscaling_group_name = aws_autoscaling_group.app_asg.name
  adjustment_type        = "ChangeInCapacity"
  scaling_adjustment     = -1
  cooldown               = 180
}

resource "aws_cloudwatch_metric_alarm" "cpu_low_alarm_action" {
  alarm_name          = "arquisoft-cpu-low-action"
  comparison_operator = aws_cloudwatch_metric_alarm.cpu_low.comparison_operator
  evaluation_periods  = aws_cloudwatch_metric_alarm.cpu_low.evaluation_periods
  metric_name         = aws_cloudwatch_metric_alarm.cpu_low.metric_name
  namespace           = aws_cloudwatch_metric_alarm.cpu_low.namespace
  period              = aws_cloudwatch_metric_alarm.cpu_low.period
  statistic           = aws_cloudwatch_metric_alarm.cpu_low.statistic
  threshold           = aws_cloudwatch_metric_alarm.cpu_low.threshold
  dimensions          = aws_cloudwatch_metric_alarm.cpu_low.dimensions
  alarm_actions       = [aws_autoscaling_policy.scale_in_one.arn]
}

output "alb_dns_name" {
  value = aws_lb.app_alb.dns_name
}

output "db_public_ip" {
  value = aws_instance.db_server.public_ip
}







