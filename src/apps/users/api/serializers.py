from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.users.models import UserProfile

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)
    points = serializers.IntegerField(source='user.points', read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'points', 'photo', 'photo_url', 'favorite_team'
        )

    def get_photo_url(self, obj):
        return self._build_photo_url(obj)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['photo'] = self._build_photo_url(instance)
        return data

    def _build_photo_url(self, obj):
        request = self.context.get('request')
        url = obj.photo.url if obj.photo else settings.DEFAULT_PROFILE_PHOTO_URL
        if request:
            return request.build_absolute_uri(url)
        return url

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
