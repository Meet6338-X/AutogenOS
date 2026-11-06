"""
Local Vector Search and Semantic Indexing Component.
Provides zero-cost, persistent vector retrieval using TF-IDF and dense embeddings.
Powers Tool Attention semantic gating and EchoPath trajectory search.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger("autogenos.vector_search")


class LocalVectorStore:
    """
    In-memory and file-persisted semantic vector index.
    Sub-millisecond retrieval with zero cloud dependency.
    """

    def __init__(self, storage_path: Optional[str | Path] = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self.documents: List[Dict[str, Any]] = []
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._tfidf_matrix: Optional[np.ndarray] = None
        self._is_indexed = False

    def add_document(self, doc_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Adds text document to store."""
        self.documents.append({
            "id": doc_id,
            "text": text,
            "metadata": metadata or {}
        })
        self._is_indexed = False

    def build_index(self) -> None:
        """Fits vectorizer and builds dense term-frequency matrix."""
        if not self.documents:
            return

        corpus = [d["text"] for d in self.documents]
        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_features=5000
        )
        self._tfidf_matrix = self._vectorizer.fit_transform(corpus)
        self._is_indexed = True
        logger.debug(f"Built local vector index over {len(self.documents)} documents.")

    def search(self, query: str, top_k: int = 3, min_score: float = 0.1) -> List[Tuple[Dict[str, Any], float]]:
        """
        Executes cosine similarity search over indexed documents.
        Returns: [(document, score), ...]
        """
        if not self._is_indexed or self._vectorizer is None or self._tfidf_matrix is None:
            self.build_index()

        if not self.documents or self._vectorizer is None or self._tfidf_matrix is None:
            return []

        try:
            q_vec = self._vectorizer.transform([query])
            sims = cosine_similarity(q_vec, self._tfidf_matrix).flatten()
            ranked_indices = np.argsort(sims)[::-1]

            results = []
            for idx in ranked_indices[:top_k]:
                score = float(sims[idx])
                if score >= min_score:
                    results.append((self.documents[idx], round(score, 3)))
            return results
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []

    def save(self, file_path: str | Path) -> None:
        """Persists documents to JSON file."""
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.documents, indent=2), encoding="utf-8")

    def load(self, file_path: str | Path) -> None:
        """Loads documents from JSON and rebuilds index."""
        p = Path(file_path)
        if p.exists():
            self.documents = json.loads(p.read_text(encoding="utf-8"))
            self.build_index()
