# WARNING. The organization app migration must be ran before these classes
# are instantiated

from organizations.models import (Organization, OrganizationUser)


class Institution(Organization):
    class Meta:
        proxy = True


class InstitutionUser(OrganizationUser):
    class Meta:
        proxy = True
