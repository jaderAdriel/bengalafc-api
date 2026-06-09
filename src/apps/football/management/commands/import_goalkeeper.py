import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from apps.football.models import Team, Player, PlayerStatistic, Fixture, Stage, Competition


class Command(BaseCommand):
    help = "Importa saves e gols sofridos dos goleiros da Copa 2022"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)
        parser.add_argument("--stage", type=str, required=True)

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])
        stage_filter = options["stage"].strip()
        imported = 0

        competition = Competition.objects.get(external_id=999)
        stage = Stage.objects.get(competition=competition, name=stage_filter)

        with csv_path.open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                player_name = row["player_name"].strip()
                team_name = row["team_name"].strip()
                saves = int(row["saves"])
                goals_conceded = int(row["goals_against"])

                team = Team.objects.filter(name=team_name).first()
                if not team:
                    self.stderr.write(f"Time não encontrado: {team_name}")
                    continue

                player = Player.objects.filter(name=player_name, team=team).first()
                if not player:
                    self.stderr.write(f"Goleiro não encontrado: {player_name}")
                    continue

                fixtures = Fixture.objects.filter(
                    stage=stage, home_team=team
                ) | Fixture.objects.filter(
                    stage=stage, away_team=team
                )

                stats = PlayerStatistic.objects.filter(
                    player=player, fixture__in=fixtures
                )

                if not stats.exists():
                    self.stderr.write(f"Nenhuma estatística encontrada para: {player_name}")
                    continue

                total_fixtures = stats.count()
                saves_per_game = saves // total_fixtures
                goals_per_game = goals_conceded // total_fixtures

                for i, stat in enumerate(stats):
                    extra = i == total_fixtures - 1
                    stat.saves = saves_per_game + (saves % total_fixtures if extra else 0)
                    stat.goals_conceded = goals_per_game + (goals_conceded % total_fixtures if extra else 0)
                    stat.save()
                    imported += 1

        self.stdout.write(self.style.SUCCESS(f"\nConcluído: {imported} registros atualizados."))