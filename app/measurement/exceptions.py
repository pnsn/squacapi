from rest_framework.exceptions import APIException


class MissingParameterException(APIException):
    status_code = 422
    default_detail = 'Metric id, channel id, start time and end time required'
    default_code = 'missing_parameter'
