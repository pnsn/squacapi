from rest_framework import serializers
# from org.models import Org, OrgUser
from organizations.models import (Organization, OrganizationUser)
from django.contrib.auth import get_user_model


class OrganizationUserSerializer(serializers.ModelSerializer):

    user = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all()
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all()
    )

    class Meta:
        model = OrganizationUser
        fields = (
            'id', 'is_admin', 'user', 'organization'
        )
        read_only_fields = ('id', 'org')


class OrganizationSerializer(serializers.ModelSerializer):
    organization_users = OrganizationUserSerializer(many=True)

    class Meta:
        model = Organization
        fields = (
            'id', 'name', 'is_active', 'organization_users', 'slug',
            'created', 'modified'
        )
        read_only_fields = ('id',)
