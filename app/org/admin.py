# WARNING. The organization app migration must be ran before these classes
# are instantiated
from django.contrib import admin
# from organizations.models import (Organization, OrganizationUser,
#                                   OrganizationOwner)
from org.forms import OrganizationUserForm
# from org.models import Org, OrgUser


class OrgUserAdmin(admin.ModelAdmin):
    form = OrganizationUserForm


# admin.site.unregister(Organization)
# admin.site.unregister(OrganizationUser)
# admin.site.unregister(OrganizationOwner)
# admin.site.register(Org)
# admin.site.register(OrgUser, OrgUserAdmin)
