from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Player(models.Model):
    POSITION_CHOICES = [
        ('goleiro', 'Goleiro'),
        ('zagueiro', 'Zagueiro'),
        ('lateral', 'Lateral'),
        ('meia', 'Meia'),
        ('atacante', 'Atacante'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player_profile')
    position = models.CharField(max_length=10, choices=POSITION_CHOICES)

    # Liga o jogador do usuário ao jogador real da API de futebol
    football_player = models.ForeignKey(
        'football.Player',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fantasy_players',
        verbose_name='Jogador Real'
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_position_display()}"


class ScoreEvent(models.Model):
    EVENT_CHOICES = [
        ('grande_defesa', 'Grande defesa'),
        ('jogo_sem_sofrer_gol', 'Jogo sem sofrer gol'),
        ('gols_sofridos', 'Gols sofridos'),
        ('cartao_amarelo', 'Cartão Amarelo'),
        ('cartao_vermelho', 'Cartão Vermelho'),
        ('gol', 'Gol'),
        ('assistencia', 'Assistência'),
        ('desarme', 'Desarme'),
        ('finalizacao_fora', 'Finalização (fora/trave)'),
        ('finalizacao_alvo', 'Finalização no alvo'),
    ]

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='score_events')
    event_type = models.CharField(max_length=25, choices=EVENT_CHOICES)
    points = models.DecimalField(max_digits=5, decimal_places=2)
    # Agora guarda a referência direta à partida real
    fixture = models.ForeignKey(
        'football.Fixture',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Partida'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Evita processar a mesma partida duas vezes
        unique_together = ('player', 'event_type', 'fixture')

    def __str__(self):
        return f"{self.player.user.username} - {self.get_event_type_display()} ({self.points}pts)"


class FantasyLineup(models.Model):
    """Escalacao de um usuario para uma fase da competicao."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fantasy_lineups')
    stage = models.ForeignKey(
        'football.Stage',
        on_delete=models.CASCADE,
        related_name='fantasy_lineups',
        verbose_name='Fase'
    )
    captain = models.ForeignKey(
        'football.Player',
        on_delete=models.PROTECT,
        related_name='captain_lineups',
        verbose_name='Capitao'
    )
    coach = models.ForeignKey(
        'football.Coach',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fantasy_lineups',
        verbose_name='Técnico'
    )
    final_points = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Pontuação final',
    )
    finalized_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Finalizada em',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'stage')
        ordering = ('stage__order', 'stage__name')
        verbose_name = 'Escalacao'
        verbose_name_plural = 'Escalacoes'

    def __str__(self):
        return f"{self.user.username} - {self.stage.name}"


class FantasyLineupPlayer(models.Model):
    lineup = models.ForeignKey(FantasyLineup, on_delete=models.CASCADE, related_name='players')
    player = models.ForeignKey(
        'football.Player',
        on_delete=models.PROTECT,
        related_name='fantasy_lineup_entries',
        verbose_name='Jogador'
    )
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lineup', 'player')
        ordering = ('order', 'id')
        verbose_name = 'Jogador escalado'
        verbose_name_plural = 'Jogadores escalados'

    def __str__(self):
        return f"{self.player.name} em {self.lineup}"


class FantasyTransfer(models.Model):
    """Historico de troca feita em uma escalação de fase."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fantasy_transfers')
    stage = models.ForeignKey(
        'football.Stage',
        on_delete=models.CASCADE,
        related_name='fantasy_transfers',
        verbose_name='Fase'
    )
    lineup = models.ForeignKey(FantasyLineup, on_delete=models.CASCADE, related_name='transfers')
    from_player = models.ForeignKey(
        'football.Player',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fantasy_transfers_out',
        verbose_name='Saiu'
    )
    to_player = models.ForeignKey(
        'football.Player',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fantasy_transfers_in',
        verbose_name='Entrou'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at', '-id')
        verbose_name = 'Troca'
        verbose_name_plural = 'Trocas'

    def __str__(self):
        return f"{self.user.username} - {self.stage.name}"
