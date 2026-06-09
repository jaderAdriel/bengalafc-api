import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from apps.football.models import Team, Fixture, TeamStatistic, Stage, Competition


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
    help = "Importa estatísticas de equipes por fase"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)
        parser.add_argument("--stage", type=str, required=True)

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])
        stage_filter = options["stage"].strip()
        competition = Competition.objects.get(external_id=999)
        stage = Stage.objects.get(competition=competition, name=stage_filter)

        seen = set()

        with csv_path.open("r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if not row["date"].strip() or not row["opponent"].strip():
                    continue

                if normalize_stage(row["category"]) != stage_filter:
                    continue

                team1_name = row["Team"].strip().title()
                team2_name = row["opponent"].strip().title()
                key = (team1_name, team2_name, row["date"].strip())

                if key in seen:
                    continue
                seen.add(key)

                fixture_key = f"{team1_name}_{team2_name}_{row['date'].strip()}"
                fixture = Fixture.objects.filter(
                    external_id=hash(fixture_key) % 1000000
                ).first()

                if not fixture:
                    self.stderr.write(f"Partida não encontrada: {team1_name} x {team2_name}. Rode import_fixtures antes.")
                    continue

                team = Team.objects.filter(name=team1_name).first()
                if not team:
                    continue

                TeamStatistic.objects.update_or_create(
                    team=team,
                    fixture=fixture,
                    defaults={
                        "possession": 0,
                        "shots": pi(row["Shots"]),
                        "shots_on_target": pi(row["shots_on_target"]),
                        "corners": 0,
                        "fouls": pi(row["fouls_commited"]),
                        "offsides": pi(row["offside"]),
                        "yellow_cards": pi(row["CrdY"]),
                        "red_cards": pi(row["CrdR"]),
                    },
                )

                self.stdout.write(self.style.SUCCESS(f"Stats: {team1_name} x {team2_name}"))