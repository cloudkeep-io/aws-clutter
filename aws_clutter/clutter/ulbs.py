import boto3
import json
import asyncio
import concurrent.futures
import os
from importlib_resources import files
from aws_clutter.tools import boto3_paginate
from datetime import datetime
from collections import defaultdict

ELB_PRICING = json.loads(
    files('aws_clutter.data')
    .joinpath('elb_pricing.json')
    .read_text()
)
ULBS_DIMS_DEFAULT = os.getenv('ULBS_DIMS', default="RZCode")
HRS_IN_MONTH = 730


async def query(ulbs):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=30)
    loop = asyncio.get_event_loop()
    await asyncio.wait(
        [loop.run_in_executor(executor, list_ulbs_region, *(ulbs, region))
         for region in list_regions()]
    )


def summarize(ulbs):
    summary = {}
    for rz in ulbs.keys():
        if len(ulbs[rz]):
            rz_cost = sum(ulb["MonthlyCost"] for ulb in ulbs[rz])
            unit = ulbs[rz][0]["MonthlyCostUnit"]
            if not summary.get(unit):
                summary[unit] = {'cost': 0.0, 'count': 0, 'rzs': []}
            summary[unit]['cost'] += rz_cost
            summary[unit]['count'] += len(ulbs[rz])
            summary[unit]['rzs'].append(rz)
    units = summary.keys()
    if len(units) == 0:
        print("No Unused Load Balancers found.")
    else:
        for unit in units:
            print(f"Found {summary[unit]['count']} unused Load Balancers "
                  f"with monthly run cost of {summary[unit]['cost']} {unit} "
                  f"in regions: {summary[unit]['rzs']}")


def aggregate(ulbs):
    ulbs_dims = [d.strip() for d in ULBS_DIMS_DEFAULT.split(',')]
    timestamp = datetime.utcnow()
    metric_data = []
    ulbs_count = 0
    ulbs_cost = defaultdict(float)
    ulbs_count_rz = defaultdict(int)
    ulbs_cost_rz = defaultdict(lambda: defaultdict(float))
    ulbs_count_lbtype = defaultdict(int)
    ulbs_cost_lbtype = defaultdict(lambda: defaultdict(float))
    ulbs_count_rz_lbtype = defaultdict(lambda: defaultdict(int))
    ulbs_cost_rz_lbtype = defaultdict(
        lambda: defaultdict(lambda: defaultdict(float)))

    for rz in ulbs.keys():
        for lb in ulbs[rz]:
            cost_unit = lb['MonthlyCostUnit']
            cost = lb['MonthlyCost']
            lb_type = lb['Type']

            # update aggregations
            ulbs_count_rz_lbtype[rz][lb_type] += 1
            ulbs_cost_rz_lbtype[rz][lb_type][cost_unit] += cost
            ulbs_count_lbtype[lb_type] += 1
            ulbs_cost_lbtype[lb_type][cost_unit] += cost
            ulbs_count_rz[rz] += 1
            ulbs_cost_rz[rz][cost_unit] += cost
            ulbs_count += 1
            ulbs_cost[cost_unit] += cost

        # create regional aggregate metrics
        if 'RZCode' in ulbs_dims:
            if ulbs_count_rz[rz]:
                metric_data_add_ulbs_count(metric_data, timestamp,
                                           ulbs_count_rz[rz], rz=rz)
                metric_data_add_ulbs_cost(metric_data, timestamp,
                                          ulbs_cost_rz[rz], rz=rz)
            if 'LBType' in ulbs_dims:
                for lb_type, count in ulbs_count_rz_lbtype[rz].items():
                    metric_data_add_ulbs_count(metric_data, timestamp, count,
                                               rz=rz, lb_type=lb_type)
                    metric_data_add_ulbs_cost(metric_data, timestamp,
                                              ulbs_cost_rz_lbtype[rz][lb_type],
                                              rz=rz, lb_type=lb_type)

    # add the lb_type aggregate (cross-regional) metrics
    if 'LBType' in ulbs_dims:
        for lb_type, count in ulbs_count_lbtype.items():
            metric_data_add_ulbs_count(metric_data, timestamp, count,
                                       lb_type=lb_type)
            metric_data_add_ulbs_cost(metric_data, timestamp,
                                      ulbs_cost_lbtype[lb_type],
                                      lb_type=lb_type)

    # add the total aggregate data
    metric_data_add_ulbs_count(metric_data, timestamp, ulbs_count)
    metric_data_add_ulbs_cost(metric_data, timestamp, ulbs_cost)

    return metric_data


