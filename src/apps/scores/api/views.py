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
from apps.football.models import Competition, Stage
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

    @action(detail=False, methods=['get'], url_path='phase-score-history')
    def phase_score_history(self, request):
        """Retorna todas as fases com a pontuação do usuário, usando 0 quando não há escalação."""
        competition = self._get_history_competition()
        if competition is None:
            return Response([])

        stages = Stage.objects.filter(competition=competition).order_by('order', 'id')
        lineups_by_stage = {
            lineup.stage_id: lineup
            for lineup in self.get_queryset().filter(stage__competition=competition)
        }

        history = []
        for stage in stages:
            lineup = lineups_by_stage.get(stage.id)
            total_points = 0.0
            items = []
            if lineup:
                total_points, items = calculate_lineup_score(lineup, include_items=True)

            history.append({
                'stage': stage.id,
                'stage_name': stage.name,
                'stage_order': stage.order,
                'is_current': stage.is_current,
                'is_finished': stage.finished_at is not None,
                'lineup': lineup.id if lineup else None,
                'has_lineup': lineup is not None,
                'total_points': total_points,
                'items': items,
            })

        return Response(history)

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

    def _get_history_competition(self):
        competition_id = self.request.query_params.get('competition')
        comp_external_id = self.request.query_params.get('competition_external_id')

        if competition_id:
            return Competition.objects.filter(id=competition_id).first()
        if comp_external_id:
            return Competition.objects.filter(external_id=comp_external_id).first()

        current_stage = (
            Stage.objects.select_related('competition')
            .filter(is_current=True)
            .order_by('-competition__season', 'order', 'id')
            .first()
        )
        if current_stage:
            return current_stage.competition

        latest_lineup = (
            self.get_queryset()
            .select_related('stage__competition')
            .order_by('-stage__competition__season', '-stage__order', '-stage_id')
            .first()
        )
        if latest_lineup:
            return latest_lineup.stage.competition

        return Competition.objects.order_by('-season', 'name', 'id').first()


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
