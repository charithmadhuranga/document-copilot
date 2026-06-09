from __future__ import annotations

from app.retrieval.fusion import reciprocal_rank_fusion


def test_empty_results():
    result = reciprocal_rank_fusion([], [])
    assert result == []


def test_only_semantic():
    semantic = [("a", 0.9), ("b", 0.8), ("c", 0.7)]
    result = reciprocal_rank_fusion(semantic, [])
    assert len(result) == 3
    assert result[0][0] == "a"


def test_only_fulltext():
    fulltext = [("x", 0.9), ("y", 0.8)]
    result = reciprocal_rank_fusion([], fulltext)
    assert len(result) == 2
    assert result[0][0] == "x"


def test_fusion_prioritizes_common():
    semantic = [("a", 0.9), ("b", 0.8), ("c", 0.7)]
    fulltext = [("b", 0.9), ("a", 0.8), ("d", 0.7)]
    result = reciprocal_rank_fusion(semantic, fulltext)
    ids = [r[0] for r in result]
    assert ids.index("a") < ids.index("d")
    assert ids.index("b") < ids.index("d")


def test_top_n():
    semantic = [(str(i), 1.0) for i in range(20)]
    fulltext = [(str(i), 1.0) for i in range(5, 25)]
    result = reciprocal_rank_fusion(semantic, fulltext, top_n=5)
    assert len(result) <= 5


def test_scores_are_descending():
    semantic = [("a", 0.9), ("b", 0.8), ("c", 0.7)]
    fulltext = [("d", 0.9), ("e", 0.8)]
    result = reciprocal_rank_fusion(semantic, fulltext)
    scores = [s for _, s in result]
    assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
