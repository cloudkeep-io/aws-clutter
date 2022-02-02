variable "region1" {
  type = string
  default = "us-west-1"
}

variable "region2" {
  type = string
  default = "us-east-2"
}

provider "aws" {
  region = var.region1
}

provider "aws" {
  alias  = "region2"
  region = var.region2
}
