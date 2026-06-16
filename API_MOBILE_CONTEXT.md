# Bengala FC API - contexto para o app mobile

Este arquivo documenta a API existente no checkout atual para servir de base ao app mobile. A fonte usada foi o codigo do projeto: `config/urls.py`, routers, views, serializers, models, testes e settings.

## Base

- Local: `http://127.0.0.1:8000`
- Android emulator acessando servidor local do host: `http://10.0.2.2:8000`
- Railway configurado no projeto:
  - `https://bengalafc-api-production.up.railway.app`
  - `https://bengalafc-api-production-0a3a.up.railway.app`

Todas as rotas da API usam barra final, por exemplo `/api/users/`.

## Segredos e variaveis

Nao colocar segredos no app mobile nem neste arquivo. O app mobile deve receber apenas valores publicos, como base URL da API e, se o backend continuar usando OAuth password grant, o `client_id` apropriado.

Variaveis relevantes do backend:

| Variavel | Uso |
| --- | --- |
| `SECRET_KEY` | segredo interno do Django |
| `DEBUG` | modo debug |
| `ALLOWED_HOSTS` | hosts aceitos pelo Django |
| `CSRF_TRUSTED_ORIGINS` | origens confiaveis para CSRF em fluxos web |
| `DATABASE_URL` / `DATABASE_PUBLIC_URL` | banco PostgreSQL Railway; sem elas usa SQLite |
| `FOOTBALL_API_URL` | URL da API-Football/API-Sports |
| `FOOTBALL_API_KEY` | chave secreta da API externa de futebol |
| `FOOTBALL_API_HEADER` | header da chave externa, ex: `x-apisports-key` |
| `FOOTBALL_API_DEFAULT_COMPETITION_ID` | competicao default dos comandos de sync |
| `FOOTBALL_API_DEFAULT_SEASON` | temporada default dos comandos de sync |

Observacao importante: existe chave sensivel no `.env.example` atual. Para uso em app mobile, trate esse valor como vazado e nao o copie.

## Autenticacao

O backend usa Django REST Framework com OAuth2 via `django-oauth-toolkit`.

Headers comuns:

```http
Accept: application/json
Content-Type: application/json
Authorization: Bearer <access_token>
```

Para upload de foto em perfil:

