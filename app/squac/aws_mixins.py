import boto3
from django.conf import settings
''' module to manage aws services'''


class Sns:
    '''Simple Notification Service'''

    ARNS = {
        'admin': settings.AWS_SNS_ADMIN_ARN
    }

    def __init__(self, topic):
        self.arn = self.ARNS[topic]
        self.client = boto3.client('sns')

    def publish(self, subject, message):
        return self.client.publish(
            TopicArn=self.arn,
            Subject=subject,
            Message=message
        )
