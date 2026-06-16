import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.football.models import Team, Competition, Stage, Fixture, Player, PlayerStatistic, TeamStatistic
from apps.scores.services import process_fixture_scores

# Normalization of team names to match the 2022 dataset if they already exist
TEAM_NAME_MAP = {
    "South Korea": "Korea Republic",
    "USA": "United States",
    "US": "United States",
}

def is_placeholder(name):
    if not name:
        return True
    name = name.strip()
    # Check if name is like '1A', '2B', '3A/B/...', etc., or 'W100', 'L101'
    if name[0].isdigit():
        return True
    if name.startswith(('W', 'L')) and len(name) > 1 and name[1:].isdigit():
        return True
    return False

def get_stage_name(round_name, group_name=None):
    round_lower = round_name.lower()
    if "matchday" in round_lower or (group_name and "group" in group_name.lower()):
        return "Fase de Grupos"
    elif "round of 32" in round_lower:
        return "Dezesseis-avos de Final"
    elif "round of 16" in round_lower:
        return "Oitavas de Final"
    elif "quarter" in round_lower:
        return "Quartas de Final"
    elif "semi" in round_lower:
        return "Semifinal"
    elif "third" in round_lower or "3rd" in round_lower or "place" in round_lower:
        return "Decisão do 3º Lugar"
    elif "final" in round_lower:
        return "Final"
    return round_name

def get_stage_order(stage_name):
    name_lower = stage_name.lower()
    if "grupos" in name_lower:
        return 10
    elif "dezesseis" in name_lower:
        return 15
    elif "oitavas" in name_lower:
        return 20
    elif "quartas" in name_lower:
        return 30
    elif "semifinal" in name_lower:
        return 40
    elif "terceiro" in name_lower or "decisão" in name_lower:
        return 45
    elif "final" in name_lower:
        return 50
    return 99

def parse_match_datetime(date_str, time_str):
    # e.g., date_str = "2026-06-11", time_str = "13:00 UTC-6"
    match = re.match(r"(\d{2}:\d{2})\s+UTC([+-]\d+)?", time_str)
    if match:
        hm = match.group(1)
        offset_str = match.group(2)
        dt_naive = datetime.strptime(f"{date_str} {hm}", "%Y-%m-%d %H:%M")
        if offset_str:
            offset_hours = int(offset_str)
        else:
            offset_hours = 0
        tz = timezone(timedelta(hours=offset_hours))
        return dt_naive.replace(tzinfo=tz)
    else:
        dt_naive = datetime.strptime(f"{date_str} {time_str[:5]}", "%Y-%m-%d %H:%M")
        return dt_naive.replace(tzinfo=timezone.utc)

