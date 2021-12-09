import boto3
import json
import click
import asyncio
import concurrent.futures
from importlib_resources import files
from .tools import boto3_paginate, DateTimeJSONEncoder
from importlib_metadata import version
from datetime import datetime
from collections import defaultdict

EBS_PRICING = json.loads(
    files('aws_clutter.data')
    .joinpath('ebs_pricing.json')
    .read_text()
)

PRICE_MAP = {price['rzCode']: price['ebs_prices'] for price in EBS_PRICING}


@click.group()
@click.version_option(version=version('aws_clutter'))
def cli():
    '''
    Detached EBS Cost Monitor command line interface
    '''
    pass


@cli.command()
@click.option('-s', '--summary', is_flag=True, default=False,
              help='Print just a summary')
def list(summary):
    dvs = {}
    asyncio.run(list_dvs(dvs))
    if (summary):
        print_summary(dvs)
    else:
        print(json.dumps(
            dvs, sort_keys=True, indent=4, cls=DateTimeJSONEncoder
        ))


@cli.command()
def watch():
    sample_and_post()


def lambda_handler(event, context):
    if False:
        print(event)
        print(context)

    sample_and_post()


def sample_and_post():
    timestamp = datetime.utcnow()

    dvs = {}
    asyncio.run(list_dvs(dvs))

    metric_data = []
    total_count = 0
    total_cost = defaultdict(float)
    for rz in dvs.keys():
        # create granular metrics
        for dv in dvs[rz]:
            metric_data.append({
                'MetricName': 'DetachedEBSVolCost',
                'Dimensions': [
                    {
                        'Name': 'RZ_CODE',
                        'Value': rz
                    },
                    {
                        'Name': 'COST_UNIT',
                        'Value': dv["MonthlyCostUnit"]
                    },
                    {
                        'Name': 'VOL_ID',
                        'Value': dv['VolumeId']
                    },
                    {
                        'Name': 'VOL_TYPE',
                        'Value': dv['VolumeType']
                    }
                ],
                'Timestamp': timestamp,
                'Unit': 'None',
                'Value': dv['MonthlyCost']
            })

        # create regional aggregate metrics
        if len(dvs[rz]):
            rz_count = len(dvs[rz])
            rz_cost = sum(v['MonthlyCost'] for v in dvs[rz])
            unit = dvs[rz][0]['MonthlyCostUnit']
            total_count += rz_count
            total_cost[unit] += rz_cost
            metric_data.append({
                'MetricName': 'DetachedEBSCount',
                'Dimensions': [
                    {
                        'Name': 'RZ_CODE',
                        'Value': rz
                    }
                ],
                'Timestamp': timestamp,
                'Unit': 'Count',
                'Value': rz_count
            })
            metric_data.append({
                'MetricName': 'DetachedEBSMonthlyCost',
                'Dimensions': [
                    {
                        'Name': 'RZ_CODE',
                        'Value': rz
                    },
                    {
                        'Name': 'COST_UNIT',
                        'Value': unit
                    }
                ],
                'Timestamp': timestamp,
                'Unit': 'None',
                'Value': rz_cost
            })

    # add the total aggregate data
    metric_data.append({
        'MetricName': 'DetachedEBSCount',
        'Timestamp': timestamp,
        'Unit': 'Count',
        'Value': rz_count
    })
    for unit, cost in total_cost.items():
        metric_data.append({
            'MetricName': 'DetachedEBSMonthlyCost',
            'Dimensions': [
                {
                    'Name': 'COST_UNIT',
                    'Value': unit
                }
            ],
            'Timestamp': timestamp,
            'Unit': 'None',
            'Value': cost
        })

    if len(metric_data):
        client = boto3.client('cloudwatch')
        for i in range(0, len(metric_data), 20):
            client.put_metric_data(
                Namespace='CloudKeep',
                MetricData=metric_data[i:i+20]
            )


