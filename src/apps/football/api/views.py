from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
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

    @action(detail=False, methods=["get"], url_path="state")
    def state(self, request):
        """Retorna a fase atual, anterior, próxima e status final da competição."""
        competition = self._get_state_competition()
        if competition is None:
            return Response(
                {"detail": "Competição não encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )

        stages = list(
            Stage.objects.filter(competition=competition).order_by("order", "id")
        )
        if not stages:
            return Response(
                {
                    "competition": CompetitionSerializer(
                        competition, context={"request": request}
                    ).data,
                    "competition_finished": False,
                    "has_started": False,
                    "current_stage": None,
                    "previous_stage": None,
                    "next_stage": None,
                    "last_stage": None,
                    "stages": [],
                }
            )

        current_stage = next((stage for stage in stages if stage.is_current), None)
        last_stage = stages[-1]
        finished_stages = [stage for stage in stages if stage.finished_at is not None]
        previous_stage = self._get_previous_stage(stages, current_stage, finished_stages)
        next_stage = self._get_next_stage(stages, current_stage)
        competition_finished = (
            current_stage is None
            and last_stage.finished_at is not None
            and len(finished_stages) == len(stages)
        )

        serializer_context = {"request": request}
        return Response(
            {
                "competition": CompetitionSerializer(
                    competition, context=serializer_context
                ).data,
                "competition_finished": competition_finished,
                "has_started": current_stage is not None or bool(finished_stages),
                "current_stage": self._serialize_stage(current_stage, serializer_context),
                "previous_stage": self._serialize_stage(
                    previous_stage, serializer_context
                ),
                "next_stage": self._serialize_stage(next_stage, serializer_context),
                "last_stage": self._serialize_stage(last_stage, serializer_context),
                "stages": StageSerializer(
                    stages, many=True, context=serializer_context
                ).data,
            }
        )

    def _get_state_competition(self) -> Competition | None:
        competition_id = self.request.query_params.get("competition")
        comp_external_id = self.request.query_params.get("competition_external_id")

        if competition_id:
            return Competition.objects.filter(id=competition_id).first()
        if comp_external_id:
            return Competition.objects.filter(external_id=comp_external_id).first()

        current_stage = (
            Stage.objects.select_related("competition")
            .filter(is_current=True)
            .order_by("-competition__season", "order", "id")
            .first()
        )
        if current_stage:
            return current_stage.competition

        return Competition.objects.order_by("-season", "name", "id").first()

    def _get_previous_stage(
        self,
        stages: list[Stage],
        current_stage: Stage | None,
        finished_stages: list[Stage],
    ) -> Stage | None:
        if current_stage:
            current_index = stages.index(current_stage)
            ordered_previous = stages[:current_index]
            finished_previous = [
                stage for stage in ordered_previous if stage.finished_at is not None
            ]
            if finished_previous:
                return finished_previous[-1]
            return None

        if finished_stages:
            return finished_stages[-1]
        return None

    def _get_next_stage(
        self, stages: list[Stage], current_stage: Stage | None
    ) -> Stage | None:
        if current_stage is None:
            return None

        current_index = stages.index(current_stage)
        if current_index >= len(stages) - 1:
            return None
        return stages[current_index + 1]

    def _serialize_stage(
        self, stage: Stage | None, serializer_context: dict
    ) -> dict | None:
        if stage is None:
            return None
        return StageSerializer(stage, context=serializer_context).data


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
