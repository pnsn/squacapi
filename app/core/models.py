from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
    PermissionsMixin, Group
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import models
from django.utils.translation import gettext_lazy as _

from organization.models import Organization


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, organization=None,
                    **extra_fields):
        '''Creates and saves a new user'''
        if not email:
            raise ValueError("users must have an email address")
        # lowercase all emails!
        if not organization:
            organization = Organization.objects.get(name='PNSN')
        user = self.model(
            email=self.normalize_email(email),
            organization=organization,
            **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, organization=None,
                         is_active=True):
        """Creates and saves new superuser"""
        user = self.create_user(email, password, organization)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = is_active
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    '''custom user model that supports using email instead of username'''
    email = models.EmailField(max_length=255, unique=True)
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_org_admin = models.BooleanField(default=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='users'
    )

    objects = UserManager()
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.firstname + " " + self.lastname

    def belongs_to_group(self, group_name):
        '''check if user belongs to group by passing in group name (string)'''
        return self.groups.filter(name=group_name).exists()

    def set_permission_groups(self, group_list):
        '''group_list is list of Group objects (permissions)
        simplify groups, which are hierachical
        contributer <  reporter < viewer
        viewer is default
        adding user to group that user already belongs to doesn't duplicate
        '''
        org_admin = Group.objects.get(name='org_admin')
        '''organization admins can edit org users'''
        if self.is_org_admin:
            self.groups.add(org_admin)
        else:
            org_admin.user_set.remove(self)

        viewer = Group.objects.get(name='viewer')
        reporter = Group.objects.get(name='reporter')
        contributor = Group.objects.get(name='contributor')
        self.groups.add(viewer)
        if contributor in group_list:
            self.groups.add(reporter)
            self.groups.add(contributor)
        elif reporter in group_list:
            self.groups.add(reporter)
            contributor.user_set.remove(self)
        else:  # viewer (least priv)
            reporter.user_set.remove(self)
            contributor.user_set.remove(self)

    def get_notifications(self, level):
        return Notification.objects.filter(user=self, level=level)


class Contact(models.Model):
    """Contains contact information for alert notifications"""
    email_value = models.CharField(
        max_length=255,
        default="",
        blank=True,
        validators=[validate_email, ]
    )
    sms_value = models.CharField(
        max_length=255,
        default="",
        blank=True
    )
    name = models.CharField(
        max_length=255,
        default="",
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        if not self.name:
            return (f"email_value: {self.email_value}, "
                    f"sms_value: {self.sms_value}"
                    )
        else:
            return self.name

    def save(self, *args, **kwargs):
        """
        Do regular save except also validate fields. This doesn't happen
        automatically on save
        """
        try:
            self.full_clean()
        except ValidationError:
            raise

        super().save(*args, **kwargs)  # Call the "real" save() method.


class Notification(models.Model):
    '''User notification model for alerting'''

    class NotificationType(models.TextChoices):
        EMAIL = 'email', _('Email')
        SMS = 'sms', _('SMS')
        SLACK = 'slack', _('Slack')

    # Define choices for notification level
    class Level(models.IntegerChoices):
        ONE = 1
        TWO = 2
        THREE = 3

    notification_type = models.CharField(
        max_length=255,
        choices=NotificationType.choices,
        default=NotificationType.EMAIL
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        null=True,
        related_name='notifications'
    )
    level = models.IntegerField(
        choices=Level.choices,
        default=Level.ONE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def send_email(self, alert):
        subject = (f"SQUAC alert for '{alert.trigger.monitor}', "
                   f"level {alert.trigger.level}"
                   )
        message = alert.get_email_message()
        send_mail(subject,
                  message,
                  settings.EMAIL_NO_REPLY,
                  [self.contact.email_value, ],
                  fail_silently=False,
                  )
        return True

    def send_sms(self, alert):
        pass

    def send_slack(self, alert):
        pass

    def send(self, alert):
        if self.notification_type == self.NotificationType.EMAIL:
            self.send_email(alert)
        elif self.notification_type == self.NotificationType.SLACK:
            self.send_slack(alert)
        elif self.notification_type == self.NotificationType.SMS:
            self.send_sms(alert)

    def __str__(self):
        return f'{self.user} {self.notification_type} notification'