```http
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

### Login por OAuth2

`POST /o/token/`

Content-Type:

```http
application/x-www-form-urlencoded
```

Payload para login com usuario e senha:

```text
grant_type=password&username=<username>&password=<senha>&client_id=<client_id>&client_secret=<client_secret>
```

Resposta esperada do OAuth toolkit:

```json
{
  "access_token": "token",
  "expires_in": 36000,
  "token_type": "Bearer",
  "scope": "read write",
  "refresh_token": "refresh"
}
```

Payload para renovar token:

```text
grant_type=refresh_token&refresh_token=<refresh_token>&client_id=<client_id>&client_secret=<client_secret>
```

Notas para o mobile:

- O README orienta criar uma aplicacao OAuth2 `Confidential` com grant `Resource owner password-based`.
- Em app mobile, `client_secret` embutido no app nao e realmente secreto. Em ajuste futuro, vale mudar para um fluxo mais apropriado ao mobile ou criar um endpoint de auth simplificado.
- O backend tambem aceita `SessionAuthentication`, mas o app mobile deve usar `Bearer`.

### Rotas OAuth2 disponiveis

| Metodo | Rota | Uso no mobile |
| --- | --- | --- |
| `POST` | `/o/token/` | obter ou renovar token |
| `POST` | `/o/revoke_token/` | revogar token/logout server-side |
| `POST` | `/o/introspect/` | introspecionar token, normalmente uso interno |
| `GET/POST` | `/o/authorize/` | authorization code flow, nao e o fluxo atual do app |
| `POST` | `/o/device-authorization/` | device flow, nao usado hoje |
| `GET/POST` | `/o/device/` | device flow |
| `GET` | `/o/userinfo/` | OIDC user info, se configurado |
| `GET` | `/o/.well-known/openid-configuration` | discovery OIDC |
| `GET` | `/o/.well-known/jwks.json` | chaves OIDC |
| `GET/POST` | `/o/logout/` | logout OIDC |

## Convencoes DRF

Quando um recurso usa `ModelViewSet`, as rotas automaticas sao:

| Metodo | Rota | Acao |
| --- | --- | --- |
| `GET` | `/api/recurso/` | listar |
| `POST` | `/api/recurso/` | criar |
| `GET` | `/api/recurso/{id}/` | detalhar |
| `PUT` | `/api/recurso/{id}/` | substituir |
| `PATCH` | `/api/recurso/{id}/` | atualizar parcialmente |
| `DELETE` | `/api/recurso/{id}/` | excluir |

Nao ha paginacao configurada no `REST_FRAMEWORK`, entao listas retornam array JSON puro por padrao.

## Usuarios e perfil

Router: `/api/users/`

Permissoes:

- `POST /api/users/`: publico.
- Actions `me`, `update_profile`, `profiles`: requerem Bearer token.
- `PATCH /api/users/{id}/update_profile/`: admin.
- O ViewSet de usuarios nao expoe listagem/detalhe padrao de `User`; so cadastro e actions.

### Cadastrar usuario

`POST /api/users/`

Payload:

```json
{
  "username": "maria",
  "email": "maria@example.com",
  "password": "senha123",
  "first_name": "Maria",
  "last_name": "Silva"
}
```

Resposta `201`:

```json
{
  "id": 1,
  "username": "maria",
  "email": "maria@example.com",
  "first_name": "Maria",
  "last_name": "Silva"
}
```

O campo `password` e apenas escrita.

### Perfil do usuario logado

`GET /api/users/me/`

Resposta:

```json
{
  "id": 1,
  "username": "maria",
  "email": "maria@example.com",
  "first_name": "Maria",
  "last_name": "Silva",
  "points": 120,
  "photo": "/media/profiles/foto.jpg",
  "favorite_team": 3
}
```

### Atualizar perfil do usuario logado

`PATCH /api/users/update_profile/`

Aceita JSON ou `multipart/form-data`.

Payload JSON:

```json
{
  "first_name": "Maria",
  "last_name": "Souza",
  "favorite_team": 3
}
```

Payload multipart:

```text
first_name=Maria
last_name=Souza
favorite_team=3
photo=<arquivo>
```

Resposta: mesmo shape de `/api/users/me/`.

### Listar perfis

`GET /api/users/profiles/`

Resposta:

```json
[
  {
    "id": 1,
    "username": "maria",
    "email": "maria@example.com",
    "first_name": "Maria",
    "last_name": "Silva",
    "points": 120,
    "photo": null,
    "favorite_team": 3
  }
]
```

### Admin atualizar perfil de usuario

`PATCH /api/users/{id}/update_profile/`

Mesmo payload de `/api/users/update_profile/`, mas requer usuario admin.

## Dados reais de futebol

Os endpoints abaixo usam `ModelViewSet`.

Permissao:

- `GET` publico, sem token.
- `POST`, `PUT`, `PATCH` e `DELETE` exigem usuario autenticado.

### Times/selecao

Base: `/api/teams/`

Filtros:

| Query param | Exemplo | Efeito |
| --- | --- | --- |
| `country` | `?country=Brazil` | filtra por pais exato, case-insensitive |
| `is_active` | `?is_active=true` | aceita `true`/`1`; outros valores viram `false` |

Campos:

```json
{
  "id": 1,
  "external_id": 26,
  "name": "Argentina",
  "code": "ARG",
  "country": "Argentina",
  "logo": "https://...",
  "founded": 1893,
  "is_active": true,
  "created_at": "2026-06-16T10:00:00-03:00",
  "updated_at": "2026-06-16T10:00:00-03:00"
}
```

Payload de criacao/edicao usa os mesmos campos, exceto `id`, `created_at` e `updated_at`.

### Jogadores reais

Base: `/api/players/`

Filtros:

| Query param | Exemplo | Efeito |
| --- | --- | --- |
| `team` | `?team=1` | filtra pelo ID interno do time |
| `team_external_id` | `?team_external_id=26` | filtra pelo ID externo do time |
| `position` | `?position=Attacker` | contem texto na posicao |
| `nationality` | `?nationality=Brazil` | nacionalidade exata, case-insensitive |
| `stage` | `?stage=1` | filtra jogadores das selecoes que possuem partidas na fase |

Campos:

```json
{
  "id": 10,
  "external_id": 154,
  "team": 1,
  "team_detail": {
    "id": 1,
    "external_id": 26,
    "name": "Argentina"
  },
  "name": "Lionel Messi",
  "firstname": "Lionel",
  "lastname": "Messi",
  "age": 35,
  "nationality": "Argentina",
  "height": "170 cm",
  "weight": "72 kg",
  "photo": "https://...",
  "position": "Attacker",
  "number": 10,
  "is_active": true,
  "created_at": "2026-06-16T10:00:00-03:00",
  "updated_at": "2026-06-16T10:00:00-03:00"
}
```

`team_detail` e somente leitura. Para criar/editar, envie `team` com ID interno.

Para montagem de escalação por fase, prefira combinar `stage` e `position`, por exemplo:

```http
GET /api/players/?stage=1&position=FW
```

### Tecnicos

Base: `/api/coaches/`

Filtros:

| Query param | Exemplo | Efeito |
| --- | --- | --- |
| `team` | `?team=1` | filtra pelo ID interno do time |
| `nationality` | `?nationality=Brazil` | nacionalidade exata |
| `is_active` | `?is_active=true` | ativo/inativo |

Campos:

```json
{
  "id": 1,
  "external_id": 900,
  "team": 1,
  "name": "Tecnico",
  "nationality": "Brazil",
  "photo": "https://...",
  "is_active": true,
  "created_at": "2026-06-16T10:00:00-03:00",
  "updated_at": "2026-06-16T10:00:00-03:00"
}
```

### Competicoes

Base: `/api/competitions/`

Filtros:

| Query param | Exemplo | Efeito |
| --- | --- | --- |
| `season` | `?season=2022` | filtra temporada |
| `type` | `?type=Cup` | filtra tipo exato, case-insensitive |

Campos:

```json
{
  "id": 1,
  "external_id": 1,
  "name": "World Cup",
  "type": "Cup",
  "logo": "https://...",
  "season": 2022,
  "created_at": "2026-06-16T10:00:00-03:00",
  "updated_at": "2026-06-16T10:00:00-03:00"
}
```

### Fases

Base: `/api/stages/`

Filtros:

| Query param | Exemplo | Efeito |
| --- | --- | --- |
| `competition` | `?competition=1` | ID interno da competicao |
| `competition_external_id` | `?competition_external_id=1` | ID externo da competicao |

Campos expostos hoje pelo serializer:

```json
{
  "id": 1,
  "competition": 1,
  "competition_detail": {
    "id": 1,
    "external_id": 1,
    "name": "World Cup",
    "season": 2022
  },
  "name": "Fase de Grupos",
  "order": 1,
  "starts_at": "2026-06-11T18:00:00-03:00",
  "lineup_deadline_at": "2026-06-11T17:30:00-03:00",
  "ends_at": "2026-06-19T23:30:00-03:00",
  "finished_at": null,
  "is_current": true,
  "is_finished": false,
  "is_last_stage": false,
  "previous_stage": null,
  "next_stage": 2
}
```

Payload de criacao:

```json
{
  "competition": 1,
  "name": "Final",
  "order": 50,
  "starts_at": "2026-06-30T18:00:00Z",
  "lineup_deadline_at": "2026-06-30T17:30:00Z",
  "ends_at": "2026-06-30T23:30:00Z",
  "finished_at": null,
  "is_current": false
}
```

Campos de fluxo:

| Campo | Uso no mobile |
| --- | --- |
| `is_current` | indica a fase atual, onde o usuario deve escalar |
| `finished_at` | data/hora em que a fase foi encerrada |
| `is_finished` | `true` quando `finished_at` existe |
| `is_last_stage` | `true` quando e a ultima fase pela ordem cadastrada |
| `previous_stage` | ID da fase anterior, se existir |
| `next_stage` | ID da proxima fase, se existir |

### Estado da competicao/fases

`GET /api/stages/state/`

Filtros opcionais:

| Query param | Exemplo | Efeito |
| --- | --- | --- |
| `competition` | `?competition=1` | busca estado da competicao pelo ID interno |
| `competition_external_id` | `?competition_external_id=2026001` | busca estado da competicao pelo ID externo |

Se nenhum filtro for enviado, a API tenta usar a competicao que possui fase atual. Se nao houver fase atual, usa a competicao mais recente.

No endpoint de estado, `previous_stage` representa a ultima fase finalizada. Se a fase anterior ainda nao foi finalizada, o valor vem `null`.

Resposta com competicao em andamento:

```json
{
  "competition": {
    "id": 1,
    "external_id": 2026001,
    "name": "Copa Bengala FC",
    "season": 2026
  },
  "competition_finished": false,
  "has_started": true,
  "current_stage": {
    "id": 2,
    "name": "Semifinal",
    "is_current": true,
    "is_finished": false,
    "is_last_stage": false,
    "previous_stage": 1,
    "next_stage": 3
  },
  "previous_stage": {
    "id": 1,
    "name": "Fase de Grupos",
    "is_current": false,
    "is_finished": true
  },
  "next_stage": {
    "id": 3,
    "name": "Final"
  },
  "last_stage": {
    "id": 3,
    "name": "Final",
    "is_last_stage": true
  },
  "stages": []
}
```

Resposta apos a ultima fase:

```json
{
  "competition_finished": true,
  "has_started": true,
  "current_stage": null,
  "previous_stage": {
    "id": 3,
    "name": "Final",
    "is_finished": true,
    "is_last_stage": true
  },
  "next_stage": null,
  "last_stage": {
    "id": 3,
    "name": "Final",
    "is_finished": true,
    "is_last_stage": true
  },
  "stages": []
}
```

Uso recomendado na Home:

- Se `competition_finished` for `true`, mostrar que a competicao acabou.
- Para "pontuacao da rodada anterior", usar `previous_stage.id`.
- Para montagem de time, usar `current_stage.id`.
- Se `current_stage` for `null` e `competition_finished` for `false`, nao existe fase atual definida no backend.

### Partidas

Base: `/api/fixtures/`

Filtros:

| Query param | Exemplo | Efeito |
| --- | --- | --- |
| `competition` | `?competition=1` | competicao interna |
| `stage` | `?stage=1` | fase |
| `team` | `?team=1` | mandante ou visitante |
| `status` | `?status=FT` | status exato |

Campos:

```json
{
  "id": 1,
  "external_id": 855735,
  "competition": 1,
  "competition_detail": {},
  "stage": 1,
  "stage_detail": {},
  "home_team": 1,
  "home_team_detail": {},
  "away_team": 2,
  "away_team_detail": {},
  "kickoff_at": "2022-12-18T15:00:00Z",
  "status": "FT",
  "home_score": 3,
  "away_score": 3,
  "venue": "Lusail Stadium",
  "created_at": "2026-06-16T10:00:00-03:00",
  "updated_at": "2026-06-16T10:00:00-03:00"
}
```

Payload de criacao:

```json
{
  "external_id": 855735,
  "competition": 1,
  "stage": 1,
  "home_team": 1,
  "away_team": 2,
  "kickoff_at": "2022-12-18T15:00:00Z",
  "status": "FT",
  "home_score": 3,
  "away_score": 3,
  "venue": "Lusail Stadium"
}
```

### Estatisticas de jogadores

Base: `/api/player-statistics/`

Filtros:

| Query param | Exemplo | Efeito |
| --- | --- | --- |
| `player` | `?player=10` | jogador real |
| `fixture` | `?fixture=1` | partida |

Campos expostos:

```json
{
  "id": 1,
  "player": 10,
  "player_detail": {},
  "fixture": 1,
  "fixture_detail": {},
  "minutes": 90,
  "goals": 1,
  "assists": 1,
  "shots": 3,
  "shots_on_target": 2,
  "passes": 50,
  "key_passes": 2,
  "tackles": 1,
  "interceptions": 0,
  "yellow_cards": 0,
  "red_cards": 0,
  "rating": "8.50"
}
```

Observacao: o model atual tem `goals_conceded` e `saves`, mas o serializer nao retorna nem aceita esses campos na API atual.

### Estatisticas de times

Base: `/api/team-statistics/`

Filtros:

| Query param | Exemplo | Efeito |
| --- | --- | --- |
| `team` | `?team=1` | time |
| `fixture` | `?fixture=1` | partida |

Campos:

```json
{
  "id": 1,
  "team": 1,
  "team_detail": {},
  "fixture": 1,
  "fixture_detail": {},
  "possession": 55,
  "shots": 12,
  "shots_on_target": 6,
  "corners": 4,
  "fouls": 10,
  "offsides": 1,
  "yellow_cards": 2,
  "red_cards": 0
}
```

## Fantasy: jogador virtual e pontuacao individual

Router de jogador virtual: `/api/player/`

Este ViewSet nao expoe CRUD padrao. Use apenas as actions abaixo.

### Criar perfil de jogador virtual

`POST /api/player/create_profile/`

Requer token.

Payload:

```json
{
  "position": "atacante",
  "football_player_id": 154
}
```

Campos:

- `position`: obrigatorio no fluxo atual. Opcoes do model: `goleiro`, `zagueiro`, `lateral`, `meia`, `atacante`.
- `football_player_id`: opcional; o servico busca pelo `external_id` do jogador real, nao pelo ID interno.

Resposta `201`:

```json
{
  "id": 1,
  "position": "atacante",
  "football_player": 10,
  "user": 1
}
```

Erros:

```json
{"detail": "Perfil já existe."}
```

Observacao: nao ha validacao explicita no serializer nessa action porque ela chama o servico direto. Se `position` vier invalida, o erro pode estourar como erro de banco/validacao do Django.

### Buscar meu jogador virtual

`GET /api/player/me/`

Resposta:

```json
{
  "id": 1,
  "position": "atacante",
  "football_player": 10,
  "user": 1
}
```

Se nao existir:

```json
{"detail": "Perfil não encontrado."}
```

### Eventos de pontuacao

Router: `/api/scores/`

Este ViewSet nao expoe CRUD padrao. Use apenas actions.

`GET /api/scores/my_scores/`

Resposta:

```json
[
  {
    "id": 1,
    "event_type": "gol",
    "event_display": "Gol",
    "points": "8.00",
    "fixture": 1,
    "created_at": "2026-06-16T10:00:00-03:00"
  }
]
```

`GET /api/scores/total/`

Resposta:

```json
{
  "points": 120
}
```

Eventos existentes no model:

| `event_type` | Display | Pontos base |
| --- | --- | --- |
| `grande_defesa` | Grande defesa | goleiro: `4.0` |
| `jogo_sem_sofrer_gol` | Jogo sem sofrer gol | goleiro/zagueiro/lateral: `5.0` |
| `gols_sofridos` | Gols sofridos | goleiro: `-2.0` |
| `cartao_amarelo` | Cartao Amarelo | `-2.0` |
| `cartao_vermelho` | Cartao Vermelho | `-5.0` |
| `gol` | Gol | `8.0` |
| `assistencia` | Assistencia | `5.0` |
| `desarme` | Desarme | `1.5` |
| `finalizacao_fora` | Finalizacao fora/trave | `1.0` |
| `finalizacao_alvo` | Finalizacao no alvo | `3.0` |

## Fantasy: escalacoes

Router: `/api/lineups/`

Permissao: todas as rotas exigem token.

Este recurso usa `ModelViewSet`, entao possui:

| Metodo | Rota | Uso |
| --- | --- | --- |
| `GET` | `/api/lineups/` | listar minhas escalacoes |
| `POST` | `/api/lineups/` | criar escalacao |
| `GET` | `/api/lineups/{id}/` | detalhar minha escalacao |
| `PUT` | `/api/lineups/{id}/` | substituir |
| `PATCH` | `/api/lineups/{id}/` | atualizar parcialmente |
| `DELETE` | `/api/lineups/{id}/` | excluir |
| `GET` | `/api/lineups/by-stage/{stage_id}/` | buscar minha escalacao de uma fase |
| `GET` | `/api/lineups/phase-score-history/` | historico completo por fase, com 0 quando nao houve escalacao |
| `GET` | `/api/lineups/{id}/score-history/` | historico/calculo de pontos da escalacao |

Filtro de listagem:

| Query param | Exemplo |
| --- | --- |
| `stage` | `/api/lineups/?stage=1` |

### Criar escalacao

`POST /api/lineups/`

Payload:

```json
{
  "stage": 1,
  "player_ids": [10, 11, 12, 13, 14],
  "captain_id": 10,
  "coach_id": 1
}
```

Campos:

- `stage`: ID interno da fase.
- `player_ids`: lista de IDs internos de `football.Player`.
- `captain_id`: ID interno de `football.Player`; precisa estar dentro de `player_ids`.
- `coach_id`: opcional; ID interno de `football.Coach`.

Validacoes:

- Nao permite jogadores repetidos.
- Todos os jogadores precisam existir.
- O capitao precisa estar na escalacao.
- O tecnico, se informado, precisa existir.
- Um usuario so pode ter uma escalacao por fase.
- Se a fase tiver partidas cadastradas, todos os jogadores precisam ser de selecoes que jogam nessa fase.
- Se informado, o tecnico tambem precisa ser de uma selecao que joga nessa fase.

Resposta:

```json
{
  "id": 1,
  "stage": 1,
  "captain": 10,
  "captain_detail": {
    "id": 10,
    "name": "Jogador 1",
    "team": 1
  },
  "coach": 1,
  "coach_detail": {
    "id": 1,
    "name": "Tecnico",
    "photo": "https://..."
  },
  "players": [
    {
      "id": 1,
      "player": 10,
      "player_detail": {
        "id": 10,
        "name": "Jogador 1",
        "position": "Attacker"
      },
      "order": 0,
      "created_at": "2026-06-16T10:00:00-03:00"
    }
  ],
  "created_at": "2026-06-16T10:00:00-03:00",
  "updated_at": "2026-06-16T10:00:00-03:00"
}
```

Nota: `captain_id`, `coach_id` e `player_ids` sao campos de escrita. Mesmo aparecendo no serializer, em resposta normalmente os campos write-only nao devem ser usados pelo app. Use `captain`, `coach`, `captain_detail`, `coach_detail` e `players`.

### Atualizar escalacao

`PATCH /api/lineups/{id}/`

Payload para trocar jogadores e capitao:

```json
{
  "player_ids": [11, 12, 13, 14, 15],
  "captain_id": 15,
  "coach_id": 2
}
```

Quando `player_ids` muda, o backend registra automaticamente entradas em `/api/transfers/` comparando removidos e adicionados.

### Buscar escalacao por fase

`GET /api/lineups/by-stage/{stage_id}/`

Resposta: mesmo shape de detalhe da escalacao.

Se nao existir:

```json
{"detail": "Escalação não encontrada para esta fase."}
```

### Historico de pontos da escalacao

`GET /api/lineups/{id}/score-history/`

Calcula pontos com base em `PlayerStatistic` das partidas da fase da escalacao.

Resposta:

```json
{
  "lineup": 1,
  "stage": 1,
  "total_points": 41.0,
  "items": [
    {
      "fixture": 1,
      "fixture_external_id": 855735,
      "player": 10,
      "player_name": "Jogador 1",
      "is_captain": true,
      "points": 28.0
    },
    {
      "fixture": null,
      "player": null,
      "player_name": "Tecnico",
      "is_captain": false,
      "is_coach": true,
      "points": 7.2
    }
  ]
}
```

Regras usadas nessa rota:

- Gol: `8.0`
- Assistencia: `5.0`
- Desarme: `1.5`
- Cartao amarelo: `-2.0`, no maximo uma vez por partida
- Cartao vermelho: `-5.0`, no maximo uma vez por partida
- Finalizacao no alvo: `3.0`
- Finalizacao fora: `shots - shots_on_target`, multiplicado por `1.0`
- Capitao tem os pontos dobrados.
- Tecnico pontua pela media de `rating` dos jogadores do time dele naquela fase.

Observacao: a mesma funcao de calculo desta rota tambem e usada pelo ranking global e pelo ranking de amigos. Assim, o total do ranking deve bater com a soma das pontuacoes das escalacoes do usuario.

## Fantasy: transferencias

Router: `/api/transfers/`

Permissao: requer token.

Read-only:

| Metodo | Rota | Uso |
| --- | --- | --- |
| `GET` | `/api/transfers/` | listar minhas transferencias |
| `GET` | `/api/transfers/{id}/` | detalhar transferencia |

Filtro:

| Query param | Exemplo |
| --- | --- |
| `stage` | `/api/transfers/?stage=1` |

Resposta:

```json
[
  {
    "id": 1,
    "stage": 1,
    "lineup": 1,
    "from_player": 10,
    "from_player_detail": {},
    "to_player": 15,
    "to_player_detail": {},
    "created_at": "2026-06-16T10:00:00-03:00"
  }
]
```

## Ranking e amizades

Router: `/api/ranking/`

Permissao: todas as rotas exigem token.

Este ViewSet nao expoe CRUD padrao. Use apenas actions.

### Ranking global

`GET /api/ranking/global/`

Resposta:

```json
[
  {
    "id": 1,
    "username": "maria",
    "points": 120,
    "position": 1
  }
]
```

`points` e calculado pela soma de todas as escalacoes do usuario usando a mesma regra de `/api/lineups/{id}/score-history/`. Nao depende do campo legado `User.points`.

Ordenacao: `points` calculado decrescente. Empates sao ordenados por `username` e depois `id`. `position` e calculado em memoria pela view.

### Ranking de amigos

`GET /api/ranking/friends/`

Resposta: mesmo shape do ranking global, incluindo o usuario logado. A pontuacao tambem e calculada pela soma das escalacoes.

Importante: amizade e direcional. Se A adiciona B, B aparece no ranking de amigos de A, mas A nao aparece automaticamente no ranking de B.

### Adicionar amigo

`POST /api/ranking/friends/add/`

Payload:

```json
{
  "username": "joao"
}
```

Resposta `201`:

```json
{"detail": "joao adicionado com sucesso."}
```

Erros:

```json
{"detail": "username é obrigatório."}
{"detail": "Usuário não encontrado."}
{"detail": "Você não pode adicionar a si mesmo."}
{"detail": "Amizade já existe."}
```

## Documentacao e schema

| Metodo | Rota | Uso |
| --- | --- | --- |
| `GET` | `/api/schema/` | schema OpenAPI via drf-spectacular |
| `GET` | `/api/docs/` | Swagger UI |
| `GET` | `/api/redoc/` | Redoc |

No ambiente atual, a tentativa de gerar schema via comando falhou porque a `.venv` nao tem `dj_database_url` instalado. As rotas web acima existem no codigo.

## Rotas web/admin fora do consumo mobile

| Metodo | Rota | Uso |
| --- | --- | --- |
| `GET` | `/admin/` | Django admin |
| `GET` | `/hello/` | pagina HTML interna |
| `GET` | `/pag2/` | pagina HTML interna |
| `GET/POST` | `/accounts/login/` | login web por sessao |
| `GET/POST` | `/accounts/signup/` | cadastro HTML |

O app mobile nao deve depender dessas rotas.

## Fluxos recomendados para o app mobile

### Cadastro e login

1. `POST /api/users/` com `username`, `email`, `password`, `first_name`, `last_name`.
2. `POST /o/token/` com grant `password`.
3. Guardar `access_token` e `refresh_token` em armazenamento seguro.
4. Chamar `GET /api/users/me/` para montar o usuario logado.

### Home inicial

Chamadas uteis:

1. `GET /api/users/me/`
2. `GET /api/scores/total/`
3. `GET /api/ranking/global/`
4. `GET /api/lineups/`

### Montagem de escalacao

1. Buscar fases: `GET /api/stages/?competition={id}`.
2. Buscar jogadores reais por time/posicao/nacionalidade:
   - `GET /api/players/?team={team_id}`
   - `GET /api/players/?position=Attacker`
   - `GET /api/players/?stage={stage_id}&position=FW`
   - `GET /api/players/?nationality=Brazil`
3. Buscar tecnicos: `GET /api/coaches/?team={team_id}`.
4. Ver se ja existe escalacao: `GET /api/lineups/by-stage/{stage_id}/`.
5. Se nao existir, criar com `POST /api/lineups/`.
6. Se existir, atualizar com `PATCH /api/lineups/{id}/`.

### Tela de historico/pontuacao da escalacao

Para mostrar todas as fases, incluindo fases em que o usuario nao escalou e pontuou `0.0`, prefira:

`GET /api/lineups/phase-score-history/`

Filtros opcionais:

| Query param | Exemplo | Efeito |
| --- | --- | --- |
| `competition` | `?competition=1` | competicao interna |
| `competition_external_id` | `?competition_external_id=2026001` | competicao externa |

Resposta:

```json
[
  {
    "stage": 1,
    "stage_name": "Fase de Grupos",
    "stage_order": 1,
    "is_current": false,
    "is_finished": true,
    "lineup": 10,
    "has_lineup": true,
    "total_points": 259.0,
    "items": []
  },
  {
    "stage": 3,
    "stage_name": "Final",
    "stage_order": 3,
    "is_current": false,
    "is_finished": true,
    "lineup": null,
    "has_lineup": false,
    "total_points": 0.0,
    "items": []
  }
]
```

Uso no app:

- `has_lineup=false` significa que o usuario nao escalou naquela fase.
- Ainda assim a fase deve aparecer no historico com `total_points=0.0`.
- Quando quiser detalhes por jogador, use `items` das fases que possuem `has_lineup=true`.

Fluxo antigo, baseado apenas em escalacoes existentes:

1. `GET /api/lineups/?stage={stage_id}` ou `GET /api/lineups/by-stage/{stage_id}/`.
2. `GET /api/lineups/{id}/score-history/`.
3. Opcional: `GET /api/transfers/?stage={stage_id}`.

### Ranking e amigos

1. `GET /api/ranking/global/`.
2. `GET /api/ranking/friends/`.
3. `POST /api/ranking/friends/add/` com `username`.

## Seeds de demonstracao

Para preparar a apresentacao em etapas, rode os comandos nesta ordem:

```bash
.venv/bin/python src/manage.py seed_minimal_worldcup
.venv/bin/python src/manage.py seed_worldcup_phase1_scores
.venv/bin/python src/manage.py seed_worldcup_phase2_scores
.venv/bin/python src/manage.py seed_worldcup_phase3_scores
```

O primeiro comando cria/reset a Copa minima: 4 selecoes, fases, partidas e jogadores, sem pontuacoes. Ele tambem volta a `Fase de Grupos` para fase atual.

Os comandos seguintes fazem a evolucao da demonstracao:

- `seed_worldcup_phase1_scores`: pontua a `Fase de Grupos`, finaliza essa fase e muda a fase atual para `Semifinal`.
- `seed_worldcup_phase2_scores`: pontua a `Semifinal`, finaliza essa fase e muda a fase atual para `Final`.
- `seed_worldcup_phase3_scores`: pontua a `Final`, Brasil vence Argentina por 3x1 e todas as fases ficam finalizadas.

As pontuacoes sao criadas em `PlayerStatistic` para todos os jogadores dos jogos e em `TeamStatistic` para as selecoes de cada partida.

## Pendencias/inconsistencias importantes para ajuste futuro

- Ha conflito potencial de numeracao de migrations em `football`: existe `0003_coach.py` e tambem `0003_stage_is_current_and_more.py`.
- Ha conflito potencial de numeracao de migrations em `scores`: existe `0003_fantasylineup_coach.py` e tambem `0003_fantasylineup_final_points_and_more.py`.
- `PlayerStatistic` tem `goals_conceded` e `saves` no model, mas a API nao expoe esses campos no serializer.
- `scores.services.calculate_from_statistic` consulta `team_stat.goals_conceded`, mas `TeamStatistic` nao tem esse campo no model atual.
- `create_player` recebe `football_player_id`, mas interpreta como `external_id` de `football.Player`. O nome do campo pode confundir o app.
- `User.email` e unico, mas `username` tambem e o identificador usado no login OAuth. No cadastro web, `username=email`; no cadastro API, `username` e `email` podem ser diferentes.
- O app mobile nao deve embutir `client_secret`; o fluxo OAuth atual funciona, mas nao e ideal para mobile.
