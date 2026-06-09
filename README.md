# Bengala FC API ⚽🏆

A **Bengala FC API** é uma API REST desenvolvida em Python com o framework Django e Django REST Framework (DRF). Ela serve como o backend completo para uma plataforma de **Fantasy Game** de futebol (semelhante ao Cartola FC) ou um gerenciador de campeonatos integrado com dados de futebol reais.

O sistema permite sincronizar dados reais de ligas de futebol, além de gerenciar contas de usuários, perfis com fotos, amizades, escalações de times por fase do campeonato, transferências de jogadores e rankings competitivos.

---

## 📋 Para que serve? (Visão Geral)

A API do Bengala FC foi projetada para atender a duas frentes principais:

1. **Gestão de Dados Reais de Futebol**:
   - Integração com a API externa **API-Football** (via RapidAPI ou API-Sports) para capturar dados atualizados sobre seleções/equipes, elencos, partidas, fases de torneios e estatísticas completas pós-jogo.
   
2. **Plataforma de Fantasy Game**:
   - **Contas de Usuários & Perfis Detalhados**: Cadastro e autenticação de usuários, além de suporte a perfis de usuário (`UserProfile`) contendo foto de perfil e seleção favorita (`favorite_team`).
   - **Perfis de Jogador Virtual**: Permite que o usuário crie um perfil de jogador virtual (`Player`) associado a uma posição específica (Goleiro, Zagueiro, Lateral, Volante, Meia ou Atacante) e, opcionalmente, o vincule a um jogador real do futebol.
   - **Escalação de Times (Fantasy Lineup)**: Usuários escalam equipes completas de jogadores reais (`football.Player`) para fases (`Stage`) específicas do campeonato. Cada escalação define um **Capitão**, que tem sua pontuação de partida **dobrada**.
   - **Mercado & Transferências (`FantasyTransfer`)**: Atualizações nas escalações salvam automaticamente o histórico de trocas efetuadas por fase (jogadores que saíram e que entraram).
   - **Sistema de Pontuação (Score Engine)**: 
     - Pontuação manual ou automática com base nas estatísticas das partidas reais. 
     - Conversão de ações reais de jogo (gols, assistências, desarmes, finalizações, faltas, cartões) em pontuações personalizadas para o time do usuário ou perfil individual, com pesos configuráveis e bônus específicos por posição (ex: zagueiros, laterais e goleiros ganham bônus de *saldo de gols* quando a equipe não sofre gols).
   - **Rankings Competitivos & Amizades**: Sistema de amizades (`Friendship`) que permite visualizar Rankings de Amigos ou Rankings Globais baseados na soma das pontuações.

---

## 🛠️ Tecnologias Utilizadas

