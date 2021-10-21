from aws_clutter_meter import cli


def handler(event, context):
    print(event)
    print(context)

    cli.sample_and_post()

    return {}
