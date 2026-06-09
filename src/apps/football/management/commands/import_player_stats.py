import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from apps.football.models import Team, Fixture, Player, PlayerStatistic, Stage, Competition


def pi(val, default=0):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def normalize_stage(category):
    if category.strip().startswith("Group"):
        return "Fase de Grupos"
    return category.strip()


class Command(BaseCommand):
    help = "Importa estatísticas de jogadores por fase"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)
        parser.add_argument("--stage", type=str, required=True)

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])
        stage_filter = options["stage"].strip()
        competition = Competition.objects.get(external_id=999)
        stage = Stage.objects.get(competition=competition, name=stage_filter)

        imported = 0

        with csv_path.open("r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if not row["date"].strip() or not row["opponent"].strip():
                    continue

                if normalize_stage(row["category"]) != stage_filter:
                    continue

                team_name = row["Team"].strip().title()
                opponent_name = row["opponent"].strip().title()
                player_name = row["Player"].strip()

                team = Team.objects.filter(name=team_name).first()
                if not team:
                    continue

                fixture = (
                    Fixture.objects.filter(
                        home_team__name=team_name,
                        away_team__name=opponent_name,
                    ).first()
                    or Fixture.objects.filter(
                        home_team__name=opponent_name,
                        away_team__name=team_name,
                    ).first()
                )

                if not fixture:
                    self.stderr.write(f"Partida não encontrada: {team_name} x {opponent_name}")
                    continue

                player, _ = Player.objects.get_or_create(
                    external_id=abs(hash(player_name + team_name)) % 1000000,
                    defaults={
                        "name": player_name,
                        "team": team,
                        "position": row["Pos"].strip() if row["Pos"] else None,
                        "nationality": team_name,
                    },
                )

                PlayerStatistic.objects.update_or_create(
                    player=player,
                    fixture=fixture,
                    defaults={
                        "minutes": pi(row["Minutes_played"]),
                        "goals": pi(row["Gls"]),
                        "assists": pi(row["Ast"]),
                        "shots": pi(row["Shots"]),
                        "shots_on_target": pi(row["shots_on_target"]),
                        "passes": pi(row["pass_comp"]),
                        "key_passes": 0,
                        "tackles": pi(row["tackles_made"]),
                        "interceptions": pi(row["interceptions"]),
                        "yellow_cards": pi(row["CrdY"]),
                        "red_cards": pi(row["CrdR"]),
                    },
                )

                imported += 1

        self.stdout.write(self.style.SUCCESS(f"\nConcluído: {imported} registros importados."))