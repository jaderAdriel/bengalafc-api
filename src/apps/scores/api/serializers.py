from rest_framework import serializers
from apps.football.models import Player as FootballPlayer
from apps.football.api.serializers import PlayerSerializer as FootballPlayerSerializer
from ..models import (
    FantasyLineup,
    FantasyLineupPlayer,
    FantasyTransfer,
    Player,
    ScoreEvent,
)
from apps.football.models import Coach as FootballCoach
from apps.football.models import Fixture

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ('id', 'position', 'football_player', 'user')
        read_only_fields = ('user',)


class ScoreEventSerializer(serializers.ModelSerializer):
    event_display = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = ScoreEvent
        fields = ('id', 'event_type', 'event_display', 'points', 'fixture', 'created_at')
        read_only_fields = ('points',)


class AddScoreEventSerializer(serializers.Serializer):
    event_type = serializers.CharField()
    fixture = serializers.IntegerField(required=False)


class FantasyLineupPlayerSerializer(serializers.ModelSerializer):
    player_detail = FootballPlayerSerializer(source='player', read_only=True)

    class Meta:
        model = FantasyLineupPlayer
        fields = ('id', 'player', 'player_detail', 'order', 'created_at')
        read_only_fields = ('id', 'player_detail', 'created_at')


class FantasyLineupSerializer(serializers.ModelSerializer):
    players = FantasyLineupPlayerSerializer(many=True, read_only=True)
    player_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        allow_empty=False
    )
    captain_id = serializers.IntegerField(write_only=True)
    captain_detail = FootballPlayerSerializer(source='captain', read_only=True)
    coach_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    coach_detail = serializers.SerializerMethodField(read_only=True)

    def get_coach_detail(self, obj):
        if obj.coach:
            return {'id': obj.coach.id, 'name': obj.coach.name, 'photo': obj.coach.photo}
        return None

    class Meta:
        model = FantasyLineup
        fields = (
            'id',
            'stage',
            'captain',
            'captain_id',
            'captain_detail',
            'coach',
            'coach_id',
            'coach_detail',
            'players',
            'player_ids',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'captain', 'captain_detail', 'coach', 'coach_detail', 'players', 'created_at', 'updated_at')

    def validate_player_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError('A escalação não pode ter jogadores repetidos.')

        found_count = FootballPlayer.objects.filter(id__in=value).count()
        if found_count != len(value):
            raise serializers.ValidationError('Um ou mais jogadores informados não existem.')

        return value

    def validate(self, attrs):
        player_ids = attrs.get('player_ids')
        captain_id = attrs.get('captain_id')
        coach_id = attrs.get('coach_id')
        request = self.context.get('request')
        stage = attrs.get('stage')

        if coach_id and not FootballCoach.objects.filter(id=coach_id).exists():
            raise serializers.ValidationError({'coach_id': 'Técnico não encontrado.'})

        if self.instance:
            current_player_ids = list(self.instance.players.values_list('player_id', flat=True))
            player_ids = player_ids if player_ids is not None else current_player_ids
            captain_id = captain_id if captain_id is not None else self.instance.captain_id
            stage = stage if stage is not None else self.instance.stage
            coach_id = coach_id if coach_id is not None else self.instance.coach_id
        elif request and FantasyLineup.objects.filter(user=request.user, stage=stage).exists():
            raise serializers.ValidationError({'stage': 'Você já possui escalação para esta fase.'})

        if player_ids and captain_id not in player_ids:
            raise serializers.ValidationError({'captain_id': 'O capitão precisa estar na escalação.'})

        if stage is not None:
            allowed_team_ids = self._stage_team_ids(stage.id)
            if allowed_team_ids:
                invalid_players = FootballPlayer.objects.filter(
                    id__in=player_ids,
                ).exclude(team_id__in=allowed_team_ids)
                if invalid_players.exists():
                    names = ', '.join(
                        invalid_players.order_by('name').values_list('name', flat=True)
                    )
                    raise serializers.ValidationError({
                        'player_ids': (
                            'A escalação só pode ter jogadores das seleções '
                            f'que jogam nesta fase. Fora da fase: {names}.'
                        )
                    })

                if coach_id:
                    coach_in_stage = FootballCoach.objects.filter(
                        id=coach_id,
                        team_id__in=allowed_team_ids,
                    ).exists()
                    if not coach_in_stage:
                        raise serializers.ValidationError({
                            'coach_id': 'O técnico precisa ser de uma seleção que joga nesta fase.'
                        })

        return attrs

    def _stage_team_ids(self, stage_id):
        team_ids = set()
        fixtures = Fixture.objects.filter(stage_id=stage_id).values_list(
            'home_team_id',
            'away_team_id',
        )
        for home_team_id, away_team_id in fixtures:
            if home_team_id:
                team_ids.add(home_team_id)
            if away_team_id:
                team_ids.add(away_team_id)
        return team_ids

    def create(self, validated_data):
        player_ids = validated_data.pop('player_ids')
        captain_id = validated_data.pop('captain_id')
        coach_id = validated_data.pop('coach_id', None)
        lineup = FantasyLineup.objects.create(
            user=self.context['request'].user,
            captain_id=captain_id,
            coach_id=coach_id,
            **validated_data
        )
        self._set_players(lineup, player_ids)
        return lineup

    def update(self, instance, validated_data):
        player_ids = validated_data.pop('player_ids', None)
        captain_id = validated_data.pop('captain_id', None)
        coach_id = validated_data.pop('coach_id', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if captain_id is not None:
            instance.captain_id = captain_id
        if coach_id is not None:
            instance.coach_id = coach_id
        instance.save()

        if player_ids is not None:
            old_ids = list(instance.players.values_list('player_id', flat=True))
            self._set_players(instance, player_ids)
            self._record_transfers(instance, old_ids, player_ids)

        return instance

    def _set_players(self, lineup, player_ids):
        lineup.players.all().delete()
        FantasyLineupPlayer.objects.bulk_create([
            FantasyLineupPlayer(lineup=lineup, player_id=player_id, order=index)
            for index, player_id in enumerate(player_ids)
        ])

    def _record_transfers(self, lineup, old_ids, new_ids):
        removed_ids = [player_id for player_id in old_ids if player_id not in new_ids]
        added_ids = [player_id for player_id in new_ids if player_id not in old_ids]
        transfer_count = max(len(removed_ids), len(added_ids))

        FantasyTransfer.objects.bulk_create([
            FantasyTransfer(
                user=lineup.user,
                stage=lineup.stage,
                lineup=lineup,
                from_player_id=removed_ids[index] if index < len(removed_ids) else None,
                to_player_id=added_ids[index] if index < len(added_ids) else None,
            )
            for index in range(transfer_count)
        ])


class FantasyTransferSerializer(serializers.ModelSerializer):
    from_player_detail = FootballPlayerSerializer(source='from_player', read_only=True)
    to_player_detail = FootballPlayerSerializer(source='to_player', read_only=True)

    class Meta:
        model = FantasyTransfer
        fields = (
            'id',
            'stage',
            'lineup',
            'from_player',
            'from_player_detail',
            'to_player',
            'to_player_detail',
            'created_at',
        )
        read_only_fields = fields
