"""
Tests for Reciprocal Rank Fusion (RRF).

Verifies that:
  - RRF correctly merges two ranked lists
  - Chunks appearing in both lists get higher scores
  - Results are sorted by RRF score (best first)
  - The formula produces expected scores for known inputs
  - Edge cases (empty lists, single list) are handled
"""

from app.retrieval.fusion import fuse


class TestRRFBasics:
    """Test basic RRF fusion behavior."""

    def test_disjoint_lists(self):
        """Two lists with no overlapping chunks should produce all items."""
        bm25 = [
            ("chunk_a", 5.0, "text a"),
            ("chunk_b", 3.0, "text b"),
        ]
        vector = [
            ("chunk_c", 0.9, "text c"),
            ("chunk_d", 0.7, "text d"),
        ]

        results = fuse(bm25, vector, k=60)

        # Should have all 4 chunks
        assert len(results) == 4
        result_ids = {r.chunk_id for r in results}
        assert result_ids == {"chunk_a", "chunk_b", "chunk_c", "chunk_d"}

    def test_overlapping_chunks_rank_higher(self):
        """Chunks in both lists should get higher RRF scores."""
        bm25 = [
            ("chunk_shared", 5.0, "shared text"),
            ("chunk_bm25_only", 3.0, "bm25 only"),
        ]
        vector = [
            ("chunk_shared", 0.9, "shared text"),
            ("chunk_vector_only", 0.7, "vector only"),
        ]

        results = fuse(bm25, vector, k=60)

        # chunk_shared should be ranked first (highest RRF score)
        assert results[0].chunk_id == "chunk_shared"
        assert results[0].rrf_score > results[1].rrf_score

    def test_sorted_by_score(self):
        """Results should be sorted by RRF score, highest first."""
        bm25 = [("a", 1.0, "a"), ("b", 0.5, "b"), ("c", 0.3, "c")]
        vector = [("d", 0.9, "d"), ("b", 0.8, "b"), ("e", 0.6, "e")]

        results = fuse(bm25, vector, k=60)

        scores = [r.rrf_score for r in results]
        assert scores == sorted(scores, reverse=True)


class TestRRFScoring:
    """Test the RRF scoring formula."""

    def test_known_scores(self):
        """Verify RRF scores against hand-computed expected values."""
        k = 60

        bm25 = [("chunk_x", 5.0, "x")]  # rank 0 → score = 1/(60+1) = 1/61
        vector = [("chunk_x", 0.9, "x")]  # rank 0 → score = 1/(60+1) = 1/61

        results = fuse(bm25, vector, k=k)

        expected_score = 1.0 / (k + 1) + 1.0 / (k + 1)  # 2/61
        assert len(results) == 1
        assert abs(results[0].rrf_score - expected_score) < 1e-10

    def test_rank_positions_matter(self):
        """Higher-ranked items should get higher individual contributions."""
        k = 60

        bm25 = [
            ("rank1", 5.0, "r1"),  # 1/(60+1)
            ("rank2", 4.0, "r2"),  # 1/(60+2)
        ]
        vector = []

        results = fuse(bm25, vector, k=k)

        # rank1 should have higher score than rank2
        rank1 = next(r for r in results if r.chunk_id == "rank1")
        rank2 = next(r for r in results if r.chunk_id == "rank2")
        assert rank1.rrf_score > rank2.rrf_score

    def test_k_parameter_effect(self):
        """Higher k should reduce the difference between rank positions."""
        bm25 = [("a", 5.0, "a"), ("b", 4.0, "b")]

        results_k10 = fuse(bm25, [], k=10)
        results_k1000 = fuse(bm25, [], k=1000)

        # With k=10: scores are 1/11 and 1/12 → diff = 1/132
        diff_k10 = results_k10[0].rrf_score - results_k10[1].rrf_score

        # With k=1000: scores are 1/1001 and 1/1002 → diff ≈ 1/1003002
        diff_k1000 = results_k1000[0].rrf_score - results_k1000[1].rrf_score

        # k=1000 should compress the differences more
        assert diff_k1000 < diff_k10


class TestRRFSources:
    """Test that source tracking works correctly."""

    def test_single_source(self):
        """Items from only one list should have one source."""
        bm25 = [("a", 1.0, "a")]
        vector = [("b", 0.9, "b")]

        results = fuse(bm25, vector, k=60)

        a_result = next(r for r in results if r.chunk_id == "a")
        b_result = next(r for r in results if r.chunk_id == "b")

        assert a_result.sources == ["bm25"]
        assert b_result.sources == ["vector"]

    def test_dual_source(self):
        """Items in both lists should have both sources."""
        bm25 = [("shared", 1.0, "text")]
        vector = [("shared", 0.9, "text")]

        results = fuse(bm25, vector, k=60)

        assert len(results) == 1
        assert "bm25" in results[0].sources
        assert "vector" in results[0].sources


class TestRRFEdgeCases:
    """Test edge cases."""

    def test_empty_both_lists(self):
        """Empty inputs should return empty results."""
        results = fuse([], [], k=60)
        assert results == []

    def test_empty_bm25(self):
        """Empty BM25 list — should still return vector results."""
        vector = [("a", 0.9, "a"), ("b", 0.8, "b")]
        results = fuse([], vector, k=60)
        assert len(results) == 2

    def test_empty_vector(self):
        """Empty vector list — should still return BM25 results."""
        bm25 = [("a", 5.0, "a"), ("b", 3.0, "b")]
        results = fuse(bm25, [], k=60)
        assert len(results) == 2

    def test_single_item_both(self):
        """Single item in both lists."""
        results = fuse([("x", 1.0, "x")], [("x", 0.9, "x")], k=60)
        assert len(results) == 1
        assert results[0].chunk_id == "x"
