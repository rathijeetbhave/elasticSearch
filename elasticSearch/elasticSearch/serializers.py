from rest_framework import serializers
from django.contrib.auth.models import User


class DummySerializer(serializers.Serializer) :
    data = serializers.CharField()
    title = serializers.CharField()
    id = serializers.IntegerField()
    score = serializers.FloatField()