class Command(BaseCommand):
    help = "Sincroniza os dados e partidas da Copa do Mundo 2026 a partir do arquivo JSON do openfootball"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=== INICIANDO SINCRONIZAÇÃO DA COPA DO MUNDO 2026 ==="))

        json_path = Path("/home/jader/Projects/bengalafc-api/src/data/worldcup_2026.json")
        if not json_path.exists():
            self.stdout.write(self.style.ERROR(f"Arquivo local não encontrado em {json_path}. Sincronize/baixe o JSON primeiro."))
            return

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        matches = data.get("matches", [])
        self.stdout.write(self.style.SUCCESS(f"Carregado arquivo JSON com {len(matches)} partidas."))

        # 1. Criar ou atualizar a competição World Cup 2026
        competition, comp_created = Competition.objects.update_or_create(
            external_id=1,  # ID 1 é a Copa do Mundo na API-Football
            defaults={
                "name": "FIFA World Cup 2026",
                "season": 2026,
                "type": "Cup",
                "logo": "https://media.api-sports.io/football/leagues/1.png"
            }
        )
        comp_action = "Criada" if comp_created else "Atualizada"
        self.stdout.write(self.style.SUCCESS(f"{comp_action} competição: {competition.name}"))

        def get_or_create_team(team_name):
            team_name = team_name.strip()
            norm_name = TEAM_NAME_MAP.get(team_name, team_name)
            try:
                team = Team.objects.get(name__iexact=norm_name)
                # Garante que o nome esteja atualizado
                if team.name != norm_name:
                    team.name = norm_name
                    team.save()
                return team
            except Team.DoesNotExist:
                ext_id = hash(norm_name) % 100000
                while Team.objects.filter(external_id=ext_id).exists():
                    ext_id += 1
                team = Team.objects.create(
                    external_id=ext_id,
                    name=norm_name,
                    country=norm_name,
                    logo=f"https://media.api-sports.io/football/teams/{ext_id}.png"
                )
                self.stdout.write(self.style.SUCCESS(f"Criada nova seleção: {team.name} (ID: {team.external_id})"))
                return team

        def ensure_squad(team):
            if team.players.count() == 0:
                self.stdout.write(self.style.WARNING(f"Gerando elenco mock de 11 jogadores para a seleção {team.name}..."))
                mock_players = [
                    ("Goleiro " + team.name, "GK", 1),
                    ("Zagueiro A " + team.name, "DF", 2),
                    ("Zagueiro B " + team.name, "DF", 3),
                    ("Lateral Dir " + team.name, "DF", 4),
                    ("Lateral Esq " + team.name, "DF", 6),
                    ("Meia A " + team.name, "MF", 5),
                    ("Meia B " + team.name, "MF", 8),
                    ("Meia C " + team.name, "MF", 10),
                    ("Atacante A " + team.name, "FW", 7),
                    ("Atacante B " + team.name, "FW", 9),
                    ("Atacante C " + team.name, "FW", 11),
                ]
                for name, pos, number in mock_players:
                    p_ext_id = hash(name + team.name) % 1000000
                    while Player.objects.filter(external_id=p_ext_id).exists():
                        p_ext_id += 1
                    Player.objects.create(
                        external_id=p_ext_id,
                        team=team,
                        name=name,
                        position=pos,
                        number=number,
                        photo=f"https://media.api-sports.io/football/players/default.png"
                    )

        fixtures_synced = 0
        stats_synced = 0

        for m in matches:
            t1_name = m.get("team1")
            t2_name = m.get("team2")

            if is_placeholder(t1_name) or is_placeholder(t2_name):
                # Ignora confrontos ainda indefinidos
                continue

            with transaction.atomic():
                team1 = get_or_create_team(t1_name)
                team2 = get_or_create_team(t2_name)

                ensure_squad(team1)
                ensure_squad(team2)

                stage_name = get_stage_name(m.get("round"), m.get("group"))
                stage, _ = Stage.objects.get_or_create(
                    competition=competition,
                    name=stage_name,
                    defaults={"order": get_stage_order(stage_name)}
                )

                kickoff_at = parse_match_datetime(m.get("date"), m.get("time"))

                fixture_key = f"2026_{team1.name}_{team2.name}_{m.get('date')}"
                
                # Procura fixture existente para evitar duplicados
                fixture = Fixture.objects.filter(
                    competition=competition,
                    home_team=team1,
                    away_team=team2,
                    kickoff_at=kickoff_at
                ).first()

                if not fixture:
                    ext_id = hash(fixture_key) % 1000000
                    while Fixture.objects.filter(external_id=ext_id).exists():
                        ext_id += 1
                    fixture = Fixture(
                        external_id=ext_id,
                        competition=competition,
                        home_team=team1,
                        away_team=team2,
                        kickoff_at=kickoff_at
                    )

                score_data = m.get("score")
                is_finished = False
                if score_data and "ft" in score_data:
                    fixture.home_score = score_data["ft"][0]
                    fixture.away_score = score_data["ft"][1]
                    fixture.status = "FT"
                    is_finished = True
                else:
                    fixture.home_score = None
                    fixture.away_score = None
                    fixture.status = "NS"

                fixture.stage = stage
                fixture.venue = m.get("ground", "")[:255]
                fixture.save()
                fixtures_synced += 1

                # Se a partida já terminou, vamos gerar estatísticas mock
                if is_finished:
                    # 1. TeamStatistic (necessário para a regra de Clean Sheet do fantasy)
                    # Time mandante
                    TeamStatistic.objects.update_or_create(
                        team=team1,
                        fixture=fixture,
                        defaults={
                            "possession": 50,
                            "shots": 10,
                            "shots_on_target": 4,
                            "corners": 5,
                            "fouls": 12,
                            "offsides": 2,
                            "yellow_cards": 1,
                            "red_cards": 0
                        }
                    )
                    # Time visitante
                    TeamStatistic.objects.update_or_create(
                        team=team2,
                        fixture=fixture,
                        defaults={
                            "possession": 50,
                            "shots": 10,
                            "shots_on_target": 4,
                            "corners": 5,
                            "fouls": 12,
                            "offsides": 2,
                            "yellow_cards": 1,
                            "red_cards": 0
                        }
                    )

                    # Contabiliza gols marcados por cada jogador na partida
                    goals1_by_player = {}
                    for g in m.get("goals1", []):
                        pname = g.get("name", "").strip()
                        if pname:
                            goals1_by_player[pname] = goals1_by_player.get(pname, 0) + 1

                    goals2_by_player = {}
                    for g in m.get("goals2", []):
                        pname = g.get("name", "").strip()
                        if pname:
                            goals2_by_player[pname] = goals2_by_player.get(pname, 0) + 1

                    def ensure_player_by_name(team, pname):
                        # Tenta encontrar no elenco existente da seleção
                        player = Player.objects.filter(team=team, name__iexact=pname).first()
                        if not player:
                            # Tenta por aproximação ou cria
                            p_ext_id = hash(pname + team.name) % 1000000
                            while Player.objects.filter(external_id=p_ext_id).exists():
                                p_ext_id += 1
                            player = Player.objects.create(
                                external_id=p_ext_id,
                                team=team,
                                name=pname,
                                position="FW",
                                photo="https://media.api-sports.io/football/players/default.png"
                            )
                        return player

                    # Mapeando os jogadores de fato
                    squad1_players = list(team1.players.all())
                    squad2_players = list(team2.players.all())

                    # Associa gols para os jogadores do Time 1
                    for pname, gcount in list(goals1_by_player.items()):
                        player = ensure_player_by_name(team1, pname)
                        if player not in squad1_players:
                            squad1_players.append(player)

                    # Associa gols para os jogadores do Time 2
                    for pname, gcount in list(goals2_by_player.items()):
                        player = ensure_player_by_name(team2, pname)
                        if player not in squad2_players:
                            squad2_players.append(player)

                    # Salva PlayerStatistic para todos os jogadores do Time 1
                    for player in squad1_players:
                        goals_scored = goals1_by_player.get(player.name, 0)
                        
                        # Determina gols sofridos (apenas goleiro ou defensores podem pontuar com isso)
                        goals_conceded = fixture.away_score
                        
                        defaults = {
                            "minutes": 90,
                            "goals": goals_scored,
                            "assists": 0,
                            "shots": 2 if player.position == "FW" else 1,
                            "shots_on_target": goals_scored,
                            "goals_conceded": goals_conceded if player.position == "GK" else 0,
                            "saves": 3 if player.position == "GK" else 0,
                            "passes": 30,
                            "key_passes": 1 if goals_scored > 0 else 0,
                            "tackles": 2 if player.position == "DF" else 0,
                            "interceptions": 1 if player.position == "DF" else 0,
                            "yellow_cards": 0,
                            "red_cards": 0,
                            "rating": 8.0 if goals_scored > 0 else 6.5
                        }
                        
                        PlayerStatistic.objects.update_or_create(
                            player=player,
                            fixture=fixture,
                            defaults=defaults
                        )
                        stats_synced += 1

                    # Salva PlayerStatistic para todos os jogadores do Time 2
                    for player in squad2_players:
                        goals_scored = goals2_by_player.get(player.name, 0)
                        goals_conceded = fixture.home_score
                        
                        defaults = {
                            "minutes": 90,
                            "goals": goals_scored,
                            "assists": 0,
                            "shots": 2 if player.position == "FW" else 1,
                            "shots_on_target": goals_scored,
                            "goals_conceded": goals_conceded if player.position == "GK" else 0,
                            "saves": 3 if player.position == "GK" else 0,
                            "passes": 30,
                            "key_passes": 1 if goals_scored > 0 else 0,
                            "tackles": 2 if player.position == "DF" else 0,
                            "interceptions": 1 if player.position == "DF" else 0,
                            "yellow_cards": 0,
                            "red_cards": 0,
                            "rating": 8.0 if goals_scored > 0 else 6.5
                        }
                        
                        PlayerStatistic.objects.update_or_create(
                            player=player,
                            fixture=fixture,
                            defaults=defaults
                        )
                        stats_synced += 1

                    # 3. Processar pontuação fantasy baseada nessa partida
                    process_fixture_scores(fixture)

        self.stdout.write(self.style.SUCCESS(f"=== SINCRONIZAÇÃO DA COPA DO MUNDO 2026 CONCLUÍDA ==="))
        self.stdout.write(self.style.SUCCESS(f"Partidas sincronizadas: {fixtures_synced}"))
        self.stdout.write(self.style.SUCCESS(f"Estatísticas de jogadores geradas: {stats_synced}"))
