from rest_framework import viewsets, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer, UserProfileSerializer
from django.contrib.auth import get_user_model
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

User = get_user_model()


class UserViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = (permissions.AllowAny,)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = UserProfileSerializer(
            request.user.profile,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], permission_classes=[permissions.IsAuthenticated],  parser_classes=[MultiPartParser, FormParser, JSONParser])
    def update_profile(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(
            profile,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def profiles(self, request):
        from apps.users.models import UserProfile
        profiles = UserProfile.objects.select_related('user', 'favorite_team').all()
        serializer = UserProfileSerializer(
            profiles,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['patch'],
        url_path='update_profile',
        permission_classes=[permissions.IsAdminUser],
        parser_classes=[MultiPartParser, FormParser, JSONParser]
    )
    def admin_update_profile(self, request, pk=None):
        user = self.get_object()
        from apps.users.models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        serializer = UserProfileSerializer(
            profile,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
