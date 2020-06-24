from rest_framework import serializers
from institution.models import Institution, InstitutionUser
from user.serializers import UserSerializer
from django.contrib.auth import get_user_model


class InstitutionUserSerializer(serializers.ModelSerializer):
    # user = serializers.PrimaryKeyRelatedField(
    #    queryset=get_user_model().objects.all()
    # )
    user = UserSerializer()
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all()
    )

    class Meta:
        model = InstitutionUser
        fields = (
            'id', 'is_admin', 'user', 'organization'
        )
        read_only_fields = ('id', 'institution')

    def create(self, validated_data):
        # print("in serializer create")
        # print(validated_data)
        user_param = validated_data.pop('user')
        get_user_model().objects.create_user(**validated_data)
        user = get_user_model().objects.get_or_create(
            email=user_param['email'],
            defaults={
                'firstname': user_param['firstname'],
                'lastname': user_param['lastname'],
            }
        )
        print(user[0])
        validated_data['user_id'] = user[0].id
        institution_user = InstitutionUser.objects.create(**validated_data)
        return institution_user


class InstitutionSerializer(serializers.ModelSerializer):
    organization_users = InstitutionUserSerializer(many=True)

    class Meta:
        model = Institution
        fields = (
            'id', 'name', 'is_active', 'organization_users'
        )
        read_only_fields = ('id',)