- **Core**: Python `>= 3.14`
- **Framework Web**: [Django 6.x](https://www.djangoproject.com/)
- **API Engine**: [Django REST Framework (DRF) 3.17.x](https://www.django-rest-framework.org/)
- **Autenticação**: OAuth2 via [Django OAuth Toolkit 3.2.x](https://django-oauth-toolkit.readthedocs.io/)
- **Processamento de Imagem**: [Pillow 12.2.x](https://python-pillow.org/) (usado nas fotos dos perfis)
- **Segurança CORS**: [django-cors-headers](https://github.com/adamchainz/django-cors-headers)
- **Banco de Dados**: PostgreSQL (Railway) / SQLite (padrão local `db.sqlite3` incluído no projeto)
- **Gerenciador de Pacotes**: `uv` (ou standard pip/venv)

---

## 🗂️ Estrutura de Módulos (Apps Localizadas)

O projeto está modularizado dentro do diretório `src/apps/`:

- **[users](file:///home/jader/Projects/bengalafc-api/src/apps/users)**: Gerencia o modelo customizado de usuário (`User`), o perfil expandido (`UserProfile`) com foto e seleção favorita, além dos endpoints para visualizar dados próprios e perfis de outros usuários.
- **[football](file:///home/jader/Projects/bengalafc-api/src/apps/football)**: Trata da integração de dados de futebol reais (seleções, jogadores reais, calendários de partidas e estatísticas da API-Football).
- **[scores](file:///home/jader/Projects/bengalafc-api/src/apps/scores)**: Contém o perfil de jogador virtual do usuário (`Player`), as escalações de fantasy (`FantasyLineup`), o controle de trocas (`FantasyTransfer`), os eventos de pontuação (`ScoreEvent`) e o motor de cálculo de pontos.
- **[ranking](file:///home/jader/Projects/bengalafc-api/src/apps/ranking)**: Provê o modelo de amizades e endpoints para geração de rankings globais e de amigos.

---

## ⚙️ Instalação e Configuração

### 1. Pré-requisitos
Certifique-se de possuir o **Python 3.14+** instalado. Recomenda-se o uso da ferramenta de pacotes `uv`.

### 2. Configurar Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto baseado no `.env.example`:

```bash
cp .env.example .env
```

Abra o `.env` e configure suas variáveis de ambiente:
- Configure sua credencial da API-Football (`FOOTBALL_API_KEY` e o header correspondente).
- Caso contrário, os serviços usarão automaticamente **fallbacks/mocks locais** para testar sem internet/credenciais.

### 3. Instalar Dependências e Criar Ambiente Virtual

```bash
# Caso utilize o uv (recomendado):
uv sync

# Caso utilize pip clássico:
python -m venv .venv
source .venv/bin/activate
pip install -r pyproject.toml
```

### 4. Executar Migrações do Banco de Dados
Para inicializar a estrutura do banco (seja o SQLite local padrão ou o PostgreSQL do Railway configurado pelas variáveis `DATABASE_URL` ou `DATABASE_PUBLIC_URL`):

```bash
.venv/bin/python src/manage.py migrate
```

### 5. Criar Administrador (Superusuário)
Para gerenciar o painel administrativo do Django e registrar aplicações OAuth2:

```bash
.venv/bin/python src/manage.py createsuperuser
```

### 6. Iniciar o Servidor de Desenvolvimento
Inicie o servidor localmente:

```bash
.venv/bin/python src/manage.py runserver
```

O servidor estará rodando em `http://127.0.0.1:8000/`.

---

## 🔑 Autenticação e Segurança (OAuth2)

A API utiliza autenticação OAuth2 protegida. Para consumir endpoints autenticados:

1. Acesse o admin do Django em `http://127.0.0.1:8000/admin/` com seu superusuário.
2. Navegue até **Django OAuth Toolkit** > **Applications** e clique em **Add Application**.
3. Crie uma aplicação com os seguintes campos:
   - **Client type**: `Confidential`
   - **Authorization grant type**: `Resource owner password-based`
   - **Name**: `Front-end App`
4. Salve e copie o **Client ID** e o **Client Secret** gerados.
5. Para requisitar um token, envie uma requisição POST para `/o/token/`:

```http
POST /o/token/
Content-Type: application/x-www-form-urlencoded

grant_type=password&username=seu_usuario&password=sua_senha&client_id=SEU_CLIENT_ID&client_secret=SEU_CLIENT_SECRET
```

Use o `access_token` retornado no header de todas as requisições autenticadas:
`Authorization: Bearer <seu_access_token>`

---

## 🔄 Sincronização de Dados de Futebol

Para carregar dados reais e estatísticas de torneios (como a Copa do Mundo 2022) no seu banco de dados, execute o comando consolidado:

```bash
.venv/bin/python src/manage.py sync_all --competition-id 1 --season 2022
```

Se desejar executar a sincronização em etapas individuais (equipes, jogadores, fases, etc.), consulte o [README interno do módulo de futebol](file:///home/jader/Projects/bengalafc-api/src/apps/football/README.md).

---

## 📡 Endpoints da API

Abaixo está o resumo dos principais endpoints disponíveis:

### 👤 Usuários e Perfis
| Método | Endpoint | Autenticação | Descrição |
| :--- | :--- | :---: | :--- |
| **POST** | `/api/users/` | Não | Cadastra um novo usuário no sistema. |
| **GET** | `/api/users/me/` | **Sim** | Retorna as informações do perfil do usuário logado (`UserProfile`). |
| **PATCH** | `/api/users/update_profile/` | **Sim** | Atualiza dados do perfil (aceita upload de foto de perfil e seleção favorita). |
| **GET** | `/api/users/profiles/` | **Sim** | Lista todos os perfis cadastrados no sistema. |
| **PATCH** | `/api/users/<pk>/update_profile/` | **Admin** | Permite ao administrador atualizar o perfil de qualquer usuário. |
| **POST** | `/o/token/` | Não | Solicita token de acesso via fluxo OAuth2 Password Grant. |

### 🎮 Jogador Virtual e Eventos de Pontuação
| Método | Endpoint | Autenticação | Descrição |
| :--- | :--- | :---: | :--- |
| **POST** | `/api/player/create_profile/` | **Sim** | Cria o perfil de jogador virtual do usuário logado. |
| **GET** | `/api/player/me/` | **Sim** | Retorna os detalhes do perfil de jogador do usuário logado. |
| **GET** | `/api/scores/my_scores/` | **Sim** | Lista os eventos de pontuação (`ScoreEvent`) atribuídos ao usuário. |
| **GET** | `/api/scores/total/` | **Sim** | Retorna o total acumulado de pontos do usuário logado. |

> [!NOTE]
> **Payload de Criação de Perfil de Jogador (`POST /api/player/create_profile/`):**
> ```json
> {
>   "position": "atacante",
>   "football_player_id": 154  // Opcional: ID externo do jogador real
> }
> ```
> *Posições válidas: `goleiro`, `zagueiro`, `lateral`, `meia`, `atacante`, `volante`.*

### 🛡️ Escalações e Transferências (Fantasy)
| Método | Endpoint | Autenticação | Descrição |
| :--- | :--- | :---: | :--- |
| **GET** | `/api/lineups/` | **Sim** | Lista todas as escalações do usuário logado (filtro: `?stage=<id>`). |
| **POST** | `/api/lineups/` | **Sim** | Escala um time para uma fase específica. |
| **GET** | `/api/lineups/by-stage/<stage_id>/` | **Sim** | Retorna a escalação do usuário para uma fase específica. |
| **GET** | `/api/lineups/<id>/score-history/` | **Sim** | Detalha os pontos gerados por cada jogador escalado naquela fase (pontos do capitão vêm dobrados). |
| **PUT/PATCH** | `/api/lineups/<id>/` | **Sim** | Atualiza a escalação (gera de forma transparente registros de `FantasyTransfer` para novos jogadores). |
| **GET** | `/api/transfers/` | **Sim** | Lista o histórico de trocas do usuário logado. |

> [!IMPORTANT]
> **Payload de Criação de Escalação (`POST /api/lineups/`):**
> ```json
> {
>   "stage": 1,
>   "captain_id": 25,
>   "player_ids": [25, 26, 27, 28, 29]
> }
> ```
> *Nota: O ID do capitão (`captain_id`) deve obrigatoriamente estar contido na lista de jogadores (`player_ids`).*

### 🏆 Rankings e Amigos
| Método | Endpoint | Autenticação | Descrição |
| :--- | :--- | :---: | :--- |
| **GET** | `/api/ranking/global/` | **Sim** | Retorna a lista de todos os usuários ordenados por pontuação decrescente. |
| **GET** | `/api/ranking/friends/` | **Sim** | Retorna a lista de amigos do usuário (incluindo ele mesmo) ordenados por pontuação. |
| **POST** | `/api/ranking/friends/add/` | **Sim** | Adiciona um amigo informando o payload `{"username": "nome_do_amigo"}`. |

### ⚽ Dados de Futebol Real (Sincronizados)
Todos os endpoints abaixo suportam filtros via Query Parameters (ex: `?country=Brazil`, `?status=FT`, `?position=Attacker`).
- `GET /api/teams/` - Listar seleções/equipes
- `GET /api/players/` - Listar jogadores reais
- `GET /api/competitions/` - Listar campeonatos cadastrados
- `GET /api/stages/` - Listar fases dos campeonatos (Grupo A, Final, etc.)
- `GET /api/fixtures/` - Listar partidas e confrontos
- `GET /api/player-statistics/` - Listar estatísticas de desempenho por jogador
- `GET /api/team-statistics/` - Listar estatísticas de desempenho por equipe

---

## 🧪 Como Rodar os Testes

Para validar a integridade da lógica de negócios, endpoints e regras do fantasy game:

```bash
# Rodar testes do módulo de usuários
.venv/bin/python src/manage.py test apps.users

# Rodar testes do módulo de futebol
.venv/bin/python src/manage.py test apps.football

# Rodar testes do módulo de pontuações/escalações
.venv/bin/python src/manage.py test apps.scores

# Rodar todos os testes do projeto
.venv/bin/python src/manage.py test
```
