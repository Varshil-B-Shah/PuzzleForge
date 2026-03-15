from ai import client
from ai.prompts import build_level1_compression_prompt


class AnnotationList:
    def __init__(self):
        self._entries = []  # list of dicts: {type: "annotation"|"summary", text: str}

    def add_annotation(self, move_number: int, player_uci: str, ai_uci: str, observation: str):
        text = f"Move {move_number} (you: {player_uci}, AI: {ai_uci}): {observation}"
        self._entries.append({"type": "annotation", "text": text})

    def should_compress(self, move_number: int) -> bool:
        return move_number > 0 and move_number % 10 == 0

    def compress(self):
        """Replace oldest 10 entries with a GPT-4o-mini summary. No-op if < 10 entries."""
        if len(self._entries) < 10:
            return
        oldest = self._entries[:10]
        rest = self._entries[10:]
        raw_texts = [e["text"] for e in oldest]
        summary_text = client.call_llm(
            build_level1_compression_prompt(raw_texts), "gpt-4o-mini", max_tokens=200
        )
        self._entries = [{"type": "summary", "text": summary_text}] + rest

    def get_context_string(self) -> str:
        """Numbered list of last 20 entries. Summaries prefixed with [SUMMARY]."""
        recent = self._entries[-20:]
        lines = []
        for i, entry in enumerate(recent, start=1):
            if entry["type"] == "summary":
                lines.append(f"{i}. [SUMMARY] {entry['text']}")
            else:
                lines.append(f"{i}. {entry['text']}")
        return "\n".join(lines)
