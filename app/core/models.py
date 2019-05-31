from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
    PermissionsMixin
from django.conf import settings


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        '''Creates and saves a new user'''
        if not email:
            raise ValueError("users must have an email address")
        # lowercase all emails!
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        # using=self._db for supporting multiple dbs not needed now but good
        # practice
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Creates and saves new superuser"""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    '''custom user model that supports using email instead of username'''
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    objects = UserManager()
    USERNAME_FIELD = 'email'


# NSLC APP
class Nslc(models.Model):
    '''abstract base class used by all nslc models'''
    code = models.CharField(max_length=2)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

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
