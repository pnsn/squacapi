from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import Group

from rest_framework import serializers
from organization.models import Organization
from core.models import Contact, Notification
# from measurement.models import Contact


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('name',)


class UserSimpleSerializer(serializers.ModelSerializer):
    '''for nesting in organization_user serializer'''
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all()
    )

    class Meta:
        model = get_user_model()
        fields = ('email', 'firstname', 'lastname', 'id', 'is_active',
                  'last_login', 'organization', 'is_org_admin')


class UserBaseSerializer(serializers.ModelSerializer):
    '''serialzer for the user object'''

    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'firstname', 'lastname', 'is_staff',
                  'groups', 'id', 'organization', 'is_org_admin', 'last_login',
                  'is_active')
        read_only_fields = ('is_staff', 'id')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    def create(self, validated_data):
        '''Create a new user with an encrypted password set groups'''
        groups = validated_data.pop('groups', [])
        user = get_user_model().objects.create_user(**validated_data)
        if(len(groups) > 0):
            user.set_permission_groups(groups)
        return user

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


class UserWriteSerializer(UserBaseSerializer):
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all()
    )

    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all()
    )


class UserReadSerializer(UserBaseSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all()
    )


class UserMeSerializer(UserBaseSerializer):
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'firstname', 'lastname', 'is_staff',
                  'id', 'organization', 'is_org_admin', 'groups')
        read_only_fields = ('is_staff', 'id', 'is_org_admin', 'groups',
                            'organization', 'email')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}


class UserGroupSerializer(serializers.Serializer):
    class Meta:
        model = Group
        fields = ('id', 'name')
        read_only_fields = ('id', 'name')


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


class ContactSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="user:contact-detail")

    class Meta:
        model = Contact
        fields = (
            'id', 'url', 'email_value', 'sms_value', 'created_at',
            'updated_at', 'user_id'
        )
        read_only_fields = ('id',)


class NotificationSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="user:notification-detail")
    contact = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all())

    class Meta:
        model = Notification
        fields = (
            'id', 'url', 'notification_type', 'contact', 'level', 'created_at',
            'updated_at', 'user_id'
        )
        read_only_fields = ('id',)
