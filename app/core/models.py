from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
    PermissionsMixin
from organization.models import Organization


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, organization=None,
                    **extra_fields):
        '''Creates and saves a new user'''
        if not email:
            raise ValueError("users must have an email address")
        # lowercase all emails!
        if not organization:
            raise ValueError('users must have an organization')
        user = self.model(
            email=self.normalize_email(email),
            organization=organization,
            **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, organization):
        """Creates and saves new superuser"""
        user = self.create_user(email, password, organization)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    '''custom user model that supports using email instead of username'''
    email = models.EmailField(max_length=255, unique=True)
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
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
