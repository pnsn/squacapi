from organizations.models import Organization, OrganizationUser
# from organizations.abstract import AbstractOrganizationInvitation


class Account(Organization):
    class Meta:
        proxy = True


class AccountUser(OrganizationUser):
    class Meta:
        proxy = True


# class AccountInvitation(AbstractOrganizationInvitation):
#     class Meta:
#         abstract = False
