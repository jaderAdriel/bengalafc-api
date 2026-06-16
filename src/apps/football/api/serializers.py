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
        ]


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
