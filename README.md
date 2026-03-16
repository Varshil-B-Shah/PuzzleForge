# PuzzleForge Chess

> An adaptive chess AI that learns *your* habits across sessions and uses them against you — powered by a three-level memory system inspired by [Nested Learning (NeurIPS 2025)](https://arxiv.org/abs/2412.09279).

---

## The Problem: Catastrophic Forgetting

Traditional AI systems suffer from **catastrophic forgetting** — every time they encounter new information, they overwrite what they already learned. A chess AI that retrains on your games will forget your early tendencies as soon as you play a few new ones.

PuzzleForge solves this with a **Continuum Memory System** — three memory layers operating at different timescales, each feeding into the next, so the AI never forgets who you are.

---

## How the Memory System Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     Every Move (in-game)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LEVEL 1 — Annotation List  (pure Python, in-memory)     │   │
│  │  • Records every move pair + AI's observation            │   │
│  │  • Compresses oldest 10 entries into a summary via GPT   │   │
│  │    every 10 moves  (sliding window, never loses context) │   │
│  │  • Lives only for the current game                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │ passed to AI on every move
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    After Each Game                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LEVEL 2 — Scouting Report  (SQLite, updated by GPT-4.1) │   │
│  │  • Synthesises Level 1 context + game result             │   │
│  │  • Maintains a living scouting report: opening prefs,    │   │
│  │    middlegame tendencies, weaknesses, psychological       │   │
│  │    patterns, exploits attempted                          │   │
│  │  • Each new game UPDATES it (never replaces from scratch)│   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │ loaded at game start as briefing
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Every 5 Games                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LEVEL 3 — Player Profile  (SQLite, single row, GPT-4.1) │   │
│  │  • Deep psychological + strategic profile of the player  │   │
│  │  • Style Name ("The Impatient Attacker")                 │   │
│  │  • Style Class (Aggressive-Tactical / Passive-Positional │   │
│  │    / Chaotic / Balanced)                                 │   │
│  │  • Counter-Personality: how the AI should play against   │   │
│  │    this specific person                                  │   │
│  │  • Target win rate (calibrated difficulty)               │   │
│  │  • Stored as INSERT OR REPLACE id=1 — one profile,       │   │
│  │    always the latest synthesis                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │ loaded at game start as identity
                            ▼
                    ┌───────────────┐
                    │  AI Engine    │
                    │  (gpt-4.1-mini│
                    │   per move)   │
                    └───────────────┘
```

### Why Three Levels?

| Problem | Solution |
|---|---|
| AI forgets what you did 20 moves ago in a long game | Level 1 compression: oldest moves summarised, never dropped |
| AI forgets your style between games | Level 2 scouting report persists to SQLite across sessions |
| One atypical game throws off the whole model | Level 3 only updates every 5 games — stable, noise-resistant profile |
| Hard train/test boundary causes forgetting | No retraining ever — GPT synthesises incrementally on top of existing context |
| AI plays the same against everyone | Level 3 generates a personalised counter-strategy unique to you |

### How Each Level Feeds the Next

```
Game N:      Level 1 builds  ──► fed to Level 2 after game ends
             Level 2 updates ──► fed to Level 3 every 5 games
             Level 3 updates ──► loaded at start of Game N+1 as strategic identity

Game N+1:    AI enters knowing:
             • Who you are (Level 3 profile — stable, built over 5+ games)
             • How your last few games went (Level 2 scouting — updated each game)
             • Nothing yet about this game (Level 1 starts fresh — browser-refresh safe)
```

This is the core of **Nested Learning**: memory at multiple frequencies, each level stabilising the level above it, with no hard boundary between "training" and "inference."

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│              Streamlit (port 8501)               │
│  ┌─────────────┐        ┌───────────────────┐    │
│  │  Game Page  │        │   Profile Page    │    │
│  │  (iframe ──►│        │  win rate chart   │    │
│  │  :8000)     │        │  style card       │    │
│  └─────────────┘        │  scouting report  │    │
│                         │  reset button     │    │
│                         └───────────────────┘    │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│              FastAPI (port 8000)                 │
│                                                  │
│  POST /api/game/start  ──► new game_id + FEN     │
│  POST /api/game/move   ──► player+AI move,       │
│                            observation, new FEN  │
│                                                  │
│  Serves React build at /                         │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│              React (Vite build)                  │
│  react-chessboard  ──  drag-and-drop board       │
│  chess.js          ──  local move validation     │
│  fetch /api/game/* ──  talks to FastAPI          │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│              Python Core                         │
│  chessboard/   python-chess wrapper (UCI)        │
│  ai/           prompts, parser, client, engine   │
│  memory/       level1, level2, level3            │
│  db/           SQLite (3 tables)                 │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│              Azure OpenAI                        │
│  gpt-4.1       ──  Level 2 & 3 updates          │
│  gpt-4.1-mini  ──  every in-game move            │
└──────────────────────────────────────────────────┘
```

### Module Boundaries

| Module | Responsibility | Can import |
|---|---|---|
| `chessboard/` | Board logic, legal moves, FEN/PGN | `python-chess` only |
| `ai/` | Prompts, parsing, LLM calls, move engine | `chessboard/`, `memory/` |
| `memory/` | Annotation list, scouting, profile | `ai/`, `db/` |
| `db/` | SQLite CRUD | stdlib only |
| `ui/` | Streamlit pages | everything |
| `api.py` | FastAPI endpoints | everything |

---

## Database Schema

```sql
-- One row per completed game
CREATE TABLE game_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id       TEXT UNIQUE,
    game_number   INTEGER,
    pgn           TEXT,
    result        TEXT,     -- 'win' | 'loss' | 'draw'
    move_count    INTEGER,
    metadata      TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- One row per completed game — running scouting report
CREATE TABLE level2_scouting (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id       TEXT,
    game_number   INTEGER,
    result        TEXT,
    report_text   TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Always exactly ONE row — the current player profile
CREATE TABLE level3_profile (
    id                INTEGER PRIMARY KEY DEFAULT 1,
    style_name        TEXT,
    style_class       TEXT,
    full_profile      TEXT,
    counter_strategy  TEXT,
    target_win_rate   REAL,
    games_analyzed    INTEGER,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Project Structure

```
PuzzleForge/
├── api.py                    # FastAPI server — game endpoints + serves React
├── app.py                    # Streamlit entry point — Profile page
├── requirements.txt
├── .env                      # your Azure OpenAI keys (not committed)
├── .env.example
│
├── ai/
│   ├── client.py             # Azure OpenAI client (lazy env resolution)
│   ├── engine.py             # move generation with 3-retry + random fallback
│   ├── parser.py             # MOVE:/OBSERVATION: extractor + UCI validation
│   └── prompts.py            # all prompt templates
│
├── chessboard/
│   └── board.py              # ChessBoard wrapper (UCI throughout)
│
├── db/
│   └── database.py           # SQLite — init, save, get, reset
│
├── memory/
│   ├── level1.py             # AnnotationList — in-game, compresses every 10 moves
│   ├── level2.py             # post-game scouting report
│   └── level3.py             # every-5-games deep player profile
│
├── ui/
│   ├── game_page.py          # Streamlit page — embeds React via iframe
│   ├── profile_page.py       # Streamlit page — stats, chart, profile card
│   ├── chess_component.py    # (legacy) Streamlit component wrapper
│   └── chess_frontend/       # React + Vite
│       ├── src/
│       │   ├── App.jsx       # drag-and-drop board, move log, game over
│       │   └── main.jsx
│       ├── build/            # compiled output served by FastAPI
│       ├── package.json
│       └── vite.config.js    # /api proxy → FastAPI in dev mode
│
└── tests/
    ├── conftest.py           # global DB isolation fixture
    ├── test_board.py
    ├── test_client.py
    ├── test_database.py
    ├── test_engine.py
    ├── test_level1.py
    ├── test_level2.py
    ├── test_level3.py
    ├── test_parser.py
    └── test_prompts.py
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- An Azure AI Foundry deployment with `gpt-4.1` and `gpt-4.1-mini`

### 1. Clone and install

```bash
git clone <repo>
cd PuzzleForge

python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
AZURE_OPENAI_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/openai/v1/
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_4O=gpt-4.1
AZURE_OPENAI_DEPLOYMENT_4O_MINI=gpt-4.1-mini
```

### 3. Build the React frontend

```bash
cd ui/chess_frontend
npm install
npm run build
cd ../..
```

### 4. Run

Open **two terminals**:

```bash
# Terminal 1 — Game server
.venv\Scripts\uvicorn api:app --port 8000 --reload

# Terminal 2 — Profile page
.venv\Scripts\streamlit run app.py
```

Open **`http://localhost:8501`** in your browser.

- **Game tab** → drag-and-drop chess board (served from FastAPI at `:8000`)
- **Profile tab** → your style card, win rate chart, scouting report

---

## Running Tests

```bash
pytest tests/ -v
```

All 74 tests pass. Tests use an isolated in-memory SQLite database (global `autouse` fixture in `conftest.py`) so they never touch your real game data.

---

## Key Design Decisions

### UCI everywhere

All moves are passed as UCI strings (`e2e4`, `g1f3`) throughout the entire stack — from `get_legal_moves()` to the LLM prompt to `push_move()`. SAN is only accepted as user input and immediately converted.

### Lazy deployment resolution

`ai/client.py` resolves `AZURE_OPENAI_DEPLOYMENT_4O` inside `call_llm()` at call time, not at import time. This means `load_dotenv()` in `api.py` / `app.py` always runs first.

### Retry logic in one place

`ai/engine.py` is the only place that retries on `ParseError` or `LLMError` (3 attempts, then random legal move). No other layer handles retries.

### Level 3 off-by-one guard

```python
def should_update(completed_game_count):
    return completed_game_count > 0 and completed_game_count % 5 == 0
```

The count is read *after* `save_game` succeeds, so if the save fails, Level 3 never fires on stale data.

### Optimistic UI updates

When you drag a piece, the React board updates immediately (local chess.js validation). The API call happens in the background. If the server rejects the move, the board rolls back. This makes the game feel responsive even when the AI is thinking.

---

## Inspiration

This project is an applied implementation of ideas from:

- **Nested Learning** — Continuum Memory System, multi-frequency memory updates, no hard train/test boundary, self-referential learning loop *(NeurIPS 2025)*
- The insight that **catastrophic forgetting is a boundary problem**: if you never draw a hard line between "what I know" and "what I'm learning," there is no boundary to forget across.

---

## License

MIT
