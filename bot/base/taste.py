import numpy as np

STEP_BY_SCORE: dict[int, float] = {5: 0.3, 4: 0.15, 3: 0.0, 2: -0.15, 1: -0.3}

def _normalize(v: np.ndarray) -> np.ndarray | None:
    normal = float(np.linalg.norm(v))
    return v / normal if normal > 1e-9 else None

def update_taste(taste: list[float], album: list[float], score: int) -> list[float] | None:
    step = STEP_BY_SCORE.get(score, 0.0)
    if step == 0.0 or album is None:
        return taste
    album = np.asarray(album, dtype=np.float32)
    if not taste:
        if step < 0:
            return None
        result = _normalize(album)
        return None if not result else result.tolist()
    user = np.asarray(taste, dtype=np.float32)
    if step > 0:
        new = (1.0 - step) * user + step * album
    else:
        new = user + step * album
    result = _normalize(new)
    return taste if not result else result.tolist()

def centroid(vectors: list[list[float]]) -> list[float] | None:
    if not vectors:
        return None
    result = _normalize(np.asarray(vectors, dtype=np.float32).mean(axis=0))
    return None if not result else result.tolist()