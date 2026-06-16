from django.db.models import Q
from rest_framework import permissions, viewsets
from apps.football.models import (
    Competition,
    Fixture,
    Player,
    PlayerStatistic,
    Stage,
    Team,
    TeamStatistic,
    Coach,
)
from .serializers import (
    CompetitionSerializer,
    FixtureSerializer,
    PlayerSerializer,
    PlayerStatisticSerializer,
    StageSerializer,
    TeamSerializer,
    TeamStatisticSerializer,
    CoachSerializer,
)


class TeamViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar equipes/seleções."""

    queryset = Team.objects.all().order_by("name")
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        country = self.request.query_params.get("country")
        is_active = self.request.query_params.get("is_active")

        if country:
            queryset = queryset.filter(country__iexact=country)
        if is_active is not None:
            is_active_bool = is_active.lower() in ["true", "1"]
            queryset = queryset.filter(is_active=is_active_bool)

        return queryset


class PlayerViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar jogadores."""

    queryset = Player.objects.all().order_by("name")
    serializer_class = PlayerSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        team_id = self.request.query_params.get("team")
        team_external_id = self.request.query_params.get("team_external_id")
        position = self.request.query_params.get("position")
        nationality = self.request.query_params.get("nationality")
        stage_id = self.request.query_params.get("stage")

        if team_id:
            queryset = queryset.filter(team_id=team_id)
        if team_external_id:
            queryset = queryset.filter(team__external_id=team_external_id)
        if position:
            queryset = queryset.filter(position__icontains=position)
        if nationality:
            queryset = queryset.filter(nationality__iexact=nationality)
        if stage_id:
            stage_team_filter = Q(team__home_fixtures__stage_id=stage_id) | Q(
                team__away_fixtures__stage_id=stage_id
            )
            queryset = queryset.filter(stage_team_filter).distinct()

        return queryset


class CompetitionViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar competições."""

    queryset = Competition.objects.all().order_by("-season", "name")
    serializer_class = CompetitionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        season = self.request.query_params.get("season")
        comp_type = self.request.query_params.get("type")

        if season:
            queryset = queryset.filter(season=season)
        if comp_type:
            queryset = queryset.filter(type__iexact=comp_type)

        return queryset


class StageViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar fases da competição."""

    queryset = Stage.objects.all().order_by("order", "name")
    serializer_class = StageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        competition_id = self.request.query_params.get("competition")
        comp_external_id = self.request.query_params.get("competition_external_id")

        if competition_id:
            queryset = queryset.filter(competition_id=competition_id)
        if comp_external_id:
            queryset = queryset.filter(competition__external_id=comp_external_id)

        return queryset


class FixtureViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar partidas."""

    queryset = Fixture.objects.all().order_by("kickoff_at")
    serializer_class = FixtureSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        competition_id = self.request.query_params.get("competition")
        stage_id = self.request.query_params.get("stage")
        team_id = self.request.query_params.get("team")  # home or away team
        status = self.request.query_params.get("status")

        if competition_id:
            queryset = queryset.filter(competition_id=competition_id)
        if stage_id:
            queryset = queryset.filter(stage_id=stage_id)
        if team_id:
            queryset = queryset.filter(home_team_id=team_id) | queryset.filter(
                away_team_id=team_id
            )
        if status:
            queryset = queryset.filter(status=status)

        return queryset


class PlayerStatisticViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar estatísticas de jogadores em partidas."""

    queryset = PlayerStatistic.objects.all().order_by("-fixture__kickoff_at")
    serializer_class = PlayerStatisticSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        player_id = self.request.query_params.get("player")
        fixture_id = self.request.query_params.get("fixture")

        if player_id:
            queryset = queryset.filter(player_id=player_id)
        if fixture_id:
            queryset = queryset.filter(fixture_id=fixture_id)

        return queryset


class TeamStatisticViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar estatísticas de equipes em partidas."""

    queryset = TeamStatistic.objects.all().order_by("-fixture__kickoff_at")
    serializer_class = TeamStatisticSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        team_id = self.request.query_params.get("team")
        fixture_id = self.request.query_params.get("fixture")

        if team_id:
            queryset = queryset.filter(team_id=team_id)
        if fixture_id:
            queryset = queryset.filter(fixture_id=fixture_id)

        return queryset

class CoachViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar técnicos."""

    queryset = Coach.objects.all().order_by("name")
    serializer_class = CoachSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        team_id = self.request.query_params.get("team")
        nationality = self.request.query_params.get("nationality")
        is_active = self.request.query_params.get("is_active")

        if team_id:
            queryset = queryset.filter(team_id=team_id)
        if nationality:
            queryset = queryset.filter(nationality__iexact=nationality)
        if is_active is not None:
            is_active_bool = is_active.lower() in ["true", "1"]
            queryset = queryset.filter(is_active=is_active_bool)

        return queryset
