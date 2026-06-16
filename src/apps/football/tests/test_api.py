from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from apps.football.models import (
    Competition,
    Fixture,
    Player,
    Stage,
    Team,
)

User = get_user_model()


class FootballAPITestCase(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testadmin", password="password123"
        )
        self.team = Team.objects.create(
            external_id=26, name="Argentina", code="ARG"
        )
        self.competition = Competition.objects.create(
            external_id=1, name="World Cup", season=2022
        )
        self.stage = Stage.objects.create(
            competition=self.competition, name="Final", order=50
        )
        self.fixture = Fixture.objects.create(
            external_id=855735,
            competition=self.competition,
            stage=self.stage,
            home_team=self.team,
            away_team=self.team,
            kickoff_at="2022-12-18T15:00:00Z",
            status="FT",
        )
        self.player = Player.objects.create(
            external_id=154, name="Lionel Messi", team=self.team
        )

    def test_players_can_be_filtered_by_stage_teams(self) -> None:
        outside_team = Team.objects.create(
            external_id=55, name="Brazil", code="BRA"
        )
        outside_player = Player.objects.create(
            external_id=999,
            name="Outside Player",
            team=outside_team,
            position="Attacker",
        )

        response = self.client.get(reverse("player-list"), {"stage": self.stage.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        player_ids = {item["id"] for item in response.data}
        self.assertIn(self.player.id, player_ids)
        self.assertNotIn(outside_player.id, player_ids)

    def test_get_endpoints_anonymous(self) -> None:
        """Verifica que usuários não autenticados conseguem listar dados (Read-Only)."""
        endpoints = [
            "team-list",
            "player-list",
            "competition-list",
            "stage-list",
            "fixture-list",
            "player-statistic-list",
            "team-statistic-list",
        ]
        for url_name in endpoints:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_endpoints_require_auth(self) -> None:
        """Verifica que requisições POST falham sem autenticação (IsAuthenticatedOrReadOnly)."""
        url = reverse("team-list")
        data = {
            "external_id": 2,
            "name": "France",
            "code": "FRA",
            "country": "France",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_team(self) -> None:
        """Verifica criação de equipes com usuário autenticado."""
        url = reverse("team-list")
        data = {
            "external_id": 2,
            "name": "France",
            "code": "FRA",
            "country": "France",
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Team.objects.filter(external_id=2).count(), 1)

    def test_create_player(self) -> None:
        """Verifica criação de jogadores com usuário autenticado."""
        url = reverse("player-list")
        data = {
            "external_id": 222,
            "name": "Kylian Mbappé",
            "team": self.team.id,
            "position": "Attacker",
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Player.objects.filter(external_id=222).count(), 1)

    def test_create_stage(self) -> None:
        """Verifica criação de fases de competição."""
        url = reverse("stage-list")
        data = {
            "competition": self.competition.id,
            "name": "Semifinal",
            "order": 40,
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Stage.objects.filter(competition=self.competition, name="Semifinal").count(),
            1,
        )

    def test_stage_state_returns_sequence_for_current_competition(self) -> None:
        group_stage = Stage.objects.create(
            competition=self.competition,
            name="Fase de Grupos",
            order=10,
            finished_at=timezone.now(),
        )
        semifinal = Stage.objects.create(
            competition=self.competition,
            name="Semifinal",
            order=20,
            is_current=True,
        )
        self.stage.order = 30
        self.stage.name = "Final"
        self.stage.save(update_fields=["order", "name"])

        response = self.client.get(reverse("stage-state"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["competition_finished"])
        self.assertEqual(response.data["current_stage"]["id"], semifinal.id)
        self.assertEqual(response.data["previous_stage"]["id"], group_stage.id)
        self.assertEqual(response.data["next_stage"]["id"], self.stage.id)
        self.assertEqual(response.data["last_stage"]["id"], self.stage.id)
        self.assertFalse(response.data["last_stage"]["is_finished"])
        self.assertTrue(response.data["last_stage"]["is_last_stage"])

    def test_stage_state_marks_competition_finished_after_last_stage(self) -> None:
        finished_at = timezone.now()
        self.stage.order = 30
        self.stage.finished_at = finished_at
        self.stage.is_current = False
        self.stage.save(update_fields=["order", "finished_at", "is_current"])
        Stage.objects.create(
            competition=self.competition,
            name="Fase de Grupos",
            order=10,
            finished_at=finished_at,
        )
        Stage.objects.create(
            competition=self.competition,
            name="Semifinal",
            order=20,
            finished_at=finished_at,
        )

        response = self.client.get(
            reverse("stage-state"), {"competition": self.competition.id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["competition_finished"])
        self.assertIsNone(response.data["current_stage"])
        self.assertIsNone(response.data["next_stage"])
        self.assertEqual(response.data["previous_stage"]["id"], self.stage.id)
        self.assertTrue(response.data["previous_stage"]["is_finished"])

    def test_create_fixture(self) -> None:
        """Verifica criação de partidas."""
        url = reverse("fixture-list")
        data = {
            "external_id": 99999,
            "competition": self.competition.id,
            "stage": self.stage.id,
            "home_team": self.team.id,
            "away_team": self.team.id,
            "kickoff_at": "2026-06-06T18:00:00Z",
            "status": "NS",
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Fixture.objects.filter(external_id=99999).count(), 1)
