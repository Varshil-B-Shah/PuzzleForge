import { useState, useEffect, useCallback, useRef } from "react";
import { Chessboard } from "react-chessboard";
import { Chess } from "chess.js";

const BOARD_WIDTH = 480;

export default function App() {
  const [game, setGame]         = useState(new Chess());
  const [fen, setFen]           = useState("start");
  const [lastMove, setLastMove] = useState(null);
  const [status, setStatus]     = useState("Loading…");
  const [moveLog, setMoveLog]   = useState([]);
  const [gameOver, setGameOver] = useState(false);
  const [result, setResult]     = useState(null);
  const [moveKey, setMoveKey]   = useState(0);
  const gameIdRef               = useRef(null);
  const busyRef                 = useRef(false);
  const [tiltMode, setTiltMode]       = useState(null);
  const [debriefText, setDebriefText] = useState(null);
  const [debriefLoaded, setDebriefLoaded] = useState(false);

  // ── Start / restart game ──────────────────────────────────────────────────
  const startGame = useCallback(async () => {
    busyRef.current = false;
    setGameOver(false);
    setResult(null);
    setMoveLog([]);
    setLastMove(null);
    setStatus("Starting game…");
    setTiltMode(null);
    setDebriefText(null);
    setDebriefLoaded(false);
    try {
      const res = await fetch("/api/game/start", { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      gameIdRef.current = data.game_id;
      const fresh = new Chess(data.fen);
      setGame(fresh);
      setFen(data.fen);
      setMoveKey(k => k + 1);
      setStatus("Your turn — drag a piece to move");
    } catch (err) {
      setStatus(`Could not connect to game server: ${err.message}`);
    }
  }, []);

  useEffect(() => { startGame(); }, [startGame]);

  // ── Piece drop handler ────────────────────────────────────────────────────
  const onDrop = useCallback((sourceSquare, targetSquare, piece) => {
    if (busyRef.current || gameOver || !gameIdRef.current) return false;

    // Validate locally so the board doesn't snap-back on legal moves
    const promo = piece?.[1]?.toLowerCase();
    const gameCopy = new Chess(game.fen());
    let move;
    try {
      move = gameCopy.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: promo === "p" || !promo ? "q" : promo,
      });
    } catch { return false; }
    if (!move) return false;

    const uci = sourceSquare + targetSquare + (move.promotion ?? "");

    // Optimistic: show player move immediately
    setGame(gameCopy);
    setFen(gameCopy.fen());
    setLastMove({ from: sourceSquare, to: targetSquare });
    setMoveKey(k => k + 1);
    setStatus("AI is thinking…");
    busyRef.current = true;

    fetch("/api/game/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: gameIdRef.current, uci }),
    })
      .then(async res => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
          throw new Error(err.detail ?? "Move failed");
        }
        return res.json();
      })
      .then(data => {
        const updated = new Chess(data.fen);
        setGame(updated);
        setFen(data.fen);
        setMoveKey(k => k + 1);
        setMoveLog(data.move_log ?? []);
        if (data.tilt_mode !== undefined) setTiltMode(data.tilt_mode);
        if (data.last_move?.length >= 4) {
          setLastMove({ from: data.last_move.slice(0, 2), to: data.last_move.slice(2, 4) });
        }
        if (data.game_over) {
          setGameOver(true);
          setResult(data.result);
          const label = { win: "You win! 🎉", loss: "AI wins.", draw: "Draw." }[data.result] ?? data.result;
          setStatus(`Game over — ${label}`);
          // Fetch debrief
          fetch("/api/game/debrief", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ game_id: gameIdRef.current }),
          })
            .then(r => r.json())
            .then(d => { setDebriefText(d.analysis); setDebriefLoaded(true); })
            .catch(() => { setDebriefText(null); setDebriefLoaded(true); });
        } else {
          setStatus("Your turn — drag a piece to move");
        }
      })
      .catch(err => {
        // Roll back optimistic update
        const prev = new Chess(fen);
        setGame(prev);
        setFen(fen);
        setMoveKey(k => k + 1);
        setStatus(`Error: ${err.message}`);
      })
      .finally(() => { busyRef.current = false; });

    return true;
  }, [game, fen, gameOver]);

  // ── Square highlight ──────────────────────────────────────────────────────
  const squareStyles = lastMove
    ? {
        [lastMove.from]: { backgroundColor: "rgba(255,215,0,0.5)" },
        [lastMove.to]:   { backgroundColor: "rgba(255,215,0,0.5)" },
      }
    : {};

  const resultLabel = result
    ? { win: "You win! 🎉", loss: "AI wins.", draw: "Draw." }[result] ?? result
    : null;

  return (
    <div style={{ padding: "16px", fontFamily: "sans-serif", background: "#11111b", minHeight: "100vh" }}>
      <h2 style={{ color: "#cdd6f4", marginBottom: "12px", fontSize: "18px", fontWeight: 700 }}>
        PuzzleForge Chess
      </h2>

      {/* Board */}
      <Chessboard
        key={moveKey}
        id="puzzleforge-board"
        position={fen}
        onPieceDrop={onDrop}
        boardWidth={BOARD_WIDTH}
        customSquareStyles={squareStyles}
        customBoardStyle={{ borderRadius: "6px", boxShadow: "0 4px 24px rgba(0,0,0,0.5)" }}
        customDarkSquareStyle={{ backgroundColor: "#4a4a4a" }}
        customLightSquareStyle={{ backgroundColor: "#d9d9d9" }}
        areArrowsAllowed
      />

      {/* Status bar */}
      <div style={{
        marginTop: "8px", padding: "8px 12px", textAlign: "center",
        background: "#1e1e2e", color: "#cdd6f4", borderRadius: "6px", fontSize: "13px",
      }}>
        {status}
      </div>

      {/* Tilt badge */}
      {tiltMode === "exploit" && (
        <div style={{
          marginTop: "6px", padding: "5px 12px", textAlign: "center",
          background: "#7f1d1d", color: "#fca5a5", borderRadius: "6px",
          fontSize: "12px", fontWeight: "bold",
        }}>
          ⚡ Exploit Mode
        </div>
      )}
      {tiltMode === "cooling" && (
        <div style={{
          marginTop: "6px", padding: "5px 12px", textAlign: "center",
          background: "#1e3a5f", color: "#93c5fd", borderRadius: "6px",
          fontSize: "12px", fontWeight: "bold",
        }}>
          😌 Cooling Down
        </div>
      )}

      {/* Game over banner */}
      {gameOver && (
        <div style={{
          marginTop: "12px", padding: "16px", background: "#313244",
          borderRadius: "8px", textAlign: "center",
        }}>
          <div style={{ color: "#cba6f7", fontWeight: "bold", fontSize: "16px", marginBottom: "10px" }}>
            {resultLabel}
          </div>
          {!debriefLoaded ? (
            <div style={{ color: "#a6adc8", fontSize: "13px", marginBottom: "10px" }}>
              Analysing your game…
            </div>
          ) : (
            <>
              {debriefText && (
                <div style={{
                  color: "#a6adc8", fontSize: "12px", fontStyle: "italic",
                  marginBottom: "12px", lineHeight: "1.5",
                }}>
                  {debriefText}
                </div>
              )}
              <button onClick={startGame} style={{
                padding: "8px 28px", background: "#89b4fa", color: "#1e1e2e",
                border: "none", borderRadius: "6px", cursor: "pointer",
                fontWeight: "bold", fontSize: "14px",
              }}>
                New Game
              </button>
            </>
          )}
        </div>
      )}

      {/* Move log */}
      {moveLog.length > 0 && (
        <div style={{
          marginTop: "16px", background: "#181825", borderRadius: "8px",
          padding: "12px", maxHeight: "260px", overflowY: "auto",
        }}>
          <div style={{ color: "#a6adc8", fontSize: "11px", marginBottom: "8px", fontWeight: "bold", letterSpacing: "0.05em" }}>
            MOVE LOG
          </div>
          {[...moveLog].reverse().slice(0, 12).map((entry, i) => {
            const num = moveLog.length - i;
            return (
              <div key={num} style={{ marginBottom: "10px" }}>
                <div style={{ color: "#cdd6f4", fontSize: "13px" }}>
                  <strong style={{ color: "#a6adc8" }}>{num}.</strong>{" "}
                  You: <code style={{ color: "#89b4fa", background: "#1e1e2e", padding: "1px 4px", borderRadius: "3px" }}>{entry.player}</code>
                  {" → "}
                  AI: <code style={{ color: "#f38ba8", background: "#1e1e2e", padding: "1px 4px", borderRadius: "3px" }}>{entry.ai}</code>
                </div>
                {entry.obs && (
                  <div style={{
                    color: entry.is_trap ? "#f9a825" : "#a6adc8",
                    fontSize: "12px", marginTop: "3px", paddingLeft: "14px", fontStyle: "italic",
                  }}>
                    {entry.obs}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
