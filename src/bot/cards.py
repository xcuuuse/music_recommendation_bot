from html import escape

from src.base.entities import Album, AlbumScore, RatedAlbum

DESCRIPTION_LIMIT = 500

def _album_header(album: Album) -> list[str]:
    artists = escape(", ".join(album.artists)) or "unknown author"
    year = f" ({album.year})" if album.year else ""
    lines = [f"💿 <b>{escape(album.title)}</b>{year}", f"🎤 {artists}"]
    if album.genres:
        lines.append(f" {escape(', '.join(album.genres))}")
    return lines

def _description(album: Album) -> str:
    text = album.description.strip()
    if len(text) > DESCRIPTION_LIMIT:
        text = text[:DESCRIPTION_LIMIT].rsplit(" ", 1)[0] + "..."
    return escape(text)

def _reasons(album: Album, score: AlbumScore) -> list[str]:
    reasons: list[str] = []
    if score.vector_score >= 0.8:
        reasons.append("🎯 по описанию - один из самых близких к вашему вкусу")
    elif score.vector_score >= 0.5:
        reasons.append("🎯 по описанию похож на то, что вам нравится")
    if score.artist_score > 0:
        reasons.append("❤️ вам нравится этот исполнитель")
    elif score.artist_score < 0:
        reasons.append("🤔 прошлые альбомы исполнителя вам не очень зашли - но вдруг этот")
    if score.onboarding_genre_score > 0:
        reasons.append("жанр из ваших предпочтений")
    if score.genre_score > 0:
        reasons.append("похож по жанру на то, что вы высоко оценили")
    if score.era_score > 0 and album.year:
        reasons.append(f"{album.year // 10 * 10}-е - ваше десятилетие")
    if score.community_score > 0:
        reasons.append("👥 нравится слушателям с похожим вкусом")
    return reasons or [" пробуем что-то новое для вас"]

def recommendation_card(album: Album, score: AlbumScore) -> str:
    parts = _album_header(album)
    if album.description:
        parts += ["", _description(album)]
    parts += ["", "<b>This album, cause:</b>"]
    parts += [f"• {r}" for r in _reasons(album, score)]
    parts += ["", f"<i>Total score: {score.total:.2f}</i>"]
    return "\n".join(parts)

def search_card(album: Album, others: list[Album]) -> str:
    parts = _album_header(album)
    if album.description:
        parts += ["", _description(album)]
    if others:
        parts += ["", "<b>You can also like:</b>"]
        parts += [
            f". {escape(a.title)} - {escape(', '.join(a.artists))}" for a in others
        ]
    return "\n".join(parts)

def stars(score: int) -> str:
    return "★" * score + "☆" * (5 - score)

def history_text(items: list[RatedAlbum]) -> str:
    if not items:
        return "Start rating with /recommend"
    lines = ["<b>Your latest ratings:</b>", ""]
    for it in items:
        year = f", {it.year}" if it.year else ""
        lines.append(
            f"{stars(it.score)} {escape(it.title)} - {escape(', '.join(it.artists))}{year}"
        )
    return '\n'.join(lines)