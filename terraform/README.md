# AWS Clutter Meter Terraform module

Terraform module for adding a CloudWatch metric to monitor "clutter" in the AWS account. See [aws-clutter-meter](https://github.com/cloudkeep-io/aws-clutter-meter) for more details.

## Features
* Deploys a containerized version of [aws-clutter-meter](https://github.com/cloudkeep-io/aws-clutter-meter) as a Lambda function.
* Lambda function is triggered by CloudWatch Events. (Default every 10 minute.)

## Usage Example
```
module "ck_metrics" {
  source = "github.com/cloudkeep-io/aws-clutter-meter//terraform"

  schedule_expression = "rate(60 minutes)" 
}
```

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | -------- |
| image_tag | Docker image tag to use | String | latest | no |
| schedule_expression | How often to run the Lambda function that generates the clutter metrics. See [this doc](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html) for expression syntax. | String | rate(10 minutes) | no |

