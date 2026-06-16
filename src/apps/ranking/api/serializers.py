from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class RankingUserSerializer(serializers.ModelSerializer):
    position = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'points', 'position', 'photo', 'photo_url')

    def get_position(self, obj):
        # posição vem injetada no queryset pela view
        return getattr(obj, 'position', None)

    def get_points(self, obj):
        return getattr(obj, 'ranking_points', obj.points)

    def get_photo(self, obj):
        return self._build_photo_url(obj)

    def get_photo_url(self, obj):
        return self._build_photo_url(obj)

    def _build_photo_url(self, obj):
        profile = getattr(obj, 'profile', None)

        request = self.context.get('request')
        url = (
            profile.photo.url
            if profile and profile.photo
            else settings.DEFAULT_PROFILE_PHOTO_URL
        )
        if request:
            return request.build_absolute_uri(url)
        return url
