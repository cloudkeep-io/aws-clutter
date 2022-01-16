# info from: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volume-types.html

# gp2
# size: 1 GiB - 16 TiB
resource "aws_ebs_volume" "gp2_0" {
  count             = 1
  availability_zone = "${var.region1}a"
  type              = "gp2"
  size              = 1
}
# us-west-1 monthly cost: $0.12


# gp3
# size: 1 GiB - 16 TiB
# iops: 3,000 - 16,000
# throughput: 125 - 1,000
# Iops to volume size ratio maximum is 500
resource "aws_ebs_volume" "gp3_0" {
  count             = 1
  availability_zone = "${var.region1}a"
  type              = "gp3"
  size              = 6
}
# us-west-1 monthly cost: $0.576

resource "aws_ebs_volume" "gp3_1" {
  count             = 1
  availability_zone = "${var.region1}a"
  type              = "gp3"
  size              = 8
  iops              = 4000
  throughput        = 250
}
# us-west-1 monthly cost: $12.768


# io1
# size: 4 GiB - 16 TiB
# iops: 100 to 64,000
resource "aws_ebs_volume" "io1_0" {
  count             = 1
  availability_zone = "${var.region1}a"
  type              = "io1"
  size              = 4
  iops              = 100
}
# us-west-1 monthly cost: $7.752

resource "aws_ebs_volume" "io1_1" {
  count             = 1
  availability_zone = "${var.region1}a"
  type              = "io1"
  size              = 8
  iops              = 200
}
# us-west-1 monthly cost: $15.504


# io2
# size: 4 GiB - 16 TiB
# iops: 100 to 256,000
# deploy this in second region - there's a default maximum of 100000 IOPS per region (aggregate)
resource "aws_ebs_volume" "io2_0" {
  provider          = aws.region2
  count             = 1
  availability_zone = "${var.region2}a"
  type              = "io2"
  size              = 160
  iops              = 80000
}
# us-east-2 monthly cost: $4065.60


# st1
# size: 125 GiB - 16 TiB
resource "aws_ebs_volume" "st1_0" {
  count             = 1
  availability_zone = "${var.region1}a"
  type              = "st1"
  size              = 125
}
# us-west-1 monthly cost: $6.75


# sc1
# size: 125 GiB - 16 TiB
resource "aws_ebs_volume" "sc1_0" {
  count             = 1
  availability_zone = "${var.region1}a"
  type              = "sc1"
  size              = 125
}
# us-west-1 monthly cost: $2.25


# standard
# size: 1 GiB - 1 TiB
resource "aws_ebs_volume" "standard_0" {
  count             = 1
  availability_zone = "${var.region1}a"
  type              = "standard"
  size              = 1
}
# us-west-1 monthly cost: $0.08
