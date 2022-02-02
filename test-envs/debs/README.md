# Test Environment 1

WARNING - This creates an environment with over $4,000 in monthly spend!

(Since the EBS volumes are charged per minute, and the test runs less than a minute, this should cost less than $1 to run. But if for some reason the environment is not brought down, there can be a large bill - beaware!)

See ebs.tf for all the EBS volumes it creates. These are created in us-west-1 and us-east-2.

See Makefile for tests. Basically creates the EBS volumes via terraform, run awsclutter and check to see if the results are as expected, then take down the environment.

