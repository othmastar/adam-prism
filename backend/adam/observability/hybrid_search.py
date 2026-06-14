"""
[PHASE6] Hybrid search combining BM25 (sparse) + dense vector search.
Better than either alone: BM25 catches exact keywords,
dense vectors catch semantic similarity.
"""
from __future__ import annotations

import logging
import math
import re
from collections import Counter

logger = logging.getLogger("adam_prism.hybrid_search")


class BM25:
    """
    [PHASE6] BM25 (Best Matching 25) implementation.
    Classic IR algorithm for keyword-based relevance.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._doc_freqs: dict[str, int] = {}
        self._doc_lens: list[int] = []
        self._avg_dl: float = 0.0
        self._n_docs: int = 0
        self._docs: list[str] = []  # original text
        self._doc_tokens: list[list[str]] = []

    def _tokenize(self, text: str) -> list[str]:
        # [PHASE6] Arabic + English tokenizer
        # Split on whitespace, keep Arabic words together
        text = text.lower()
        # Keep Arabic letters together, split on non-letters
        tokens = re.findall(r"[\u0600-\u06FF]+|[a-z0-9]+", text)
        return tokens

    def fit(self, documents: list[str]) -> BM25:
        """[PHASE6] Build index from documents."""
        self._docs = list(documents)
        self._doc_tokens = [self._tokenize(d) for d in documents]
        self._n_docs = len(documents)
        self._doc_lens = [len(toks) for toks in self._doc_tokens]
        self._avg_dl = (
            sum(self._doc_lens) / self._n_docs if self._n_docs > 0 else 0
        )

        # Document frequency: how many docs contain each term
        self._doc_freqs = Counter()
        for tokens in self._doc_tokens:
            unique = set(tokens)
            for term in unique:
                self._doc_freqs[term] += 1
        return self

    def score(self, query: str, top_k: int = 10) -> list[tuple[int, float]]:
        """[PHASE6] Score documents against a query. Returns (doc_idx, score)."""
        query_tokens = self._tokenize(query)
        scores = [0.0] * self._n_docs

        for q in query_tokens:
            df = self._doc_freqs.get(q, 0)
            if df == 0:
                continue
            idf = math.log((self._n_docs - df + 0.5) / (df + 0.5) + 1)

            for i, doc_tokens in enumerate(self._doc_tokens):
                tf = doc_tokens.count(q)
                if tf == 0:
                    continue
                dl = self._doc_lens[i]
                norm = 1 - self.b + self.b * dl / (self._avg_dl or 1)
                score = idf * (tf * (self.k1 + 1)) / (tf + self.k1 * norm)
                scores[i] += score

        # Return top-k by score
        ranked = sorted(enumerate(scores), key=lambda x: -x[1])
        return [(i, s) for i, s in ranked[:top_k] if s > 0]


class HybridSearcher:
    """
    [PHASE6] Combine BM25 (sparse) + dense vector search.
    Reciprocal Rank Fusion (RRF) for combining ranked lists.
    """

    def __init__(self, k: int = 60):
        self.bm25 = BM25()
        self.k = k  # RRF constant

    def fit(self, documents: list[str]) -> HybridSearcher:
        """[PHASE6] Build BM25 index."""
        self.bm25.fit(documents)
        return self

    def search(
        self,
        query: str,
        dense_ranker: list[tuple[int, float]] | None = None,
        top_k: int = 10,
    ) -> list[tuple[int, float, str]]:
        """
        [PHASE6] Hybrid search.

        Args:
            query: The search query
            dense_ranker: Pre-computed dense search results: [(doc_idx, score), ...]
            top_k: Number of results to return

        Returns:
            [(doc_idx, fused_score, source), ...]
        """
        # BM25 results
        bm25_results = self.bm25.score(query, top_k=top_k * 2)
        bm25_ranks = {idx: rank for rank, (idx, _) in enumerate(bm25_results)}

        # Dense results
        if dense_ranker is None:
            dense_ranks = {}
        else:
            dense_ranks = {idx: rank for rank, (idx, _) in enumerate(dense_ranker)}

        # Reciprocal Rank Fusion
        all_indices = set(bm25_ranks.keys()) | set(dense_ranks.keys())
        fused = []
        for idx in all_indices:
            rrf_score = 0.0
            sources = []
            if idx in bm25_ranks:
                rrf_score += 1.0 / (self.k + bm25_ranks[idx])
                sources.append("bm25")
            if idx in dense_ranks:
                rrf_score += 1.0 / (self.k + dense_ranks[idx])
                sources.append("dense")
            fused.append((idx, rrf_score, "+".join(sources)))

        # Sort by fused score
        fused.sort(key=lambda x: -x[1])
        return fused[:top_k]
