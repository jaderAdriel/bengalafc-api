from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from apps.football.models import (
    Competition,
    Fixture,
    Player,
    PlayerStatistic,
    Stage,
    Team,
    TeamStatistic,
)


class Command(BaseCommand):
    help = "Popula dados minimos de Copa para uso local do app mobile."

    def handle(self, *args, **options):
        competition, _ = Competition.objects.update_or_create(
            external_id=2026001,
            defaults={
                "name": "Copa do Mundo",
                "type": "Cup",
                "season": 2026,
            },
        )

        teams = self._seed_teams()
        stages = self._seed_stages(competition)
        players_count = self._seed_players(teams)
        self._clear_scores(competition)
        fixtures_count = self._seed_fixtures(competition, stages, teams)

        self.stdout.write(
            self.style.SUCCESS(
                "Seed minimo concluido: "
                f"1 competicao, {len(stages)} fases, {len(teams)} selecoes, "
                f"{players_count} jogadores e {fixtures_count} partidas."
            )
        )

    def _seed_teams(self):
        teams_data = [
            {
                "external_id": 9101,
                "name": "Brasil",
                "code": "BRA",
                "country": "Brazil",
                "founded": 1914,
            },
            {
                "external_id": 9102,
                "name": "Argentina",
                "code": "ARG",
                "country": "Argentina",
                "founded": 1893,
            },
            {
                "external_id": 9103,
                "name": "Franca",
                "code": "FRA",
                "country": "France",
                "founded": 1919,
            },
            {
                "external_id": 9104,
                "name": "Inglaterra",
                "code": "ENG",
                "country": "England",
                "founded": 1863,
            },
        ]

        teams = {}
        for data in teams_data:
            team, _ = Team.objects.update_or_create(
                external_id=data["external_id"],
                defaults={
                    "name": data["name"],
                    "code": data["code"],
                    "country": data["country"],
                    "founded": data["founded"],
                    "is_active": True,
                },
            )
            teams[data["code"]] = team
        return teams

    def _clear_scores(self, competition):
        PlayerStatistic.objects.filter(fixture__competition=competition).delete()
        TeamStatistic.objects.filter(fixture__competition=competition).delete()

    def _seed_stages(self, competition):
        stages_data = [
            (
                "Fase de Grupos",
                1,
                "2026-06-11T12:00:00Z",
                "2026-06-11T15:00:00Z",
                "2026-06-19T23:00:00Z",
                True,
            ),
            (
                "Semifinal",
                2,
                "2026-06-25T12:00:00Z",
                "2026-06-25T15:00:00Z",
                "2026-06-25T23:00:00Z",
                False,
            ),
            (
                "Final",
                3,
                "2026-06-30T12:00:00Z",
                "2026-06-30T17:00:00Z",
                "2026-06-30T23:00:00Z",
                False,
            ),
        ]

        stages = {}
        for name, order, starts_at, deadline_at, ends_at, is_current in stages_data:
            stage, _ = Stage.objects.update_or_create(
                competition=competition,
                name=name,
                defaults={
                    "order": order,
                    "starts_at": self._parse_datetime(starts_at),
                    "lineup_deadline_at": self._parse_datetime(deadline_at),
                    "ends_at": self._parse_datetime(ends_at),
                    "finished_at": None,
                    "is_current": is_current,
                },
            )
            stages[name] = stage
        return stages

    def _seed_players(self, teams):
        players_by_team = {
            "BRA": [
                ("Alisson", "GK", 1),
                ("Danilo", "DF", 2),
                ("Marquinhos", "DF", 3),
                ("Gabriel Magalhaes", "DF", 4),
                ("Guilherme Arana", "DF", 6),
                ("Casemiro", "MF", 5),
                ("Bruno Guimaraes", "MF", 8),
                ("Lucas Paqueta", "MF", 10),
                ("Vinicius Junior", "FW", 7),
                ("Rodrygo", "FW", 11),
                ("Richarlison", "FW", 9),
            ],
            "ARG": [
                ("Emiliano Martinez", "GK", 23),
                ("Nahuel Molina", "DF", 2),
                ("Cristian Romero", "DF", 13),
                ("Nicolas Otamendi", "DF", 19),
                ("Nicolas Tagliafico", "DF", 3),
                ("Rodrigo De Paul", "MF", 7),
                ("Enzo Fernandez", "MF", 24),
                ("Alexis Mac Allister", "MF", 20),
                ("Lionel Messi", "FW", 10),
                ("Julian Alvarez", "FW", 9),
                ("Lautaro Martinez", "FW", 22),
            ],
            "FRA": [
                ("Mike Maignan", "GK", 16),
                ("Jules Kounde", "DF", 5),
                ("William Saliba", "DF", 17),
                ("Ibrahima Konate", "DF", 13),
                ("Theo Hernandez", "DF", 22),
                ("Aurelien Tchouameni", "MF", 8),
                ("Eduardo Camavinga", "MF", 6),
                ("Adrien Rabiot", "MF", 14),
                ("Kylian Mbappe", "FW", 10),
                ("Ousmane Dembele", "FW", 11),
                ("Antoine Griezmann", "FW", 7),
            ],
            "ENG": [
                ("Jordan Pickford", "GK", 1),
                ("Kyle Walker", "DF", 2),
                ("John Stones", "DF", 5),
                ("Harry Maguire", "DF", 6),
                ("Luke Shaw", "DF", 3),
                ("Declan Rice", "MF", 4),
                ("Jude Bellingham", "MF", 10),
                ("Phil Foden", "MF", 11),
                ("Bukayo Saka", "FW", 7),
                ("Harry Kane", "FW", 9),
                ("Marcus Rashford", "FW", 19),
            ],
        }

        count = 0
        for team_code, players in players_by_team.items():
            team = teams[team_code]
            base_external_id = team.external_id * 100
            for index, (name, position, number) in enumerate(players, start=1):
                Player.objects.update_or_create(
                    external_id=base_external_id + index,
                    defaults={
                        "team": team,
                        "name": name,
                        "nationality": team.country,
                        "position": position,
                        "number": number,
                        "is_active": True,
                    },
                )
                count += 1
        return count

    def _seed_fixtures(self, competition, stages, teams):
        fixtures_data = [
            (9201, "Fase de Grupos", "BRA", "ARG", "2026-06-11T16:00:00Z"),
            (9202, "Fase de Grupos", "FRA", "ENG", "2026-06-11T19:00:00Z"),
            (9203, "Fase de Grupos", "BRA", "FRA", "2026-06-15T16:00:00Z"),
            (9204, "Fase de Grupos", "ARG", "ENG", "2026-06-15T19:00:00Z"),
            (9205, "Fase de Grupos", "BRA", "ENG", "2026-06-19T16:00:00Z"),
            (9206, "Fase de Grupos", "ARG", "FRA", "2026-06-19T19:00:00Z"),
            (9207, "Semifinal", "BRA", "ENG", "2026-06-25T16:00:00Z"),
            (9208, "Semifinal", "ARG", "FRA", "2026-06-25T19:00:00Z"),
            (9209, "Final", "BRA", "ARG", "2026-06-30T18:00:00Z"),
        ]

        for external_id, stage_name, home, away, kickoff_at in fixtures_data:
            Fixture.objects.update_or_create(
                external_id=external_id,
                defaults={
                    "competition": competition,
                    "stage": stages[stage_name],
                    "home_team": teams[home],
                    "away_team": teams[away],
                    "kickoff_at": self._parse_datetime(kickoff_at),
                    "status": "NS",
                    "home_score": None,
                    "away_score": None,
                    "venue": "Bengala FC Stadium",
                },
            )
        return len(fixtures_data)

    def _parse_datetime(self, value):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
