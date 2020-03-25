from django.db import models
from django.conf import settings
from dashboard.models import Widget
from nslc.models import Channel


class MeasurementBase(models.Model):
    '''Base class for all measurement models'''
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def class_name(self):
        return self.__class__.__name__.lower()


class Metric(MeasurementBase):
    '''Describes the kind of metric'''

    code = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    unit = models.CharField(max_length=255)
    url = models.CharField(max_length=255, default='')
    default_minval = models.FloatField(blank=True)
    default_maxval = models.FloatField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['name'])
        ]


class Measurement(MeasurementBase):
    '''describes the observable metrics'''
    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE,
        related_name='measurements'
    )
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='measurements'
    )
    value = models.FloatField()
    starttime = models.DateTimeField()
    endtime = models.DateTimeField()

    class Meta:
        indexes = [
            # index in desc order (newest first)
            models.Index(fields=['-starttime']),
            models.Index(fields=['-endtime']),
            models.Index(fields=['value'])

        ]

    def __str__(self):
        return f"Metric: {str(self.metric)} Channel: {str(self.channel)}"


class Threshold(MeasurementBase):
    widget = models.ForeignKey(
        Widget,
        on_delete=models.CASCADE,
        related_name='thresholds')

    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE,
        related_name='threshold')
    minval = models.FloatField(blank=True)
    maxval = models.FloatField(blank=True)


class Archive(models.Model):
    """An archive-summary of measurements"""

    # TODO: collapse into TextChoices innerclass after Django 3 upgrade
    DAY = 'day'
    WEEK = 'week'
    MONTH = 'month'
    YEAR = 'year'

    ARCHIVE_TYPE_CHOICES = [
        (DAY, "Day"),
        (WEEK, "Week"),
        (MONTH, "Month"),
        (YEAR, "Year")
    ]

    archive_type = models.CharField(max_length=8, choices=ARCHIVE_TYPE_CHOICES)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    metric = models.ForeignKey(Metric, on_delete=models.CASCADE)
    min = models.FloatField()
    max = models.FloatField()
    mean = models.FloatField()
    median = models.FloatField()
    stdev = models.FloatField()
    num_samps = models.IntegerField()
    starttime = models.DateTimeField(auto_now=False)
    endtime = models.DateTimeField(auto_now=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (f"Archive of Metric: {str(self.metric)} "
                f"Channel: {str(self.channel)} "
                f"from {format(self.starttime, '%m-%d-%Y')} "
                f"to {format(self.endtime, '%m-%d-%Y')}")
