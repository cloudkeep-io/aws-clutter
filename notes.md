response = cloudwatch.put_metric_data(
    MetricData = [
        {
            'MetricName': 'DetachedEBSMonthlyCost',
            'Dimensions': [
                {
                    'Name': 'SRC_RZ_CODE',
                    'Value': 'us-east-1'
                }
            ],
            'Unit': 'USD',
            'Value': value
				},
        {
            'MetricName': 'DetachedEBSMonthlyCost',
            'Dimensions': [
                {
                    'Name': 'SRC_RZ_CODE',
                    'Value': 'us-east-2'
                }
            ],
            'Unit': 'USD',
            'Value': value
        },
    ],
    Namespace='CloudKeep/CostMonitor'
)
