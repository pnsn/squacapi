from rest_framework import serializers
from account.models import Account, AccountUser
from user.serializers import UserSerializer
from django.contrib.auth import get_user_model


class AccountUserSerializer(serializers.ModelSerializer):
    # user = serializers.PrimaryKeyRelatedField(
    #    queryset=get_user_model().objects.all()
    # )
    user = UserSerializer()
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all()
    )

    class Meta:
        model = AccountUser
        fields = (
            'id', 'is_admin', 'user', 'organization'
        )
        read_only_fields = ('id', 'account')

    def create(self, validated_data):
        print("in serializer create")
        print(validated_data)
        user_param = validated_data.pop('user')
        user = get_user_model().objects.get_or_create(
            email=user_param['email'],
            defaults={
                'firstname': user_param['firstname'],
                'lastname': user_param['lastname'],
            }
        )
        print(user[0])
        validated_data['user_id'] = user[0].id
        account_user = AccountUser.objects.create(**validated_data)
        return account_user


class AccountSerializer(serializers.ModelSerializer):
    organization_users = AccountUserSerializer(many=True)

    class Meta:
        model = Account
        fields = (
            'id', 'name', 'is_active', 'organization_users'
        )
        read_only_fields = ('id',)
