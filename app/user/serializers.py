from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import Group

from rest_framework import serializers
from organization.models import Organization


class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name',)
        read_only_fields = ('id',)


class UserSerializer(serializers.ModelSerializer):
    '''serialzer for the user object'''

    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all()
    )
    groups = serializers.SlugRelatedField(
        slug_field="name",
        many=True,
        queryset=Group.objects.all()
    )

    class Meta:
        model = get_user_model()
        fields = ('email', 'firstname', 'lastname', 'is_staff',
                  'groups', 'id', 'organization', 'is_org_admin', 'last_login',
                  'is_active')
        read_only_fields = ('is_staff', 'id')

    def create(self, validated_data):
        '''Create a new user with an encrypted password set groups'''
        groups = validated_data.pop('groups', [])
        user = get_user_model().objects.create_user(**validated_data)
        if(len(groups) > 0):
            user.set_permission_groups(groups)
        return user


class UserUpdateSerializer(UserSerializer):
    '''serializer for updating users'''
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all()
    )
    groups = serializers.SlugRelatedField(
        slug_field="name",
        many=True,
        queryset=Group.objects.all()
    )

    class Meta:
        model = get_user_model()
        fields = ('email', 'firstname', 'lastname', 'password', 'is_staff',
                  'groups', 'id', 'organization', 'is_org_admin', 'last_login',
                  'is_active')
        read_only_fields = ('is_staff', 'id', 'email')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5,
                                     "required": False},
                        'firstname': {"required": False},
                        'lastname': {"required": False},
                        'organization': {"required": False},
                        'groups': {"required": False}
                        }

    def update(self, instance, validate_data):
        '''update user, set group and password and return'''
        # the None arg is the default, and for a passwd this is no good
        password = validate_data.pop('password', None)
        groups = validate_data.pop('groups', [])
        user = super().update(instance, validate_data)
        if(len(groups) > 0):
            user.set_permission_groups(groups)
        if password:
            user.set_password(password)
            user.save()
        return user


class UserMeSerializer(UserUpdateSerializer):
    '''serializer for managing authenticated user'''
    groups = serializers.StringRelatedField(many=True, read_only=True)
    organization = serializers.PrimaryKeyRelatedField(
        read_only=True
    )

    class Meta:
        model = get_user_model()
        fields = ('id', 'firstname', 'lastname', 'password', 'groups',
                  'organization', 'email', 'is_active', 'is_org_admin',
                  'is_staff')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5,
                                     "required": False},
                        'firstname': {"required": False},
                        'lastname': {"required": False},
                        'organization': {"read_only": True, "required": False}
                        }
        read_only_fields = ('id', 'email', 'is_active', 'is_org_admin',
                            'groups', 'organization', 'is_staff')


class UserSimpleSerializer(UserSerializer):
    '''serializer for nesting in orgs'''
    groups = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = ('email', 'firstname', 'lastname', 'id',
                  'is_active', 'organization', 'is_org_admin',
                  'groups')


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
