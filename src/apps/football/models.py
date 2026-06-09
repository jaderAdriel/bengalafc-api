from django.db import models


class Team(models.Model):
    """Representa uma seleção/equipe de futebol."""

    external_id = models.IntegerField(
        unique=True, db_index=True, verbose_name="ID Externo"
    )
    name = models.CharField(max_length=255, verbose_name="Nome")
    code = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="Código"
    )
    country = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="País"
    )
    logo = models.URLField(max_length=500, null=True, blank=True, verbose_name="Logo")
    founded = models.IntegerField(null=True, blank=True, verbose_name="Fundado em")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Seleção"
        verbose_name_plural = "Seleções"

    def __str__(self) -> str:
        return self.name


class Player(models.Model):
    """Representa um jogador."""

    external_id = models.IntegerField(
        unique=True, db_index=True, verbose_name="ID Externo"
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="players",
        null=True,
        blank=True,
        verbose_name="Seleção",
    )
    name = models.CharField(max_length=255, verbose_name="Nome")
    firstname = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Primeiro Nome"
    )
    lastname = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Sobrenome"
    )
    age = models.IntegerField(null=True, blank=True, verbose_name="Idade")
    nationality = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Nacionalidade"
    )
    height = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Altura"
    )
    weight = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Peso"
    )
    photo = models.URLField(max_length=500, null=True, blank=True, verbose_name="Foto")
    position = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Posição"
    )
    number = models.IntegerField(null=True, blank=True, verbose_name="Número da Camisa")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Jogador"
        verbose_name_plural = "Jogadores"

    def __str__(self) -> str:
        return self.name


class Competition(models.Model):
    """Representa um torneio/competição."""

    external_id = models.IntegerField(
        unique=True, db_index=True, verbose_name="ID Externo"
    )
    name = models.CharField(max_length=255, verbose_name="Nome")
    type = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Tipo"
    )
    logo = models.URLField(max_length=500, null=True, blank=True, verbose_name="Logo")
    season = models.IntegerField(verbose_name="Temporada")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Campeonato"
        verbose_name_plural = "Campeonatos"

    def __str__(self) -> str:
        return f"{self.name} ({self.season})"


class Stage(models.Model):
    """Representa fases da competição (ex: Grupo A, Oitavas, Final)."""

    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name="stages",
        verbose_name="Campeonato",
    )
    name = models.CharField(max_length=255, verbose_name="Nome da Fase")
    order = models.IntegerField(default=0, verbose_name="Ordem de Exibição")

    class Meta:
        unique_together = ("competition", "name")
        ordering = ["order", "name"]
        verbose_name = "Fase"
        verbose_name_plural = "Fases"

    def __str__(self) -> str:
        return f"{self.name} - {self.competition.name}"


class Fixture(models.Model):
    """Representa uma partida."""

    external_id = models.IntegerField(
        unique=True, db_index=True, verbose_name="ID Externo"
    )
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name="fixtures",
        verbose_name="Campeonato",
    )
    stage = models.ForeignKey(
        Stage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fixtures",
        verbose_name="Fase",
    )
    home_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="home_fixtures",
        verbose_name="Time Mandante",
    )
    away_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="away_fixtures",
        verbose_name="Time Visitante",
    )
    kickoff_at = models.DateTimeField(verbose_name="Data/Hora do Kickoff")
    status = models.CharField(max_length=50, verbose_name="Status")
    home_score = models.IntegerField(
        null=True, blank=True, verbose_name="Placar Mandante"
    )
    away_score = models.IntegerField(
        null=True, blank=True, verbose_name="Placar Visitante"
    )
    venue = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Estádio/Local"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Partida"
        verbose_name_plural = "Partidas"

    def __str__(self) -> str:
        return f"{self.home_team} vs {self.away_team} ({self.status})"


class PlayerStatistic(models.Model):
    """Estatísticas de um jogador em uma partida específica."""

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="statistics",
        verbose_name="Jogador",
    )
    fixture = models.ForeignKey(
        Fixture,
        on_delete=models.CASCADE,
        related_name="player_statistics",
        verbose_name="Partida",
    )

    minutes = models.IntegerField(default=0, verbose_name="Minutos Jogados")
    goals = models.IntegerField(default=0, verbose_name="Gols")
    assists = models.IntegerField(default=0, verbose_name="Assistências")
    shots = models.IntegerField(default=0, verbose_name="Chutes")
    shots_on_target = models.IntegerField(
        default=0, verbose_name="Chutes no Gol"
    )
    goals_conceded = models.IntegerField(default=0, verbose_name="Gols Sofridos")
    saves = models.IntegerField(default=0, verbose_name="Defesas")
    passes = models.IntegerField(default=0, verbose_name="Passes")
    key_passes = models.IntegerField(default=0, verbose_name="Passes Decisivos")
    tackles = models.IntegerField(default=0, verbose_name="Desarmes")
    interceptions = models.IntegerField(default=0, verbose_name="Interceptações")
    yellow_cards = models.IntegerField(default=0, verbose_name="Cartões Amarelos")
    red_cards = models.IntegerField(default=0, verbose_name="Cartões Vermelhos")
    rating = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True, verbose_name="Nota"
    )

    class Meta:
        unique_together = ("player", "fixture")
        verbose_name = "Estatística de Jogador"
        verbose_name_plural = "Estatísticas de Jogadores"

    def __str__(self) -> str:
        return f"{self.player.name} @ {self.fixture}"


class TeamStatistic(models.Model):
    """Estatísticas de uma equipe em uma partida específica."""

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="statistics",
        verbose_name="Equipe",
    )
    fixture = models.ForeignKey(
        Fixture,
        on_delete=models.CASCADE,
        related_name="team_statistics",
        verbose_name="Partida",
    )

    possession = models.IntegerField(
        default=0, verbose_name="Posse de Bola (%)"
    )
    shots = models.IntegerField(default=0, verbose_name="Chutes Totais")
    shots_on_target = models.IntegerField(
        default=0, verbose_name="Chutes no Alvo"
    )
    corners = models.IntegerField(default=0, verbose_name="Escanteios")
    fouls = models.IntegerField(default=0, verbose_name="Faltas")
    offsides = models.IntegerField(default=0, verbose_name="Impedimentos")
    yellow_cards = models.IntegerField(default=0, verbose_name="Cartões Amarelos")
    red_cards = models.IntegerField(default=0, verbose_name="Cartões Vermelhos")

    class Meta:
        unique_together = ("team", "fixture")
        verbose_name = "Estatística de Equipe"
        verbose_name_plural = "Estatísticas de Equipes"

    def __str__(self) -> str:
        return f"{self.team.name} @ {self.fixture}"

class Coach(models.Model):
    """Representa o técnico de uma equipe."""

    external_id = models.IntegerField(
        unique=True, db_index=True, verbose_name="ID Externo"
    )
    team = models.OneToOneField(
        Team,
        on_delete=models.CASCADE,
        related_name="coach",
        null=True,
        blank=True,
        verbose_name="Seleção",
    )
    name = models.CharField(max_length=255, verbose_name="Nome")
    nationality = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Nacionalidade"
    )
    photo = models.URLField(max_length=500, null=True, blank=True, verbose_name="Foto")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Técnico"
        verbose_name_plural = "Técnicos"

    def __str__(self) -> str:
        return self.name