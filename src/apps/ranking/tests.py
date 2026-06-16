from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.football.models import Competition, Fixture, Player, PlayerStatistic, Stage, Team
from apps.scores.models import FantasyLineup

User = get_user_model()


class RankingAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='password123',
        )
        self.other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='password123',
            points=999,
        )
        self.team = Team.objects.create(external_id=1, name='Brasil', code='BRA')
        self.opponent = Team.objects.create(external_id=2, name='Argentina', code='ARG')
        self.competition = Competition.objects.create(
            external_id=10,
            name='Copa',
            season=2026,
        )
        self.stage = Stage.objects.create(
            competition=self.competition,
            name='Fase 1',
            order=1,
        )
        self.fixture = Fixture.objects.create(
            external_id=100,
            competition=self.competition,
            stage=self.stage,
            home_team=self.team,
            away_team=self.opponent,
            kickoff_at='2026-06-06T18:00:00Z',
            status='FT',
        )
        self.player_1 = Player.objects.create(
            external_id=101,
            team=self.team,
            name='Atacante 1',
            position='Attacker',
        )
        self.player_2 = Player.objects.create(
            external_id=102,
            team=self.team,
            name='Meia 1',
            position='Midfielder',
        )
        self.client.force_authenticate(user=self.user)

    def test_global_ranking_uses_lineup_score_history_not_user_points(self):
        lineup = FantasyLineup.objects.create(
            user=self.user,
            stage=self.stage,
            captain=self.player_1,
        )
        lineup.players.create(player=self.player_1, order=0)
        lineup.players.create(player=self.player_2, order=1)

        PlayerStatistic.objects.create(
            player=self.player_1,
            fixture=self.fixture,
            goals=1,
            assists=1,
            shots=3,
            shots_on_target=2,
        )
        PlayerStatistic.objects.create(
            player=self.player_2,
            fixture=self.fixture,
            tackles=2,
            yellow_cards=1,
        )

        response = self.client.get(reverse('ranking-global-ranking'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['id'], self.user.id)
        self.assertEqual(response.data[0]['points'], 41.0)
        self.assertEqual(response.data[0]['position'], 1)
        self.assertEqual(response.data[1]['id'], self.other_user.id)
        self.assertEqual(response.data[1]['points'], 0.0)
        self.assertEqual(response.data[1]['position'], 2)
