  # -*- coding: utf-8 -*
from __future__ import unicode_literals

from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Pallet

from waybills.serializers import WaybillSerializer

class PalletSerializer(serializers.HyperlinkedModelSerializer):
    # waybills = WaybillSerializer(many=True, read_only=True)
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Pallet
        fields = ('url', 'user', 'id', 'batch_no', 'weight', 'waybills')
