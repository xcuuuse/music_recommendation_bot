from dataclasses import dataclass, field

@dataclass(frozen=True)
class Album:
    id: int
    title: str
    artists: list[str]
    genres: list[str]
    year: int | None
    description: str = ""


@dataclass(frozen=True)
class AlbumScore:
    album_id: int
    vector_score: float
    artist_score: float
    onboarding_genre_score: float
    genre_score: float
    era_score: float
    community_score: float

    @property
    def total(self):
        return (
            self.vector_score +
            self.artist_score +
            self.onboarding_genre_score +
            self.genre_score +
            self.era_score +
            self.community_score
        )

@dataclass
class User:
    id: int
    username: str | None
    taste_vector: list[float] | None = None
    liked_genres: list[str] = field(default_factory=list)

@dataclass
class RatedAlbum:
    album_id: int
    title: str
    artists: list[str]
    year: int | None
    score: int

@dataclass(frozen=True)
class Signals:
    cosine: float | None
    artist_delta: float | None
    liked_genre_hits: int
    genre_delta: float
    era_hits: int
    peer_delta: float
    peer_count: int