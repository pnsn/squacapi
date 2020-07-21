# WARNING. The organization app migration must be ran before these classes
# are instantiated
from django.contrib import admin

from organization.models import Organization


class OrganizationAdmin(admin.ModelAdmin):
    # form = OrganizationUserForm
    pass


admin.site.register(Organization, OrganizationAdmin)
