import pytest
import math
import aws_clutter.clutter.debs as debs


# Expected costs are gotten from https://calculator.aws/#/createCalculator/EBS
# which calcualtes to the closest penny - thus we use rel_tol of 0.01 below
@pytest.mark.parametrize("test_data", [
    {
        'vol': {
            'VolumeType': 'gp2',
            'Size': 100
        },
        'rzCode': 'us-west-1',
        'expectedMonthlyCostUnit': 'USD',
        'expectedMonthlyCost': 12.00
    },
    {
        'vol': {
            'VolumeType': 'gp3',
            'Size': 800,
            'Iops': 4000,
            'Throughput': 250
        },
        'rzCode': 'us-west-1',
        'expectedMonthlyCostUnit': 'USD',
        'expectedMonthlyCost': 88.80
    },
    {
        'vol': {
            'VolumeType': 'io1',
            'Size': 800,
            'Iops': 200
        },
        'rzCode': 'us-west-1',
        'expectedMonthlyCostUnit': 'USD',
        'expectedMonthlyCost': 124.80
    },
    {
        'vol': {
            'VolumeType': 'io2',
            'Size': 160,
            'Iops': 80000
        },
        'rzCode': 'us-east-2',
        'expectedMonthlyCostUnit': 'USD',
        'expectedMonthlyCost': 4065.60
    },
    {
        'vol': {
            'VolumeType': 'st1',
            'Size': 125
        },
        'rzCode': 'us-west-1',
        'expectedMonthlyCostUnit': 'USD',
        'expectedMonthlyCost': 6.75
    },
    {
        'vol': {
            'VolumeType': 'sc1',
            'Size': 125
        },
        'rzCode': 'us-west-1',
        'expectedMonthlyCostUnit': 'USD',
        'expectedMonthlyCost': 2.25
    },
    {
        'vol': {
            'VolumeType': 'standard',
            'Size': 100
        },
        'rzCode': 'us-west-1',
        'expectedMonthlyCostUnit': 'USD',
        'expectedMonthlyCost': 8.00
    }
])
def test_enrich_vol_info(test_data):
    vol = test_data['vol']
    debs.enrich_vol_info(vol, test_data['rzCode'])
    assert(vol['RZCode'] == test_data['rzCode'])
    assert(vol['MonthlyCostUnit'] == test_data['expectedMonthlyCostUnit'])
    assert(math.isclose(vol['MonthlyCost'], test_data['expectedMonthlyCost'],
                        rel_tol=0.001))
