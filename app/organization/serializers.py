from rest_framework import serializers
# from org.models import Org, OrgUser
from organization.models import Organization
from user.serializers import UserSerializer


class OrganizationSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True)

    class Meta:
        model = Organization
        fields = (
            'id', 'name', 'description',
            'created_at', 'updated_at', 'users'
        )
        read_only_fields = ('id',)
