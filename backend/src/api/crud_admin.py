from fastapi import APIRouter
from src.models.users import UserModel
from src.dependencies.all_dep import SessionDep, UserExistsDep

from src.services.users import (add_user, create_user_comment, 
                                create_rating, get_user_by_id, login_user,
                                toggle_favorite, check_favorite, check_rating, get_user_favorites,
                                get_user_by_username, verify_email, change_username, change_password,
                                set_best_anime, get_user_best_anime, remove_best_anime,
                                add_new_user_photo)
from src.schemas.user import (CreateNewUser, CreateUserComment, 
                              CreateUserRating, LoginUser, 
                              CreateUserFavorite, UserName, ChangeUserPassword, CreateBestUserAnime)
from src.auth.auth import get_token, delete_token


admin_router = APIRouter(prefix='/admin', tags=['AdminPanel'])


async def delete_comment(commend: int, session: SessionDep):
    pass