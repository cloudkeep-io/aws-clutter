module "ck_metrics" {
  source = "../terraform"

  schedule_expression = "rate(3 minutes)"
}

resource "aws_cloudwatch_metric_alarm" "debs_alarm" {
  alarm_name          = "Detached EBS Alarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "DetachedEBSMonthlyCost"
  dimensions = {
    Currency = "USD"
  }
  namespace          = "CloudKeep"
  period             = 60
  statistic          = "Maximum"
  threshold          = "25"
  alarm_description  = "This alarm goes to alarm when the monthly cost of detached EBS volumes (that are measured in USD) exceeds $25"
  alarm_actions      = [aws_sns_topic.ops_alarms.arn]
  ok_actions         = [aws_sns_topic.ops_alarms.arn]
  treat_missing_data = "ignore"
}

resource "aws_sns_topic" "ops_alarms" {
  name = "ops-alarms-topic"
}

resource "aws_sns_topic_subscription" "ops_alarms" {
  topic_arn = aws_sns_topic.ops_alarms.arn
  protocol  = "email"
  endpoint  = "test@cloudkeep.io"
}
