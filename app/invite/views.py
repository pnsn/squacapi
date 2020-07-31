import base64
import pytz
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import \
    validate_password, \
    get_password_validators
from rest_framework import status, serializers, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from invite.serializers import InviteTokenSerializer, InviteRegisterSerializer
from invite.models import InviteToken


class InviteView(generics.CreateAPIView):
    serializer_class = InviteTokenSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = request.data['user']
        user = get_object_or_404(
            get_user_model(),
            pk=user_id)
        if user.is_active:
            raise serializers.ValidationError(
                {'detail': 'Cannot Invite Active User'})
        # delete pending invitations for this user
        InviteToken.objects.filter(user=user).delete()
        InviteToken.objects.create(user=user)
        return Response({'detail': 'User Invited Successfully'},
                        status=status.HTTP_201_CREATED)


class RegisterView(generics.CreateAPIView):
    serializer_class = InviteRegisterSerializer
    permissions_class = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = request.data['token']
            decoded_token = base64.urlsafe_b64decode(token.encode()).decode()
            invite_token = get_object_or_404(InviteToken, id=decoded_token)
        except Exception:
            raise serializers.ValidationError(
                {'detail': 'Invalid Invitation Token'})
        expire_after = settings.INVITE_TOKEN_EXPIRY_TIME
        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        valid_token_time = now - timedelta(hours=expire_after)
        if invite_token.created_at < valid_token_time:
            raise serializers.ValidationError({'detail': 'token is expired'})

        try:
            password = request.data['password']
            validate_password(password, user=invite_token.user,
                              password_validators=get_password_validators(
                                  settings.AUTH_PASSWORD_VALIDATORS))
            invite_token.user.set_password(password)
            invite_token.user.is_active = True
            invite_token.user.save()
            InviteToken.objects.filter(user=invite_token.user).delete()
        except ValidationError as e:
            raise serializers.ValidationError({'detail': e.messages})

        return Response({'detail': 'Password sucessfully created.'},
                        status=status.HTTP_201_CREATED)
