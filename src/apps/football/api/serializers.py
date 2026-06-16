from rest_framework import serializers
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


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = "__all__"


class PlayerSerializer(serializers.ModelSerializer):
    # Permite ler dados do time detalhado, mas aceita PK na criação
    team_detail = TeamSerializer(source="team", read_only=True)

    class Meta:
        model = Player
        fields = [
            "id",
            "external_id",
            "team",
            "team_detail",
            "name",
            "firstname",
            "lastname",
            "age",
            "nationality",
            "height",
            "weight",
            "photo",
            "position",
            "number",
            "is_active",
            "created_at",
            "updated_at",
        ]


class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = "__all__"


class StageSerializer(serializers.ModelSerializer):
    competition_detail = CompetitionSerializer(source="competition", read_only=True)
    is_finished = serializers.SerializerMethodField()
    is_last_stage = serializers.SerializerMethodField()
    previous_stage = serializers.SerializerMethodField()
    next_stage = serializers.SerializerMethodField()

    class Meta:
        model = Stage
        fields = [
            "id",
            "competition",
            "competition_detail",
            "name",
            "order",
            "starts_at",
            "lineup_deadline_at",
            "ends_at",
            "finished_at",
            "is_current",
            "is_finished",
            "is_last_stage",
            "previous_stage",
            "next_stage",
        ]

    def get_is_finished(self, obj: Stage) -> bool:
        return obj.finished_at is not None

    def get_is_last_stage(self, obj: Stage) -> bool:
        stage_ids = self._get_ordered_stage_ids(obj)
        return bool(stage_ids) and stage_ids[-1] == obj.id

    def get_previous_stage(self, obj: Stage) -> int | None:
        stage_ids = self._get_ordered_stage_ids(obj)
        try:
            current_index = stage_ids.index(obj.id)
        except ValueError:
            return None
        if current_index == 0:
            return None
        return stage_ids[current_index - 1]

    def get_next_stage(self, obj: Stage) -> int | None:
        stage_ids = self._get_ordered_stage_ids(obj)
        try:
            current_index = stage_ids.index(obj.id)
        except ValueError:
            return None
        if current_index >= len(stage_ids) - 1:
            return None
        return stage_ids[current_index + 1]

    def _get_ordered_stage_ids(self, obj: Stage) -> list[int]:
        cache = self.context.setdefault("_stage_sequence_cache", {})
        if obj.competition_id not in cache:
            cache[obj.competition_id] = list(
                Stage.objects.filter(competition_id=obj.competition_id)
                .order_by("order", "id")
                .values_list("id", flat=True)
            )
        return cache[obj.competition_id]


class FixtureSerializer(serializers.ModelSerializer):
    competition_detail = CompetitionSerializer(source="competition", read_only=True)
    stage_detail = StageSerializer(source="stage", read_only=True)
    home_team_detail = TeamSerializer(source="home_team", read_only=True)
    away_team_detail = TeamSerializer(source="away_team", read_only=True)

    class Meta:
        model = Fixture
        fields = [
            "id",
            "external_id",
            "competition",
            "competition_detail",
            "stage",
            "stage_detail",
            "home_team",
            "home_team_detail",
            "away_team",
            "away_team_detail",
            "kickoff_at",
            "status",
            "home_score",
            "away_score",
            "venue",
            "created_at",
            "updated_at",
        ]


class PlayerStatisticSerializer(serializers.ModelSerializer):
    player_detail = PlayerSerializer(source="player", read_only=True)
    fixture_detail = FixtureSerializer(source="fixture", read_only=True)

    class Meta:
        model = PlayerStatistic
        fields = [
            "id",
            "player",
            "player_detail",
            "fixture",
            "fixture_detail",
            "minutes",
            "goals",
            "assists",
            "shots",
            "shots_on_target",
            "passes",
            "key_passes",
            "tackles",
            "interceptions",
            "yellow_cards",
            "red_cards",
            "rating",
        ]


class TeamStatisticSerializer(serializers.ModelSerializer):
    team_detail = TeamSerializer(source="team", read_only=True)
    fixture_detail = FixtureSerializer(source="fixture", read_only=True)

    class Meta:
        model = TeamStatistic
        fields = [
            "id",
            "team",
            "team_detail",
            "fixture",
            "fixture_detail",
            "possession",
            "shots",
            "shots_on_target",
            "corners",
            "fouls",
            "offsides",
            "yellow_cards",
            "red_cards",
        ]

class CoachSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = (
            'id',
            'external_id',
            'team',
            'name',
            'nationality',
            'photo',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')
