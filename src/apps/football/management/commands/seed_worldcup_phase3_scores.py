from django.core.management.base import BaseCommand

from ._worldcup_score_seed import WorldCupScoreSeeder


class Command(BaseCommand):
    help = "Pontua a Final, confirma Brasil campeao e finaliza todas as fases."

    def handle(self, *args, **options):
        WorldCupScoreSeeder(self.stdout, self.style).seed_phase(
            phase_name="Final",
            next_phase_name=None,
            finished_at="2026-06-30T23:30:00Z",
            results=[
                (9209, 3, 1),  # Brasil campeao contra Argentina
            ],
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Final pontuada. Brasil campeao. Todas as fases finalizadas."
            )
        )
