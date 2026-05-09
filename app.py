from detached_ebs_cost_monitor import cli


def handler(event, context):
    print(event)
    print(context)

    cli.sample_and_post()

    return {}
