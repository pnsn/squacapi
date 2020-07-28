from rest_framework import serializers
# from org.models import Org, OrgUser
from organization.models import Organization
from user.serializers import UserSimpleSerializer


class OrganizationSerializer(serializers.ModelSerializer):
    users = UserSimpleSerializer(many=True)

    class Meta:
        model = Organization
        fields = (
            'id', 'name', 'description',
            'created_at', 'updated_at', 'users'
        )
        read_only_fields = ('id',)
