import pendulum
import json
import datetime


def boto3_paginate(method, **kwargs):
    '''
    utility function - use like this:
    s3 = session.client('s3')
    for key in boto3_paginate(s3.list_objects_v2, Bucket='my-bucket'):
        print(key)
    '''
    client = method.__self__
    paginator = client.get_paginator(method.__name__)
    for page in paginator.paginate(**kwargs).result_key_iters():
        for result in page:
            yield result


# Serialize datetime in UTC
class DateTimeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            dt = pendulum.instance(obj).in_tz('UTC')
            return dt.to_iso8601_string()
        else:
            return super(DateTimeJSONEncoder, self).default(obj)
