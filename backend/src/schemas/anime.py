from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PaginatorData(BaseModel):
    limit: int = Field(6, ge=0, le=100)
    offset: int = Field(0, ge=0)


class AnimeResponse(BaseModel):
    """Схема для ответа с данными аниме (без relationships)"""
    id: int
    title: str
    title_original: str
    poster_url: str
    description: Optional[str] = None
    year: Optional[int] = None
    type: str = 'TV'
    episodes_count: Optional[int] = None
    rating: Optional[str] = None
    score: Optional[float] = None
    studio: Optional[str] = None
    status: str

    class Config:
        from_attributes = True  # Для SQLAlchemy моделей


class GenreResponse(BaseModel):
    """Схема для жанра"""
    id: int
    name: str

    class Config:
        from_attributes = True


class PlayerResponse(BaseModel):
    """Схема для плеера"""
    id: int
    embed_url: str
    translator: str
    quality: str

    class Config:
        from_attributes = True


class CommentUserResponse(BaseModel):
    """Схема для пользователя в комментарии"""
    id: int
    username: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    """Схема для комментария"""
    id: int
    text: str
    created_at: datetime
    user: CommentUserResponse

    class Config:
        from_attributes = True


class AnimeDetailResponse(BaseModel):
    """Схема для полных данных аниме с relationships"""
    id: int
    title: str
    title_original: str
    poster_url: str
    description: Optional[str] = None
    year: Optional[int] = None
    type: str = 'TV'
    episodes_count: Optional[int] = None
    rating: Optional[str] = None
    score: Optional[float] = None
    studio: Optional[str] = None
    status: str
    genres: List[GenreResponse] = []
    players: List[PlayerResponse] = []
    comments: List[CommentResponse] = []

    class Config:
        from_attributes = True