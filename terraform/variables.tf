variable "image_tag" {
  type        = string
  description = "Docker image tag to use"
  default     = "latest"
}

variable "schedule_expression" {
  type        = string
  description = "How often to run the Lambda function that generates the clutter metrics. See https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html for expression syntax."
  default     = "rate(10 minutes)"
}

variable "DEBS_DIMS" {
  type        = string
  description = "Comma separated list of dimensions to be added to the DetachedEBSCount and DetachedEBSMonthlyCost metrics. E.g., 'RZCode,VolumeType'"
  default     = "RZCode"
}

