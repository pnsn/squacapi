# WARNING. The organization app migration must be ran before these classes
# are instantiated
from django.contrib import admin
from organizations.models import (Organization, OrganizationUser,
                                  OrganizationOwner)
from institution.forms import InstitutionUserForm
from institution.models import Institution, InstitutionUser


class InstitutionUserAdmin(admin.ModelAdmin):
    form = InstitutionUserForm


admin.site.unregister(Organization)
admin.site.unregister(OrganizationUser)
admin.site.unregister(OrganizationOwner)
admin.site.register(Institution)
admin.site.register(InstitutionUser, InstitutionUserAdmin)
