from django.core.management.base import BaseCommand

from ._worldcup_score_seed import WorldCupScoreSeeder


class Command(BaseCommand):
    help = "Pontua a Fase de Grupos e muda a fase atual para Semifinal."

    def handle(self, *args, **options):
        WorldCupScoreSeeder(self.stdout, self.style).seed_phase(
            phase_name="Fase de Grupos",
            next_phase_name="Semifinal",
            finished_at="2026-06-19T23:30:00Z",
            results=[
                (9201, 2, 1),  # Brasil x Argentina
                (9202, 1, 1),  # Franca x Inglaterra
                (9203, 3, 1),  # Brasil x Franca
                (9204, 2, 0),  # Argentina x Inglaterra
                (9205, 1, 0),  # Brasil x Inglaterra
                (9206, 2, 1),  # Argentina x Franca
            ],
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Fase de Grupos pontuada. Fase atual agora: Semifinal."
            )
        )
