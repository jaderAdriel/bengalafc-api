from rest_framework import viewsets, mixins, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from apps.ranking.models import Friendship
from apps.scores.models import FantasyLineup
from apps.scores.services import calculate_lineup_score
from .serializers import RankingUserSerializer

User = get_user_model()


class RankingViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RankingUserSerializer

    @action(detail=False, methods=['get'], url_path='global')
    def global_ranking(self, request):
        queryset = User.objects.all()
        users_with_position = self._rank_users(queryset)

        serializer = self.get_serializer(users_with_position, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='friends')
    def friends_ranking(self, request):
        # Pega os IDs dos amigos do usuário logado
        friend_ids = Friendship.objects.filter(
            from_user=request.user
        ).values_list('to_user_id', flat=True)

        # Inclui o próprio usuário no ranking de amigos
        queryset = User.objects.filter(
            id__in=list(friend_ids) + [request.user.id]
        )
        users_with_position = self._rank_users(queryset)

        serializer = self.get_serializer(users_with_position, many=True)
        return Response(serializer.data)

    def _rank_users(self, queryset):
        users = list(queryset.order_by('id'))
        user_map = {user.id: user for user in users}

        lineups = FantasyLineup.objects.filter(
            user_id__in=user_map.keys(),
        ).select_related(
            'user',
            'stage',
            'captain',
            'coach',
            'coach__team',
        ).prefetch_related(
            'players',
            'players__player',
        )

        points_by_user = {user.id: 0.0 for user in users}
        for lineup in lineups:
            points_by_user[lineup.user_id] += calculate_lineup_score(lineup)

        for user in users:
            user.ranking_points = points_by_user[user.id]

        users.sort(key=lambda user: (-user.ranking_points, user.username.lower(), user.id))
        for index, user in enumerate(users, start=1):
            user.position = index

        return users

    @action(detail=False, methods=['post'], url_path='friends/add')
    def add_friend(self, request):
        # Adiciona amigo pelo username
        username = request.data.get('username')
        if not username:
            return Response({'detail': 'username é obrigatório.'}, status=400)

        try:
            to_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'detail': 'Usuário não encontrado.'}, status=404)

        if to_user == request.user:
            return Response({'detail': 'Você não pode adicionar a si mesmo.'}, status=400)

        friendship, created = Friendship.objects.get_or_create(
            from_user=request.user,
            to_user=to_user
        )

        if not created:
            return Response({'detail': 'Amizade já existe.'}, status=400)

        return Response({'detail': f'{username} adicionado com sucesso.'}, status=201)
