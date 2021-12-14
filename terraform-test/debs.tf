

resource "aws_ebs_volume" "io1_0" {
  count             = 0
  availability_zone = "us-east-1a"
  type              = "io1"
  size              = 100
  iops              = 100
}

