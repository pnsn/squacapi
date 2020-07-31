from rest_framework import serializers
from invite.models import InviteToken


class InviteTokenSerializer(serializers.Serializer):
    class Meta:
        model = InviteToken
        fields = ('user', )


class InviteRegisterSerializer(serializers.Serializer):
    class Meta:
        model = InviteToken
        fields = ('user', 'id')
