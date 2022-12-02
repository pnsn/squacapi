from drf_yasg import openapi
'''
    Param overrides for doc generator (won't be needed in V3)
    Needed for fields that have list of values allowed
'''

metric_param = openapi.Parameter(
    'metric', openapi.IN_QUERY,
    description="Comma separated list of metric ids",
    type=openapi.TYPE_ARRAY,
    items=openapi.Items(type=openapi.TYPE_INTEGER),
    collection_format='multi')

channel_param = openapi.Parameter(
    'channel', openapi.IN_QUERY,
    description="Comma separated list of channel ids",
    type=openapi.TYPE_ARRAY,
    items=openapi.Items(type=openapi.TYPE_INTEGER),
    collection_format='multi')

nslc_param = openapi.Parameter(
    'nslc', openapi.IN_QUERY,
    description="Comma separated list of channel nslcs",
    type=openapi.TYPE_ARRAY,
    items=openapi.Items(type=openapi.TYPE_STRING),
    collection_format='multi')

group_param = openapi.Parameter(
    'group', openapi.IN_QUERY,
    description="Comma separated list of channel group ids",
    type=openapi.TYPE_ARRAY,
    items=openapi.Items(type=openapi.TYPE_INTEGER),
    collection_format='multi')

measurement_params = [metric_param, channel_param, nslc_param, group_param, ]
