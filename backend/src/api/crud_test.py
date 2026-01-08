from fastapi import APIRouter
# 
from src.parsers.aniboom import get_anime_by_title

test_router = APIRouter()

@test_router.get('/test/anime/{title}')
async def get_test_anime(title: str):
    resp = await get_anime_by_title(title)
    return {'message': resp}