def print_summary(dvs):
    summary = {}
    for rz in dvs.keys():
        if len(dvs[rz]):
            rz_cost = sum(v["MonthlyCost"] for v in dvs[rz])
            unit = dvs[rz][0]["MonthlyCostUnit"]
            if not summary.get(unit):
                summary[unit] = {'cost': 0.0, 'count': 0, 'rzs': []}
            summary[unit]['cost'] += rz_cost
            summary[unit]['count'] += len(dvs[rz])
            summary[unit]['rzs'].append(rz)
    units = summary.keys()
    if len(units) == 0:
        print("No Detached EBS Volumes found.")
    else:
        for unit in units:
            print(f"Found {summary[unit]['count']} detached EBS volumes "
                  f"with monthly run cost of {summary[unit]['cost']} {unit} "
                  f"in regions: {summary[unit]['rzs']}")


async def list_dvs(dvs):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=30)
    loop = asyncio.get_event_loop()
    await asyncio.wait(
        [loop.run_in_executor(executor, list_dvs_region, *(dvs, region))
         for region in list_regions()]
    )


def list_dvs_region(dvs, region):
    client = boto3.client('ec2', region_name=region)
    volumes = [response for response in boto3_paginate(
        client.describe_volumes,
        Filters=[
            {
                'Name': 'status',
                'Values': ['available']
            }
        ]
    )]
    dvs[region] = [enrich_vol_info(v, client.meta.region_name)
                   for v in volumes if len(v["Attachments"]) == 0]


def enrich_vol_info(volume, region):
    volume['RZCode'] = region
    try:
        pricing = PRICE_MAP[region][volume['VolumeType']]
        unit, cost = {
            'gp2': get_cost_basic,
            'gp3': get_cost_gp3,
            'io1': get_cost_io1,
            'io2': get_cost_io2,
            'st1': get_cost_basic,
            'sc1': get_cost_basic,
            'standard': get_cost_standard
        }[volume['VolumeType']](volume, pricing)
        volume['MonthlyCost'] = cost
        volume['MonthlyCostUnit'] = unit
    except KeyError as e:
        print("Internal Error: Please report the following to "
              "support@cloudkeep.io")
        print(f"- Failed to calculate monthly cost for {volume['VolumeId']}.")
        print(f"- KeyError: {e}")
        print("- volume info:")
        print(json.dumps(volume, cls=DateTimeJSONEncoder))
    return volume


def get_cost_basic(volume, pricing):
    units = pricing['pricePerGBMonth'].keys()
    for unit in units:
        cost = float(pricing['pricePerGBMonth'][unit]) * int(volume['Size'])
        return (unit, cost)


def get_cost_gp3(volume, pricing):
    unit, cost = get_cost_basic(volume, pricing)

    # add IOPS cost
    if int(volume['Iops']) > 3000:
        cost += (float(pricing['pricePerIOPSMonth'][unit]) *
                 (int(volume['Iops']) - 3000))

    # add Throughput cost
    if int(volume['Throughput']) > 125:
        cost += (float(pricing['pricePerGiBpsMonth'][unit]) *
                 (int(volume['Throughput']) - 125)/1000)

    return (unit, cost)


def get_cost_io1(volume, pricing):
    unit, cost = get_cost_basic(volume, pricing)

    # add IOPS cost
    cost += float(pricing['pricePerIOPSMonth'][unit]) * int(volume['Iops'])
    return (unit, cost)


def get_cost_io2(volume, pricing):
    unit, cost = get_cost_basic(volume, pricing)

    # add Tier 3 IOPS cost
    if int(volume['Iops']) > 64000:
        cost += (float(pricing['pricePerT3IOPSMonth'][unit]) *
                 (int(volume['Iops']) - 64000))

    # add Tier 2 IOPS cost
    if int(volume['Iops']) > 32000:
        cost += (float(pricing['pricePerT2IOPSMonth'][unit]) *
                 max((int(volume['Iops']) - 32000), 32000))

    # add Tier 1 IOPS cost
    cost += (float(pricing['pricePerT1IOPSMonth'][unit]) *
             max(int(volume['Iops']), 32000))

    return (unit, cost)


def get_cost_standard(volume, pricing):
    unit, cost = get_cost_basic(volume, pricing)

    # add IOPS cost - should be zero for detached volumes

    return (unit, cost)


def list_regions():
    client = boto3.client('ec2')
    aws_regions_info = client.describe_regions()
    return [region['RegionName'] for region in
            aws_regions_info.get('Regions', [])]
