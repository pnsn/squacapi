from organizations.models import Organization, OrganizationUser


class Account(Organization):
    class Meta:
        proxy = True


class AccountUser(OrganizationUser):
    class Meta:
        proxy = True
