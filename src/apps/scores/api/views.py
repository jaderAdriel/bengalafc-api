from django.db.models import Prefetch
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import (
    FantasyLineupSerializer,
    FantasyTransferSerializer,
    PlayerSerializer,
    ScoreEventSerializer,
)
from apps.scores.models import FantasyLineup, FantasyLineupPlayer, FantasyTransfer, Player, ScoreEvent
from apps.scores.services import calculate_lineup_score, create_player, create_coach


class PlayerViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PlayerSerializer

    @action(detail=False, methods=['post'])
    def create_profile(self, request):
        if Player.objects.filter(user=request.user).exists():
            return Response({'detail': 'Perfil já existe.'}, status=400)

        position = request.data.get('position')
        football_player_id = request.data.get('football_player_id')  # external_id da API

        player = create_player(request.user, position, football_player_id)
        return Response(PlayerSerializer(player).data, status=201)

    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            player = request.user.player_profile
            return Response(PlayerSerializer(player).data)
        except Player.DoesNotExist:
            return Response({'detail': 'Perfil não encontrado.'}, status=404)


class ScoreEventViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ScoreEventSerializer

    def get_queryset(self):
        return ScoreEvent.objects.filter(
            player__user=self.request.user
        ).select_related('fixture')

    @action(detail=False, methods=['get'])
    def my_scores(self, request):
        """Lista todos os eventos de pontuação do usuário"""
        events = self.get_queryset()
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def total(self, request):
        """Retorna o total de pontos do usuário"""
        return Response({'points': request.user.points})


class FantasyLineupViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FantasyLineupSerializer

    def get_queryset(self):
        queryset = FantasyLineup.objects.filter(user=self.request.user).select_related(
            'stage',
            'captain',
            'captain__team',
        ).prefetch_related(
            Prefetch(
                'players',
                queryset=FantasyLineupPlayer.objects.select_related('player', 'player__team'),
            )
        )

        stage_id = self.request.query_params.get('stage')
        if stage_id:
            queryset = queryset.filter(stage_id=stage_id)

        return queryset

    @action(detail=False, methods=['get'], url_path='by-stage/(?P<stage_id>[^/.]+)')
    def by_stage(self, request, stage_id=None):
        lineup = self.get_queryset().filter(stage_id=stage_id).first()
        if not lineup:
            return Response({'detail': 'Escalação não encontrada para esta fase.'}, status=404)

        serializer = self.get_serializer(lineup)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='score-history')
    def score_history(self, request, pk=None):
        lineup = self.get_object()
        total_points, items = calculate_lineup_score(lineup, include_items=True)
        return Response({
            'lineup': lineup.id,
            'stage': lineup.stage_id,
            'total_points': total_points,
            'items': items,
        })


class FantasyTransferViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FantasyTransferSerializer

    def get_queryset(self):
        queryset = FantasyTransfer.objects.filter(user=self.request.user).select_related(
            'stage',
            'lineup',
            'from_player',
            'from_player__team',
            'to_player',
            'to_player__team',
        )

        stage_id = self.request.query_params.get('stage')
        if stage_id:
            queryset = queryset.filter(stage_id=stage_id)

        return queryset
