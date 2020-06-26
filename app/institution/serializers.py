from rest_framework import serializers
from institution.models import Institution, InstitutionUser
from django.contrib.auth import get_user_model


class InstitutionUserSerializer(serializers.ModelSerializer):

    user = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all()
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all()
    )

    class Meta:
        model = InstitutionUser
        fields = (
            'id', 'is_admin', 'user', 'organization'
        )
        read_only_fields = ('id', 'institution')


class InstitutionSerializer(serializers.ModelSerializer):
    organization_users = InstitutionUserSerializer(many=True)

    class Meta:
        model = Institution
        fields = (
            'id', 'name', 'is_active', 'organization_users'
        )
        read_only_fields = ('id',)
