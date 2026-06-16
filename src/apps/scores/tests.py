from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.football.models import Competition, Fixture, Player, PlayerStatistic, Stage, Team
from apps.scores.models import FantasyLineup, FantasyTransfer

User = get_user_model()


class FantasyLineupAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='password123',
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
        self.player_3 = Player.objects.create(
            external_id=103,
            team=self.team,
            name='Zagueiro 1',
            position='Defender',
        )
        self.outside_team = Team.objects.create(
            external_id=3,
            name='França',
            code='FRA',
        )
        self.outside_player = Player.objects.create(
            external_id=104,
            team=self.outside_team,
            name='Atacante Fora da Fase',
            position='Attacker',
        )
        self.client.force_authenticate(user=self.user)

    def test_create_lineup_for_stage(self):
        response = self.client.post(
            reverse('lineup-list'),
            {
                'stage': self.stage.id,
                'player_ids': [self.player_1.id, self.player_2.id],
                'captain_id': self.player_1.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FantasyLineup.objects.count(), 1)
        self.assertEqual(response.data['captain'], self.player_1.id)
        self.assertEqual(len(response.data['players']), 2)

    def test_create_lineup_rejects_player_outside_stage_teams(self):
        response = self.client.post(
            reverse('lineup-list'),
            {
                'stage': self.stage.id,
                'player_ids': [self.player_1.id, self.outside_player.id],
                'captain_id': self.player_1.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('player_ids', response.data)

    def test_update_lineup_changes_captain_and_records_transfers(self):
        lineup = FantasyLineup.objects.create(
            user=self.user,
            stage=self.stage,
            captain=self.player_1,
        )
        lineup.players.create(player=self.player_1, order=0)
        lineup.players.create(player=self.player_2, order=1)

        response = self.client.patch(
            reverse('lineup-detail', args=[lineup.id]),
            {
                'player_ids': [self.player_2.id, self.player_3.id],
                'captain_id': self.player_3.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lineup.refresh_from_db()
        self.assertEqual(lineup.captain_id, self.player_3.id)
        self.assertEqual(FantasyTransfer.objects.count(), 1)

        transfer = FantasyTransfer.objects.get()
        self.assertEqual(transfer.from_player_id, self.player_1.id)
        self.assertEqual(transfer.to_player_id, self.player_3.id)

    def test_score_history_uses_stage_statistics_and_doubles_captain(self):
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

        response = self.client.get(reverse('lineup-score-history', args=[lineup.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stage'], self.stage.id)
        self.assertEqual(response.data['total_points'], 41.0)
        self.assertEqual(len(response.data['items']), 2)

    def test_phase_score_history_includes_zero_for_stage_without_lineup(self):
        final_stage = Stage.objects.create(
            competition=self.competition,
            name='Final',
            order=2,
            finished_at=timezone.now(),
        )
        lineup = FantasyLineup.objects.create(
            user=self.user,
            stage=self.stage,
            captain=self.player_1,
        )
        lineup.players.create(player=self.player_1, order=0)

        PlayerStatistic.objects.create(
            player=self.player_1,
            fixture=self.fixture,
            goals=1,
        )

        response = self.client.get(
            reverse('lineup-phase-score-history'),
            {'competition': self.competition.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        first_stage = response.data[0]
        self.assertEqual(first_stage['stage'], self.stage.id)
        self.assertTrue(first_stage['has_lineup'])
        self.assertEqual(first_stage['lineup'], lineup.id)
        self.assertEqual(first_stage['total_points'], 16.0)

        final = response.data[1]
        self.assertEqual(final['stage'], final_stage.id)
        self.assertEqual(final['stage_name'], 'Final')
        self.assertFalse(final['has_lineup'])
        self.assertIsNone(final['lineup'])
        self.assertTrue(final['is_finished'])
        self.assertEqual(final['total_points'], 0.0)
        self.assertEqual(final['items'], [])

    def test_transfer_list_can_be_filtered_by_stage(self):
        lineup = FantasyLineup.objects.create(
            user=self.user,
            stage=self.stage,
            captain=self.player_1,
        )
        FantasyTransfer.objects.create(
            user=self.user,
            stage=self.stage,
            lineup=lineup,
            from_player=self.player_1,
            to_player=self.player_2,
        )

        response = self.client.get(reverse('transfer-list'), {'stage': self.stage.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
