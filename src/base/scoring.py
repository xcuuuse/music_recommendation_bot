from dataclasses import dataclass
import random
from src.base.entities import Signals, AlbumScore, Album

@dataclass(frozen=True)
class Weights:
    vector: float = 1.0
    artist: float = 1.0
    onboarding_per_genre: float = 0.15
    onboarding_cap: float = 0.3
    genre: float = 0.1
    era_per_album: float = 0.03
    era_cap: float = 0.12
    community: float = 0.12
    community_full_confidence: int = 3

DEFAULT_WEIGHTS = Weights()

def _vector_scale(signals: list[Signals]):
    values = [signal.cosine for signal in signals if signal.cosine]
    if not values:
        return lambda _c: 0.0
    low, high = min(values), max(values)
    span = high - low
    if span < 1e-9:
        return lambda c: 0.0 if not c else 1.0
    return lambda c: 0.0 if not c else (c - low) / span

def build_score(album_id: int, s: Signals, vector_norm: float, w: Weights) -> AlbumScore:
    confidence = min(s.peer_count / w.community_full_confidence, 1.0)
    return AlbumScore(
        album_id=album_id,
        vector_score=w.vector * vector_norm,
        artist_score=w.artist * (s.artist_delta or 0.0),
        onboarding_genre_score=min(s.liked_genre_hits * w.onboarding_per_genre, w.onboarding_cap),
        genre_score=w.genre * (s.genre_delta or 0.0),
        era_score=min(s.era_hits * w.era_per_album, w.era_cap),
        community_score=w.community * (s.peer_delta or 0.0) * confidence
    )

def rank(candidates: list[tuple[Album, Signals]], weights: Weights = DEFAULT_WEIGHTS) -> list[tuple[Album, AlbumScore]]:
    normalize = _vector_scale([score for _, score in candidates])
    scored = [
        (album, build_score(album.id, score, normalize(score.cosine), weights)) for album, score in candidates
    ]
    scored.sort(key=lambda p: (p[1].total, random.random()), reverse=True)
    return scored