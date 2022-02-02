# AWS Clutter Meter Terraform module

Terraform module for adding a CloudWatch metric to monitor "clutter" in the AWS account. See [aws-clutter](https://github.com/cloudkeep-io/aws-clutter) for more details.

## Features
* Deploys a containerized version of [aws-clutter](https://github.com/cloudkeep-io/aws-clutter) as a Lambda function.
* Lambda function is triggered by CloudWatch Events. (Default every 10 minute.)

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | -------- |
| image_tag | Docker image tag to use | String | latest | no |
| schedule_expression | How often to run the Lambda function that generates the clutter metrics. See [this doc](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html) for expression syntax. | String | rate(10 minutes) | no |
| DEBS_DIMS | Comma separated list of dimensions to be added to the DetachedEBSCount and DetachedEBSMonthlyCost metrics. E.g., 'RZCode,VolumeType' | String | RZCode | no |

## Usage Examples

### Minimal Example

```
module "ck_metrics" {
  source = "github.com/cloudkeep-io/aws-clutter//terraform"

  schedule_expression = "rate(60 minutes)" 
}
```

### Example with an Alarm that notifies an Email via SNS
```
module "ck_metrics" {
  source = "github.com/cloudkeep-io/aws-clutter//terraform"

  schedule_expression = "rate(60 minutes)" 
}

# Note the period below should match the rate in schedule_expression above

resource "aws_cloudwatch_metric_alarm" "debs_alarm" {
  alarm_name          = "Detached EBS Alarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "DetachedEBSMonthlyCost"
  dimensions = {
    Currency = "USD"
  }
  namespace          = "CloudKeep"
  period             = 3600
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
  period             = 3600
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
  endpoint  = "ops-team@acme.com"
}
```
