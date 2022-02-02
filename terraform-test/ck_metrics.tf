module "ck_metrics" {
  source = "../terraform"

  schedule_expression = "rate(30 minutes)"
}

# Note the periods below should match the rate in schedule_expression above

resource "aws_cloudwatch_metric_alarm" "debs_alarm" {
  alarm_name          = "Detached EBS Alarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "DetachedEBSMonthlyCost"
  dimensions = {
    Currency = "USD"
  }
  namespace          = "CloudKeep"
  period             = 1800
  statistic          = "Maximum"
  threshold          = "25"
  alarm_description  = "This alarm goes to alarm when the monthly cost of detached EBS volumes (that are measured in USD) exceeds $25"
  alarm_actions      = [aws_sns_topic.ops_alarms.arn]
  ok_actions         = [aws_sns_topic.ops_alarms.arn]
  treat_missing_data = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "ulbs_alarm" {
  alarm_name          = "Unused Load Balancer Alarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "UnusedLBMonthlyCost"
  dimensions = {
    Currency = "USD"
  }
  namespace          = "CloudKeep"
  period             = 1800
  statistic          = "Maximum"
  threshold          = "25"
  alarm_description  = "This alarm goes to alarm when the monthly cost of unused Load Balancers (that are measured in USD) exceeds $25"
  alarm_actions      = [aws_sns_topic.ops_alarms.arn]
  ok_actions         = [aws_sns_topic.ops_alarms.arn]
  treat_missing_data = "notBreaching"
}

resource "aws_sns_topic" "ops_alarms" {
  name = "ops-alarms-topic"
}

resource "aws_sns_topic_subscription" "ops_alarms" {
  topic_arn = aws_sns_topic.ops_alarms.arn
  protocol  = "email"
  endpoint  = "test@cloudkeep.io"
}
