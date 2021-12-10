import os
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
DEBS_DIMS_DEFAULT = os.getenv('DEBS_DIMS', default="RZCode")
NAMESPACE = os.getenv('CK_NAMESPACE', default='CloudKeep')


@click.group()
@click.version_option(version=version('aws_clutter'))
def cli():
    '''
    Detached EBS Cost Monitor command line interface
    '''
    pass


@click.option('-s', '--summary', is_flag=True, default=False,
              help='Print just a summary')
@cli.command()
def list(summary):
    dvs = {}
    asyncio.run(list_dvs(dvs))
    if (summary):
        print_summary(dvs)
    else:
        print(json.dumps(
            dvs, sort_keys=True, indent=4, cls=DateTimeJSONEncoder
        ))


@click.option('--dims', is_flag=False, default=DEBS_DIMS_DEFAULT,
              show_default=True, metavar='<dim1>,<dim2>,...',
              type=click.STRING,
              help=('Sets dimensions of CloudWatch metrics for detached '
                    'EBS volumes'))
@click.option('--dry-run', is_flag=True, default=False,
              help='Just print the custom metrics, do not push to CloudWatch')
@cli.command()
def watch(dims, dry_run):
    debs_dims = [d.strip() for d in dims.split(',')]
    sample_and_post(debs_dims, dry_run)


def lambda_handler(event, context):
    if False:
        print(event)
        print(context)

    debs_dims = [d.strip() for d in DEBS_DIMS_DEFAULT.split(',')]
    sample_and_post(debs_dims)


def metric_data_add_debs_count(metric_data, timestamp, count,
                               rz=None, vol_type=None, vol_id=None):
    dims = []
    if rz:
        dims.append({
            'Name': 'RZCode',
            'Value': rz
        })
    if vol_type:
        dims.append({
            'Name': 'VolumeType',
            'Value': vol_type
        })
    if vol_id:
        dims.append({
            'Name': 'VolumeId',
            'Value': vol_id
        })
    metric_data.append({
        'MetricName': 'DetachedEBSCount',
        'Dimensions': dims,
        'Timestamp': timestamp,
        'Unit': 'None',
        'Value': count
    })


def metric_data_add_debs_unit_cost(metric_data, timestamp, cost_unit, cost,
                                   rz=None, vol_type=None, vol_id=None):
    dims = [
        {
            'Name': 'Currency',
            'Value': cost_unit
        }
    ]
    if rz:
        dims.append({
            'Name': 'RZCode',
            'Value': rz
        })
    if vol_type:
        dims.append({
            'Name': 'VolumeType',
            'Value': vol_type
        })
    if vol_id:
        dims.append({
            'Name': 'VolumeId',
            'Value': vol_id
        })
    metric_data.append({
        'MetricName': 'DetachedEBSMonthlyCost',
        'Dimensions': dims,
        'Timestamp': timestamp,
        'Unit': 'None',
        'Value': cost
    })


def metric_data_add_debs_cost(metric_data, timestamp, unit_cost_dict,
                              rz=None, vol_type=None, vol_id=None):
    for unit, cost in unit_cost_dict.items():
        metric_data_add_debs_unit_cost(metric_data, timestamp, unit, cost,
                                       rz=rz, vol_type=vol_type, vol_id=vol_id)


def get_metric_data(dvs, debs_dims):
    timestamp = datetime.utcnow()
    metric_data = []
    debs_count = 0
    debs_cost = defaultdict(float)
    debs_count_rz = defaultdict(int)
    debs_cost_rz = defaultdict(lambda: defaultdict(float))
    debs_count_vtype = defaultdict(int)
    debs_cost_vtype = defaultdict(lambda: defaultdict(float))
    debs_count_rz_vtype = defaultdict(lambda: defaultdict(int))
    debs_cost_rz_vtype = defaultdict(
        lambda: defaultdict(lambda: defaultdict(float)))

    for rz in dvs.keys():
        for dv in dvs[rz]:
            cost_unit = dv['MonthlyCostUnit']
            cost = dv['MonthlyCost']
            vol_type = dv['VolumeType']
            vol_id = dv['VolumeId']

            # create the most granular metrics
            if 'VolumeId' in debs_dims:
                metric_data_add_debs_unit_cost(metric_data, timestamp,
                                               cost_unit, cost, rz=rz,
                                               vol_type=vol_type,
                                               vol_id=vol_id)

            # update aggregations
            debs_count_rz_vtype[rz][vol_type] += 1
            debs_cost_rz_vtype[rz][vol_type][cost_unit] += cost
            debs_count_vtype[vol_type] += 1
            debs_cost_vtype[vol_type][cost_unit] += cost
            debs_count_rz[rz] += 1
            debs_cost_rz[rz][cost_unit] += cost
            debs_count += 1
            debs_cost[cost_unit] += cost

        # create regional aggregate metrics
        if 'RZCode' in debs_dims:
            if debs_count_rz[rz]:
                metric_data_add_debs_count(metric_data, timestamp,
                                           debs_count_rz[rz], rz=rz)
                metric_data_add_debs_cost(metric_data, timestamp,
                                          debs_cost_rz[rz], rz=rz)
            if 'VolumeType' in debs_dims:
                for vol_type, count in debs_count_rz_vtype[rz].items():
                    metric_data_add_debs_count(metric_data, timestamp, count,
                                               rz=rz, vol_type=vol_type)
                    metric_data_add_debs_cost(metric_data, timestamp,
                                              debs_cost_rz_vtype[rz][vol_type],
                                              rz=rz, vol_type=vol_type)

    # add the vol_type aggregate (cross-regional) metrics
    if 'VolumeType' in debs_dims:
        for vol_type, count in debs_count_vtype.items():
            metric_data_add_debs_count(metric_data, timestamp, count,
                                       vol_type=vol_type)
            metric_data_add_debs_cost(metric_data, timestamp,
                                      debs_cost_vtype[vol_type],
                                      vol_type=vol_type)

    # add the total aggregate data
    metric_data_add_debs_count(metric_data, timestamp, debs_count)
    metric_data_add_debs_cost(metric_data, timestamp, debs_cost)

    return metric_data


def sample_and_post(debs_dims, dry_run=False):
    dvs = {}
    asyncio.run(list_dvs(dvs))

    metric_data = get_metric_data(dvs, debs_dims)

    if dry_run:
        print(json.dumps(
            metric_data, sort_keys=True, indent=4, cls=DateTimeJSONEncoder
        ))
        return

    # push metrics to CloudWatch
    if len(metric_data):
        client = boto3.client('cloudwatch')
        for i in range(0, len(metric_data), 20):
            client.put_metric_data(
                Namespace=NAMESPACE,
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
