# AWS Clutter

Python package that reports on "AWS clutter" and how much they cost. Can report via CloudWatch custom metrics.

## Features
* Cost-Aware. Where relevant, `awsclutter` calculates how much the clutter is costing you.
* Cross-Region. A common challenge for AWS users is the lack of *cross-region* visibility (for many types of resources). `awsclutter` scans across every region that's accessible to your AWS account so that it can uncover clutter in regions that are rarely visited.
* Fast.  `awsclutter` uses asynchronous programming to run queries concurrently. This makes it very fast/efficient in retrieving the underlying data from AWS.

## Getting Started
To install:
```
pip install aws-clutter
```
This installs a command line tool, `awsclutter`. You can use this to generate a report on "AWS clutter". 

Sample Commands:
```
# summary list of all the clutter resources:
awsclutter list --summary

# detailed list of debs (detached EBS):
awsclutter list debs 

# using jq to get a resource type description (here, for resource type 'debs'):
awsclutter list debs | jq '.debs.description`

# using jq to identify the properties (attributes) of 'debs' resource type:
awsclutter list debs | jq '.debs.resources."us-east-1"[0] | keys'

# to push cloudwatch metrics:
awsclutter watch

# to see what the cloudwatch metrics look like (without actually pushing them):
awsclutter watch --dry-run

# using jq to compactly print the custom metrics and their dimensions:
awsclutter watch --dry-run | jq -r '.[] | .MetricName + "[" + ( [.Dimensions[].Name] | join(",")) + "]"' | sort
```

## Installing as Lambda
If you're familiar with Terraform, see the [README](https://github.com/cloudkeep-io/aws-clutter/blob/main/terraform/README.md) under `terraform` directory. This is a Terraform module that installs this Python code as a Lambda function that will get triggered on a schedule (by default every 10 minutes.) The Lambda function calls the `awsclutter watch` method. Once deployed, look under the namespace CloudKeep in CloudWatch for the various custom metrics. More details on these metrics below.


## Clutter Type "debs" - Detached (Orphaned) EBS Volumes

Detached EBS (Elastic Block Storage) volumes constitue one of the most common sources of AWS cost that creeps up over time. When an EC2 instance is instantiated and extra storage is desired, it is easy to add an EBS volume. At the time of instantiation, there is an option to "Delete on Termination" (of the EC2 instance). The default is "No".

Thus, it's common that these detached volumes exist in a given AWS environment. The problem is two-fold:
* Not all organizations have a process in place where AWS users (who can create EC2 instances) will actually delete these volumes when they no longer need it.
* These detached volumes do not stand out in the AWS console where an admin might do something about them.

`awsclutter` allows an AWS admin to keep track of these detached EBS volumes by creating the following CloudWatch custom metrics:
* `DetachedEBSCount` - number of detached EBS volumes
* `DetachedEBSMonthlyCost` - monthly cost of detached EBS volumes

These custom metrics are created under the name space of `CloudKeep` and can have the following dimensions:
* `Currency` (only for `DetachedEBSMonthlyCost`) - required - currency for the EBS cost, as per the AWS pricing metric. Currently, this is 'CNY' for China regions and 'USD' for everywhere else.
* `RZCode` - Region/Zone Code. E.g., `us-east-1`.
* `VolumeType` - Volume Type. E.g., `gp3`.
* `VolumeId` - Volume ID. Note the dimensions `RZCode` and `VolumeType` are always added to the metric with `VolumeId` in it.

A metric without a certain dimension represents a summation over the missing dimension. For example, `DetachedEBSCount` without any dimensions is the total number of all the Detached EBS Volumes (across all the regions and volume types). `DetachedEBSCount[RZCode]` represents the total number of detached EBS volumes in the specified `RZCode`.

By default, custom metrics with the dimension of `RZCode` is added. You can specify additional dimensions to be surfaced via an environment variable `DEBS_DIMS`, by setting it to a list of dimensions, separated by a comma. E.g., `"RZCode,VolumeType"`.


## Clutter Type "ulbs" - Unused Load Balancers

Unused load balancers can come about when the servers and/or Lambda functions that backend the load balancer are removed. Note even if a load balancer is not being used at all, it incurs a charge.

The custom metrics created are:
* `UnusedLBCount` - number of unused Load Balancers
* `UnusedLBMonthlyCost` - monthly cost of unused Load Balancers

And these metrics can have the following dimensions
* `Currency` (only for `UnusedLBMonthlyCost`) - required - currency for the LB cost, as per the AWS pricing metric. For ELBs, these are all 'USD'.
* `RZCode` - Region/Zone Code. E.g., `us-east-1`.
* `LBType` - Load Balancer Type. ('application', 'network', 'gateway') - Note "Classic" is not supported.


## See Also
There is mature open source project called [Cloud Custodian](https://github.com/cloud-custodian/cloud-custodian) which includes some of aws-clutter's functionalities as use cases.

