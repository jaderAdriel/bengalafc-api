from django.core.management.base import BaseCommand
from apps.football.models import Competition, Team, Stage, Fixture, TeamStatistic

class Command(BaseCommand):
    help = "Remove todos os dados importados da Copa do Mundo"

    def handle(self, *args, **options):
        TeamStatistic.objects.all().delete()
        Fixture.objects.all().delete()
        Stage.objects.all().delete()
        Team.objects.all().delete()
        Competition.objects.filter(external_id=999).delete()
        self.stdout.write(self.style.SUCCESS("Dados removidos com sucesso!"))