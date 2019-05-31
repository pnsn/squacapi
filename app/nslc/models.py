from django.db import models
# from django.conf import settings


class Nslc(models.Model):
    '''abstract base class used by all nslc models'''
    code = models.CharField(max_length=2)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    '''force lowercase on code to provide for consistent url slug lookups'''
    def clean(self):
        self.code = self.code.lower()

    def __str__(self):
        return self.code.upper()

    def class_name(self):
        return self.__class__.__name__.lower()


class Network(Nslc):
    code = models.CharField(max_length=2, unique=True)


class Station(Nslc):
    code = models.CharField(max_length=5)
    network = models.ForeignKey(
        Network,
        on_delete=models.CASCADE,
        related_name='stations'
    )

    class Meta:
        unique_together = (("code", "network"),)


class Location(Nslc):
    lat = models.FloatField()
    lon = models.FloatField()
    elev = models.FloatField()
    station = models.ForeignKey(Station, on_delete=models.CASCADE,
                                related_name='locations')

    class Meta:
        unique_together = (("code", "station"),)


class Channel(Nslc):
    code = models.CharField(max_length=3)
    sample_rate = models.FloatField(null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE,
                                 related_name="channels")

    class Meta:
        unique_together = (("code", "location"),)


''' many to many with channelgroup
To get the all channelgroups of channel c.channelgroup_set.all()
# '''

# '''
#  Many to many with channels
#  To list
#  cg.channels.all()
#  to add to
#  cg.channels.add(c)
# '''
# class ChannelGroup(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL,
#           on_delete=models.CASCADE,)
#     public = models.BooleanField(default=False)
#     channels=models.ManyToManyField(Channel)
#     name=models.CharField(max_length=255)
#     description=models.CharField(max_length=255,null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
