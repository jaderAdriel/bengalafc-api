from datetime import datetime, timezone

from apps.football.models import (
    Competition,
    Fixture,
    Player,
    PlayerStatistic,
    Stage,
    TeamStatistic,
)


class WorldCupScoreSeeder:
    competition_external_id = 2026001

    def __init__(self, stdout=None, style=None):
        self.stdout = stdout
        self.style = style

    def seed_phase(
        self,
        *,
        phase_name,
        next_phase_name,
        finished_at,
        results,
    ):
        competition = Competition.objects.get(external_id=self.competition_external_id)
        phase = Stage.objects.get(competition=competition, name=phase_name)

        for external_id, home_score, away_score in results:
            fixture = Fixture.objects.select_related(
                "home_team",
                "away_team",
                "stage",
            ).get(external_id=external_id, stage=phase)

            fixture.home_score = home_score
            fixture.away_score = away_score
            fixture.status = "FT"
            fixture.save(update_fields=["home_score", "away_score", "status", "updated_at"])

            self._seed_team_statistics(fixture)
            self._seed_player_statistics(fixture, home_score, away_score)

        phase.finished_at = self._parse_datetime(finished_at)
        phase.is_current = False
        phase.save(update_fields=["finished_at", "is_current"])

        Stage.objects.filter(competition=competition).exclude(id=phase.id).update(
            is_current=False
        )
        if next_phase_name:
            Stage.objects.filter(
                competition=competition,
                name=next_phase_name,
            ).update(is_current=True, finished_at=None)

    def _seed_team_statistics(self, fixture):
        home_possession = 55 if fixture.home_score >= fixture.away_score else 45
        away_possession = 100 - home_possession
        data = [
            (
                fixture.home_team,
                home_possession,
                10 + fixture.home_score,
                5 + fixture.home_score,
            ),
            (
                fixture.away_team,
                away_possession,
                10 + fixture.away_score,
                5 + fixture.away_score,
            ),
        ]

        for team, possession, shots, shots_on_target in data:
            TeamStatistic.objects.update_or_create(
                fixture=fixture,
                team=team,
                defaults={
                    "possession": possession,
                    "shots": shots,
                    "shots_on_target": shots_on_target,
                    "corners": 4,
                    "fouls": 9,
                    "offsides": 1,
                    "yellow_cards": 1,
                    "red_cards": 0,
                },
            )

    def _seed_player_statistics(self, fixture, home_score, away_score):
        self._seed_team_player_statistics(
            fixture=fixture,
            team=fixture.home_team,
            goals_for=home_score,
            goals_against=away_score,
            team_won=home_score > away_score,
        )
        self._seed_team_player_statistics(
            fixture=fixture,
            team=fixture.away_team,
            goals_for=away_score,
            goals_against=home_score,
            team_won=away_score > home_score,
        )

    def _seed_team_player_statistics(self, *, fixture, team, goals_for, goals_against, team_won):
        players = list(team.players.order_by("number", "name"))
        scorers = self._goal_scorers(players, goals_for)
        assisters = self._assisters(players, goals_for)

        for player in players:
            position = (player.position or "").upper()
            is_goalkeeper = position == "GK"
            is_defender = position == "DF"
            is_midfielder = position == "MF"
            is_forward = position == "FW"

            goals = scorers.count(player.id)
            assists = assisters.count(player.id)
            shots = 1
            shots_on_target = 0
            tackles = 1
            interceptions = 1
            saves = 0

            if is_goalkeeper:
                shots = 0
                shots_on_target = 0
                tackles = 1
                saves = max(2, goals_against + 2)
            elif is_defender:
                shots = 1
                shots_on_target = 1 if goals else 0
                tackles = 3
            elif is_midfielder:
                shots = 1
                shots_on_target = 1 if goals or assists else 0
                tackles = 2
            elif is_forward:
                shots = 2
                shots_on_target = 1
                tackles = 1

            rating = 7.0
            if team_won:
                rating += 0.5
            rating += goals * 0.8
            rating += assists * 0.4

            PlayerStatistic.objects.update_or_create(
                fixture=fixture,
                player=player,
                defaults={
                    "minutes": 90,
                    "goals": goals,
                    "assists": assists,
                    "shots": shots,
                    "shots_on_target": shots_on_target,
                    "goals_conceded": goals_against if is_goalkeeper else 0,
                    "saves": saves,
                    "passes": 35 if not is_goalkeeper else 20,
                    "key_passes": 1 if assists else 0,
                    "tackles": tackles,
                    "interceptions": interceptions,
                    "yellow_cards": 0,
                    "red_cards": 0,
                    "rating": rating,
                },
            )

    def _goal_scorers(self, players, goals):
        preferred = [
            player for player in players if (player.position or "").upper() == "FW"
        ]
        preferred += [
            player for player in players if (player.position or "").upper() == "MF"
        ]
        preferred += [
            player for player in players if (player.position or "").upper() == "DF"
        ]
        if not preferred:
            preferred = players

        scorer_ids = []
        for index in range(goals):
            scorer_ids.append(preferred[index % len(preferred)].id)
        return scorer_ids

    def _assisters(self, players, goals):
        preferred = [
            player for player in players if (player.position or "").upper() == "MF"
        ]
        preferred += [
            player for player in players if (player.position or "").upper() == "FW"
        ]
        preferred += [
            player for player in players if (player.position or "").upper() == "DF"
        ]
        if not preferred:
            preferred = players

        assister_ids = []
        for index in range(max(goals - 1, 0)):
            assister_ids.append(preferred[index % len(preferred)].id)
        return assister_ids

    def _parse_datetime(self, value):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
