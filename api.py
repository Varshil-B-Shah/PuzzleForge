import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()  # must be before any project imports that read env vars

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from db import database
from chessboard.board import ChessBoard
from memory.level1 import AnnotationList
from ai import engine
from memory import level2, level3


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title="PuzzleForge API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory game store (single-user local app) ──────────────────────────────
_games: dict[str, dict] = {}


# ── Models ────────────────────────────────────────────────────────────────────
class StartResponse(BaseModel):
    game_id: str
    fen: str


class MoveRequest(BaseModel):
    game_id: str
    uci: str


class MoveResponse(BaseModel):
    fen: str
    ai_move: str
    observation: str
    game_over: bool
    result: str | None
    last_move: str
    move_log: list[dict]


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.post("/api/game/start", response_model=StartResponse)
def start_game():
    game_id = str(uuid.uuid4())
    board = ChessBoard()
    _games[game_id] = {
        "game_id": game_id,
        "board": board,
        "level1": AnnotationList(),
        "move_count": 0,
        "move_log": [],
    }
    return StartResponse(game_id=game_id, fen=board.get_fen())


@app.post("/api/game/move", response_model=MoveResponse)
def make_move(req: MoveRequest):
    state = _games.get(req.game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")

    board: ChessBoard = state["board"]
    level1_mem: AnnotationList = state["level1"]

    # Player move
    if not board.push_move(req.uci):
        raise HTTPException(status_code=400, detail=f"Illegal move: {req.uci}")

    if board.is_game_over():
        result = board.get_result() or "draw"
        _end_game(state, board, result)
        return MoveResponse(
            fen=board.get_fen(), ai_move="", observation="",
            game_over=True, result=result,
            last_move=req.uci, move_log=state["move_log"],
        )

    # AI move
    level2_report = _load_level2_report()
    level3_profile = _load_level3_profile()

    ai_uci, observation = engine.get_ai_move(
        board, level1_mem, level2_report, level3_profile, player_last_move=req.uci
    )
    board.push_move(ai_uci)

    level1_mem.add_annotation(board.fullmove_number, req.uci, ai_uci, observation)
    if level1_mem.should_compress(board.fullmove_number):
        try:
            level1_mem.compress()
        except Exception:
            pass

    state["move_log"].append({"player": req.uci, "ai": ai_uci, "obs": observation})
    state["move_count"] += 1

    game_over = board.is_game_over()
    result = None
    if game_over:
        result = board.get_result() or "draw"
        _end_game(state, board, result)

    return MoveResponse(
        fen=board.get_fen(), ai_move=ai_uci, observation=observation,
        game_over=game_over, result=result,
        last_move=ai_uci, move_log=state["move_log"],
    )


# ── Helpers ───────────────────────────────────────────────────────────────────
def _load_level2_report() -> str | None:
    reports = database.get_level2_reports(1)
    return reports[0] if reports else None


def _load_level3_profile() -> str | None:
    profile = database.get_level3_profile()
    return profile["full_profile"] if profile else None


def _end_game(state: dict, board: ChessBoard, result: str) -> None:
    game_id = state["game_id"]
    level1_mem: AnnotationList = state["level1"]
    game_number = database.get_game_count() + 1

    try:
        database.save_game(game_id, game_number, board.get_pgn(), result, state["move_count"], "{}")
    except Exception:
        return

    actual_count = database.get_game_count()
    l1_ctx = level1_mem.get_context_string()

    try:
        level2.update_after_game(l1_ctx, result, game_id, actual_count)
    except Exception:
        pass

    if level3.should_update(actual_count):
        try:
            level3.update_profile(database.get_level2_reports(5))
        except Exception:
            pass

    _games.pop(game_id, None)


# ── Serve React build as SPA — must be LAST so /api/* routes win ─────────────
app.mount("/", StaticFiles(directory="ui/chess_frontend/build", html=True), name="spa")
