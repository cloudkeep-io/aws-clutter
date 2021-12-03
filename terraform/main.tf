locals {
  repository_name     = "cloudkeep/aws-clutter-meter"
  function_name       = "aws-clutter-meter"
  ecr_repository_name = local.repository_name
}

provider "aws" {}
provider "docker" {}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "docker_registry_image" "lambda" {
  name = "${local.repository_name}:${var.image_tag}"
}

resource "aws_ecr_repository" "repo" {
  name = local.ecr_repository_name
}

resource "null_resource" "ecr_image" {
  triggers = {
    registry_image = data.docker_registry_image.lambda.sha256_digest
  }

  provisioner "local-exec" {
    command = <<EOF
           docker pull ${local.repository_name}:${var.image_tag}
           aws ecr get-login-password --region ${data.aws_region.current.id} | \
             docker login --username AWS --password-stdin ${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.id}.amazonaws.com
           docker tag ${local.repository_name}:${var.image_tag} ${aws_ecr_repository.repo.repository_url}:${var.image_tag}
           docker push ${aws_ecr_repository.repo.repository_url}:${var.image_tag}
       EOF
  }
}

data "aws_ecr_image" "lambda_image" {
  depends_on = [
    null_resource.ecr_image
  ]
  repository_name = local.ecr_repository_name
  image_tag       = var.image_tag
}

resource "aws_iam_role" "lambda" {
  name               = "${local.function_name}-role"
  assume_role_policy = <<EOF
{
   "Version": "2012-10-17",
   "Statement": [
       {
           "Action": "sts:AssumeRole",
           "Principal": {
               "Service": "lambda.amazonaws.com"
           },
           "Effect": "Allow"
       }
   ]
}
 EOF
}

data "aws_iam_policy_document" "lambda" {
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "cloudwatch:PutMetricData"
    ]
    effect    = "Allow"
    resources = ["*"]
  }

  statement {
    actions = [
      "ec2:DescribeRegions",
      "ec2:DescribeVolumes"
    ]
    effect    = "Allow"
    resources = ["*"]
  }
}

resource "aws_iam_policy" "lambda" {
  name   = "${local.function_name}-policy"
  path   = "/"
  policy = data.aws_iam_policy_document.lambda.json
}

resource "aws_iam_role_policy_attachment" "lambda" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.lambda.arn
}

resource "aws_lambda_function" "lambda" {
  depends_on = [
    null_resource.ecr_image
  ]
  function_name = local.function_name
  role          = aws_iam_role.lambda.arn
  timeout       = 300
  image_uri     = "${aws_ecr_repository.repo.repository_url}@${data.aws_ecr_image.lambda_image.id}"
  package_type  = "Image"
}

resource "aws_cloudwatch_event_rule" "sched" {
  name                = "ck_trigger"
  description         = "triggers the lambda function that generates CloudKeep metrics"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "sched_target" {
  rule      = aws_cloudwatch_event_rule.sched.name
  target_id = "lambda"
  arn       = aws_lambda_function.lambda.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.sched.arn
}

