# AWS Clutter

Python package that reports on "AWS clutter" as CloudWatch custom metrics.

## Getting Started
If you're familiar with Terraform, see the [README](./terraform/README.md) under `terraform` directory. This is a Terraform module that installs this Python code as a Lambda function that will get triggered on a schedule (by default every 10 minutes.) Once deployed, look under the namespace CloudKeep in CloudWatch for the various custom metrics. More details on these metrics below.

Alternatively, you can use the command line tool, `awsclutter`. You can use this to generate a report on "AWS clutter". You can also use it to push the custom metrics to CloudWatch. By combining it with a scheduler of your choice (e.g., `cron`), you can use it to push to CloudWatch on a schedule. See documentation on `awsclutter` CLI below.

## Features
* Cost-Aware. Where relevant, `awsclutter` calculates how much the clutter is costing you.
* Cross-Region. A common challenge for AWS users is the lack of *cross-region* visibility (for many types of resources). `awsclutter` scans across every region that's accessible to your AWS account so that it can uncover clutter in regions that are rarely visited.
* Fast.  `awsclutter` uses asynchronous programming to run queries in parallel. This makes it very fast/efficient in retrieving the underlying data from AWS.

## "Clutter" Resources and Custom Metrics

### Detached (Orphaned) EBS Volumes

Detached EBS (Elastic Block Storage) volumes constitue one of the most common sources of AWS cost that creeps up over time. When an EC2 instance is instantiated and extra storage is desired, it is easy to add an EBS volume. At the time of instantiation, there is an option to "Delete on Termination" (of the EC2 instance). The default is "No".

Thus, it's common that these detached volumes exist in a given AWS environment. The problem is two-fold:
* Not all organizations have a process in place where AWS users (who can create EC2 instances) will actually delete these volumes when they no longer need it.
* These detached volumes do not stand out in the AWS console where an admin might do something about them.

`awsclutter` addresses the second problem.

`awsclutter` allows an AWS admin to keep track of these detached EBS volumes by creating the following CloudWatch custom metrics:
* `DetachedEBSCount` - number of detached EBS volumes
* `DetachedEBSCost` - monthly cost of detached EBS volumes

These custom metrics are created under the name space of `CloudKeep` and have the following dimensions:
* `COST_UNIT` (only for `DetachedEBSCost`) - required - currency for the EBS cost, as per the AWS pricing metric. Currently, this is 'CNY' for China regions and 'USD' for everywhere else.
* `RZ_CODE` - optional (default: On) - Region/Zone Code. E.g., `us-east-1`.
* `VOL_TYPE` - optional (default: Off) - Volume Type. E.g., `gp3`.
* `VOL_ID` - optional (default: Off) - Volume ID.

### Unused Security Groups (Coming soon!)

## `awsclutter` CLI
This section WIP.

### Installation
This section WIP.

