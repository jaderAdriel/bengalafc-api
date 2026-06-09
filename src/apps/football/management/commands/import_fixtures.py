import csv
from pathlib import Path
from datetime import datetime
from django.core.management.base import BaseCommand
from apps.football.models import Team, Competition, Stage, Fixture
from django.utils.timezone import make_aware


def normalize_stage(category):
    if category.strip().startswith("Group"):
        return "Fase de Grupos"
    return category.strip()


class Command(BaseCommand):
    help = "Importa competição, fases, times e partidas do CSV combinado"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str)

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])

        competition, _ = Competition.objects.get_or_create(
            external_id=999,
            defaults={"name": "FIFA World Cup", "season": 2022, "type": "World Cup"},
        )

        seen = set()

        with csv_path.open("r", encoding="utf-8-sig") as f:
            for idx, row in enumerate(csv.DictReader(f), start=1):
                if not row["date"].strip() or not row["opponent"].strip():
                    continue

                key = (row["Team"].strip(), row["opponent"].strip(), row["date"].strip())
                if key in seen:
                    continue
                seen.add(key)

                team1_name = row["Team"].strip().title()
                team2_name = row["opponent"].strip().title()

                team1, _ = Team.objects.get_or_create(
                    external_id=hash(team1_name) % 100000,
                    defaults={"name": team1_name, "country": team1_name},
                )
                team2, _ = Team.objects.get_or_create(
                    external_id=hash(team2_name) % 100000,
                    defaults={"name": team2_name, "country": team2_name},
                )

                stage_name = normalize_stage(row["category"])
                stage, _ = Stage.objects.get_or_create(
                    competition=competition,
                    name=stage_name,
                )

                try:
                    kickoff_at = make_aware(datetime.strptime(
                        f"{row['date'].strip()} {row['hour'].strip().replace(' ', '')}",
                        "%d %b %Y %H:%M"
                    ))
                except ValueError:
                    kickoff_at = make_aware(datetime.strptime(row["date"].strip(), "%d %b %Y"))

                fixture_key = f"{team1_name}_{team2_name}_{row['date'].strip()}"
                fixture, created = Fixture.objects.get_or_create(
                    external_id=hash(fixture_key) % 1000000,
                    defaults={
                        "competition": competition,
                        "stage": stage,
                        "home_team": team1,
                        "away_team": team2,
                        "kickoff_at": kickoff_at,
                        "status": "FT",
                        "home_score": 0,
                        "away_score": 0,
                    },
                )

                action = "Criada" if created else "Já existe"
                self.stdout.write(self.style.SUCCESS(
                    f"{action}: {team1_name} x {team2_name} ({stage_name})"
                ))