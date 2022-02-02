import os
import boto3
import json
import click
import asyncio
import importlib_metadata
import aws_clutter.clutter as clutter
import aws_clutter.tools as tools

NAMESPACE = os.getenv('CK_NAMESPACE', default='CloudKeep')


@click.group()
@click.version_option(version=importlib_metadata.version('aws_clutter'))
def cli():
    '''
    `awsclutter` finds and calculates the costs of unused resources ("clutter")
    in an AWS account across all regions

    Run `awsclutter` in an environment (i.e., shell) configured to run
    `aws` CLI.
    '''
    pass


@click.option('-s', '--summary', is_flag=True, default=False,
              help='Print just a summary')
@cli.command()
def list(summary):
    '''
    list the discovered clutter resources
    '''
    dvs = {}
    ulbs = {}
    asyncio.run(clutter.debs.query(dvs))
    asyncio.run(clutter.ulbs.query(ulbs))
    if (summary):
        clutter.debs.summarize(dvs)
        clutter.ulbs.summarize(ulbs)
    else:
        print(json.dumps(
            {
                'DetachedEBSVolumes': dvs,
                'UnusedLBs': ulbs
            },
            sort_keys=True, indent=4,
            cls=tools.DateTimeJSONEncoder
        ))


async def get_metric_data(metric_data):
    dvs = {}
    ulbs = {}
    await asyncio.gather(
        clutter.debs.query(dvs),
        clutter.ulbs.query(ulbs)
    )
    metric_data.extend(clutter.debs.aggregate(dvs))
    metric_data.extend(clutter.ulbs.aggregate(ulbs))
    return metric_data


@click.option('--dry-run', is_flag=True, default=False,
              help='Just print the custom metrics, do not push to CloudWatch')
@cli.command()
def watch(dry_run):
    '''
    calculate and push CloudWatch metrics based on clutter resources
    '''
    metric_data = []
    asyncio.run(get_metric_data(metric_data))

    if dry_run:
        print(json.dumps(
            metric_data, sort_keys=True, indent=4,
            cls=tools.DateTimeJSONEncoder
        ))

    else:
        # push metrics to CloudWatch
        if len(metric_data):
            client = boto3.client('cloudwatch')
            for i in range(0, len(metric_data), 20):
                client.put_metric_data(
                    Namespace=NAMESPACE,
                    MetricData=metric_data[i:i+20]
                )
