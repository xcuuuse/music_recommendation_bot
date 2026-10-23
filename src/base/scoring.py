from dataclasses import dataclass
from src.base.entities import Signals

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
