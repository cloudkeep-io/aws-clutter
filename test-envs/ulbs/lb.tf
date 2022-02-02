#
# vpc and subnet info needed to create ELB's
# 
resource "aws_default_vpc" "default" {
}

resource "aws_default_subnet" "default_az1" {
  availability_zone = "us-east-1a"
}

resource "aws_default_subnet" "default_az2" {
  availability_zone = "us-east-1b"
}

#
# [0] completely empty (no listener) ALB and NLB
#
resource "aws_lb" "alb_0" {
  name               = "test-alb-0"
  internal           = false
  load_balancer_type = "application"
  subnets            = [aws_default_subnet.default_az1.id, aws_default_subnet.default_az2.id]
}


resource "aws_lb" "nlb_0" {
  name               = "test-nlb-0"
  internal           = false
  load_balancer_type = "network"
  subnets            = [aws_default_subnet.default_az1.id]
}

#
# [1] ALB attached to one listener with no target group
# (note NLB attached listeners need to have a target group)
#
resource "aws_lb" "alb_1" {
  name               = "test-alb-1"
  internal           = false
  load_balancer_type = "application"
  subnets            = [aws_default_subnet.default_az1.id, aws_default_subnet.default_az2.id]
}

resource "aws_lb_listener" "test_listener_1" {
  load_balancer_arn = aws_lb.alb_1.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Fixed response content"
      status_code  = "200"
    }
  }
}

#
# [2] target group that is not a listener's destination. (also no attachments)
#
resource "aws_lb_target_group" "tg_2" {
  name     = "lb-tg-2"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_default_vpc.default.id
}

#
# [3] ALB attached to one listener with one target group with no attachments
#
resource "aws_lb" "alb_3" {
  name               = "test-alb-3"
  internal           = false
  load_balancer_type = "application"
  subnets            = [aws_default_subnet.default_az1.id, aws_default_subnet.default_az2.id]
}

resource "aws_lb_listener" "test_listener_3" {
  load_balancer_arn = aws_lb.alb_3.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_3.arn
  }
}

resource "aws_lb_target_group" "tg_3" {
  name     = "lb-tg-3"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_default_vpc.default.id
}

#
# [4] NLB attached to one listener with one target group with no attachments
#
resource "aws_lb" "nlb_4" {
  name               = "test-nlb-4"
  internal           = false
  load_balancer_type = "network"
  subnets            = [aws_default_subnet.default_az1.id]
}


resource "aws_lb_listener" "test_listener_4" {
  load_balancer_arn = aws_lb.nlb_4.arn
  port              = 80
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_4.arn
  }
}

resource "aws_lb_target_group" "tg_4" {
  name     = "lb-tg-4"
  port     = 80
  protocol = "TCP"
  vpc_id   = aws_default_vpc.default.id
}

# ---- BELOW resources should not be picked up as unused ----
#
# [5] ALB attached to one listener with one target group attached to a (dummy) lambda function
#
resource "aws_lb" "alb_5" {
  name               = "test-alb-5"
  internal           = false
  load_balancer_type = "application"
  subnets            = [aws_default_subnet.default_az1.id, aws_default_subnet.default_az2.id]
}

resource "aws_lb_listener" "test_listener_5" {
  load_balancer_arn = aws_lb.alb_5.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_5.arn
  }
}

resource "aws_lb_target_group" "tg_5" {
  name        = "lb-tg-5"
  target_type = "lambda"
}

data "archive_file" "dummy" {
  type        = "zip"
  output_path = "${path.module}/lambda_function_payload.zip"
  source {
    content  = "dummy file"
    filename = "dummy.txt"
  }
}


resource "aws_iam_role" "lambda" {
  name = "test-lambda-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "lambda.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_lambda_function" "test_lambda_5" {
  filename      = data.archive_file.dummy.output_path
  function_name = "test-lambda-5"
  role          = aws_iam_role.lambda.arn
  handler       = "exports.test"
  runtime       = "nodejs14.x"
}

resource "aws_lambda_permission" "with_lb" {
  statement_id  = "AllowExecutionFromlb"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.test_lambda_5.arn
  principal     = "elasticloadbalancing.amazonaws.com"
  source_arn    = aws_lb_target_group.tg_5.arn
}

resource "aws_lb_target_group_attachment" "test_attachment_5" {
  target_group_arn = aws_lb_target_group.tg_5.arn
  target_id        = aws_lambda_function.test_lambda_5.arn
  depends_on       = [aws_lambda_permission.with_lb]
}
