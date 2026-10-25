class Embedder:
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name, device="cpu")
        self._use_prefixes = "e5" in model_name.lower()

    def _prefix(self, kind: str) -> str:
        return f"{kind}: " if self._use_prefixes else ""

    def embed_passages(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        vectors = self._model.encode(
            [self._prefix("passage") + t for t in texts],
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        vector = self._model.encode(
            self._prefix("query") + text, normalize_embeddings=True
        )
        return vector.tolist()
