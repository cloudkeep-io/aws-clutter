import os
import sys
import boto3
import json
import click
import asyncio
import importlib_metadata
import aws_clutter.clutter as clutter
import aws_clutter.tools as tools

NAMESPACE = os.getenv('CK_NAMESPACE', default='CloudKeep')
CLUTTER_TYPES = ['debs', 'ulbs']


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


@click.argument('clutter_type', nargs=-1)
@click.option('-s', '--summary', is_flag=True, default=False,
              help='Print just a summary')
@cli.command()
def list(clutter_type, summary):
    '''
    list the discovered clutter resources
    '''
    for ct in clutter_type:
        if ct not in CLUTTER_TYPES:
            print(f"Unknown clutter type {ct}")
            sys.exit(1)

    dvs = {}
    ulbs = {}
    result = {}
    if len(clutter_type) == 0:
        clutter_type = CLUTTER_TYPES

    if 'debs' in clutter_type:
        asyncio.run(clutter.debs.query(dvs))
        result['debs'] = {
            'description': 'Detached EBS Volumes',
            'resources': dvs
        }
    if 'ulbs' in clutter_type:
        asyncio.run(clutter.ulbs.query(ulbs))
        result['ulbs'] = {
            'description': 'Unused Load Balancers',
            'resources': ulbs
        }

    if (summary):
        if 'debs' in clutter_type:
            clutter.debs.summarize(dvs)
        if 'ulbs' in clutter_type:
            clutter.ulbs.summarize(ulbs)
    else:
        print(json.dumps(result, sort_keys=True, indent=4,
                         cls=tools.DateTimeJSONEncoder))


async def get_metric_data(clutter_type, metric_data):
    dvs = {}
    ulbs = {}
    queries = []
    if 'debs' in clutter_type:
        queries.append(clutter.debs.query(dvs))
    if 'ulbs' in clutter_type:
        queries.append(clutter.ulbs.query(ulbs))
    await asyncio.gather(*queries)
    if 'debs' in clutter_type:
        metric_data.extend(clutter.debs.aggregate(dvs))
    if 'ulbs' in clutter_type:
        metric_data.extend(clutter.ulbs.aggregate(ulbs))
    return metric_data


@click.argument('clutter_type', nargs=-1)
@click.option('--dry-run', is_flag=True, default=False,
              help='Just print the custom metrics, do not push to CloudWatch')
@cli.command()
def watch(clutter_type, dry_run):
    '''
    calculate and push CloudWatch metrics based on clutter resources
    '''
    metric_data = []
    asyncio.run(get_metric_data(clutter_type, metric_data))

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
