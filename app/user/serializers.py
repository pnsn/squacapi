from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import Group

from rest_framework import serializers


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('name',)


class UserSerializer(serializers.ModelSerializer):
    '''serialzer for the user object'''
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'firstname', 'lastname', 'is_staff', 
                  'organization', 'groups',)
        read_only_fields = ('is_staff',)
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    def create(self, validated_data):
        '''Create a new user with an encrypted password and return it'''
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validate_data):
        '''update user, set password and return'''
        # the None arg is the default, and for a passwd this is no good
        password = validate_data.pop('password', None)
        user = super().update(instance, validate_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class AuthTokenSerializer(serializers.Serializer):
    '''serializer for user auth object'''
    email = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        """Validate and authenticate the user"""
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        if not user:
            msg = ('Unable to authenticate with provided credentials')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs
