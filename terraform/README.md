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

