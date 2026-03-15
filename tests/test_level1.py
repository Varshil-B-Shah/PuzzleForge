import pytest
from memory.level1 import AnnotationList


# ── add_annotation / get_context_string ──────────────────────────────────────

def test_empty_returns_empty_string():
    assert AnnotationList().get_context_string() == ""


def test_single_annotation_numbered():
    al = AnnotationList()
    al.add_annotation(1, "e2e4", "e7e5", "Player opens aggressively.")
    ctx = al.get_context_string()
    assert ctx.startswith("1.")
    assert "e2e4" in ctx
    assert "Player opens aggressively." in ctx


def test_multiple_annotations_numbered_sequentially():
    al = AnnotationList()
    al.add_annotation(1, "e2e4", "e7e5", "Obs 1")
    al.add_annotation(2, "d2d4", "d7d5", "Obs 2")
    al.add_annotation(3, "g1f3", "g8f6", "Obs 3")
    ctx = al.get_context_string()
    assert "1." in ctx
    assert "2." in ctx
    assert "3." in ctx


def test_caps_at_20_entries():
    al = AnnotationList()
    for i in range(1, 26):
        al.add_annotation(i, "e2e4", "e7e5", f"Obs {i}")
    ctx = al.get_context_string()
    lines = [l for l in ctx.splitlines() if l.strip()]
    assert len(lines) == 20
    # Oldest entries dropped — entry 5 should be gone
    assert "Obs 4" not in ctx
    assert "Obs 5" in ctx or "Obs 6" in ctx  # last 20 of 25 kept


def test_cap_at_20_exactly():
    al = AnnotationList()
    for i in range(1, 26):
        al.add_annotation(i, "e2e4", "e7e5", f"Obs {i}")
    ctx = al.get_context_string()
    lines = [l for l in ctx.splitlines() if l.strip()]
    assert len(lines) == 20
    assert "Obs 4" not in ctx


# ── should_compress ───────────────────────────────────────────────────────────

def test_should_compress_at_10():
    assert AnnotationList().should_compress(10) is True


def test_should_compress_at_20():
    assert AnnotationList().should_compress(20) is True


def test_should_compress_false_at_0():
    assert AnnotationList().should_compress(0) is False


def test_should_compress_false_mid_cycle():
    assert AnnotationList().should_compress(7) is False
    assert AnnotationList().should_compress(11) is False


# ── compress ─────────────────────────────────────────────────────────────────

def test_compress_idempotent_when_fewer_than_10():
    al = AnnotationList()
    for i in range(1, 6):
        al.add_annotation(i, "e2e4", "e7e5", f"Obs {i}")
    al.compress()  # must not call LLM — no mock needed
    ctx = al.get_context_string()
    assert "Obs 1" in ctx


def test_compress_replaces_oldest_10_with_summary(monkeypatch):
    from unittest.mock import patch
    al = AnnotationList()
    for i in range(1, 16):
        al.add_annotation(i, "e2e4", "e7e5", f"Obs {i}")

    with patch("memory.level1.client.call_llm", return_value="Player likes e4 openings."):
        al.compress()

    ctx = al.get_context_string()
    assert "[SUMMARY]" in ctx
    assert "Player likes e4 openings." in ctx
    # Oldest 10 annotations replaced — obs 1-10 gone (use move number to avoid substring matches)
    assert "Move 1 " not in ctx
    assert "Move 10 " not in ctx
    # Newer ones kept
    assert "Obs 11" in ctx


def test_compress_calls_gpt4o_mini(monkeypatch):
    from unittest.mock import patch
    al = AnnotationList()
    for i in range(1, 16):
        al.add_annotation(i, "e2e4", "e7e5", f"Obs {i}")

    with patch("memory.level1.client.call_llm") as mock_llm:
        mock_llm.return_value = "Summary text."
        al.compress()
    assert mock_llm.call_args[0][1] == "gpt-4o-mini"


def test_compress_summary_appears_in_numbered_list(monkeypatch):
    from unittest.mock import patch
    al = AnnotationList()
    for i in range(1, 16):
        al.add_annotation(i, "e2e4", "e7e5", f"Obs {i}")

    with patch("memory.level1.client.call_llm", return_value="Tactical summary."):
        al.compress()

    ctx = al.get_context_string()
    # Summary entry should be numbered
    import re
    lines = [l.strip() for l in ctx.splitlines() if l.strip()]
    assert lines[0].startswith("1.")
