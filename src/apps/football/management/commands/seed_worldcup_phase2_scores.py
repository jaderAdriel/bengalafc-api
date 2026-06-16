from django.core.management.base import BaseCommand

from ._worldcup_score_seed import WorldCupScoreSeeder


class Command(BaseCommand):
    help = "Pontua a Semifinal e muda a fase atual para Final."

    def handle(self, *args, **options):
        WorldCupScoreSeeder(self.stdout, self.style).seed_phase(
            phase_name="Semifinal",
            next_phase_name="Final",
            finished_at="2026-06-25T23:30:00Z",
            results=[
                (9207, 2, 0),  # Brasil x Inglaterra
                (9208, 2, 1),  # Argentina x Franca
            ],
        )
        self.stdout.write(
            self.style.SUCCESS("Semifinal pontuada. Fase atual agora: Final.")
        )