#
# Helper Functions for query()
#
def list_regions():
    client = boto3.client('ec2')
    aws_regions_info = client.describe_regions()
    return [region['RegionName'] for region in
            aws_regions_info.get('Regions', [])]


def list_ulbs_region(ulbs, region):
    client = boto3.client('elbv2', region_name=region)
    lbs = [response for response in boto3_paginate(
        client.describe_load_balancers
    )]
    tgs = [response for response in boto3_paginate(
        client.describe_target_groups
    )]
    tg_healths = {}
    ulbs[region] = [enrich_lb_info(lb, client.meta.region_name)
                    for lb in lbs if lb_unused(lb, tgs, tg_healths, client)]


def lb_unused(lb, tgs, tg_healths, client):
    lb_ths = [tg_health(tg, tg_healths, client) for tg in tgs
              if lb['LoadBalancerArn'] in tg['LoadBalancerArns']]
    for th in lb_ths:
        if len(th['TargetHealthDescriptions']):
            return False
    return True


def tg_health(tg, tg_healths, client):
    tg_arn = tg['TargetGroupArn']
    r = tg_healths.get(tg_arn)
    if r is None:
        r = client.describe_target_health(TargetGroupArn=tg_arn)
        tg_healths[tg_arn] = r
    return r


def enrich_lb_info(lb, region):
    lb['RZCode'] = region
    (currency, monthly_cost) = get_lb_base_cost(lb, region)
    lb['MonthlyCost'] = monthly_cost
    lb['MonthlyCostUnit'] = currency
    return lb


def get_lb_base_cost(lb, region):
    elb_type = lb['Type']
    location_type = 'region'
    for z in lb['AvailabilityZones']:
        if z.get('OutpostId'):
            location_type = 'outpost'
            break

    base_pricing = (ELB_PRICING[region][elb_type]
                               [location_type]['LoadBalancerUsage'])
    pricing = base_pricing['pricePerUnit']
    units = pricing.keys()
    for unit in units:
        monthly_cost = float(pricing[unit]) * HRS_IN_MONTH
        return (unit, monthly_cost)


#
# Helper Functions for aggregate()
#
def metric_data_add_ulbs_count(metric_data, timestamp, count,
                               rz=None, lb_type=None):
    dims = []
    if rz:
        dims.append({
            'Name': 'RZCode',
            'Value': rz
        })
    if lb_type:
        dims.append({
            'Name': 'LoadBalancerType',
            'Value': lb_type
        })
    metric_data.append({
        'MetricName': 'UnusedLBCount',
        'Dimensions': dims,
        'Timestamp': timestamp,
        'Unit': 'None',
        'Value': count
    })


def metric_data_add_ulbs_cost(metric_data, timestamp, unit_cost_dict,
                              rz=None, lb_type=None):
    for unit, cost in unit_cost_dict.items():
        metric_data_add_ulbs_unit_cost(metric_data, timestamp, unit, cost,
                                       rz=rz, lb_type=lb_type)


def metric_data_add_ulbs_unit_cost(metric_data, timestamp, cost_unit, cost,
                                   rz=None, lb_type=None):
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
    if lb_type:
        dims.append({
            'Name': 'LoadBalancerType',
            'Value': lb_type
        })
    metric_data.append({
        'MetricName': 'UnusedLBMonthlyCost',
        'Dimensions': dims,
        'Timestamp': timestamp,
        'Unit': 'None',
        'Value': cost
    })
