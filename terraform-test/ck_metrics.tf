module "ck_metrics" {
  source = "../terraform"

  schedule_expression = "rate(3 minutes)" 
}
