from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class RankingUserSerializer(serializers.ModelSerializer):
    position = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'points', 'position')

    def get_position(self, obj):
        # posição vem injetada no queryset pela view
        return getattr(obj, 'position', None)

    def get_points(self, obj):
        return getattr(obj, 'ranking_points', obj.points)
