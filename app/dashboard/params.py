from drf_yasg import openapi
'''
    Param overrides for doc generator (won't be needed in V3)
'''

id_param = openapi.Parameter(
    'id',
    openapi.IN_PATH,
    type=openapi.TYPE_STRING)
