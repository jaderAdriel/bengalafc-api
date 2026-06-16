from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.football.models import Competition
from apps.scores.models import FantasyLineup, ScoreEvent


class Command(BaseCommand):
    help = "Zera pontuacao e escalacoes fantasy para recomecar o fluxo da Copa seedada."

    competition_external_id = 2026001

    def handle(self, *args, **options):
        competition = Competition.objects.filter(
            external_id=self.competition_external_id
        ).first()
        if not competition:
            raise CommandError(
                "Competicao do seed minimo nao encontrada. "
                "Rode seed_minimal_worldcup antes deste comando."
            )

        User = get_user_model()

        with transaction.atomic():
            score_events_deleted, _ = ScoreEvent.objects.filter(
                fixture__competition=competition
            ).delete()
            lineups_queryset = FantasyLineup.objects.filter(
                stage__competition=competition
            )
            lineups_deleted = lineups_queryset.count()
            lineups_queryset.delete()
            users_reset = User.objects.exclude(points=0).update(points=0)

        self.stdout.write(
            self.style.SUCCESS(
                "Fluxo fantasy resetado: "
                f"{users_reset} usuarios, "
                f"{score_events_deleted} eventos de pontuacao removidos, "
                f"{lineups_deleted} escalacoes removidas."
            )
        )
