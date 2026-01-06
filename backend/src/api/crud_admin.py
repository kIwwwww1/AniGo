from fastapi import APIRouter, Request, HTTPException, status, Depends
from typing import Annotated
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

async def is_admin(request: Request):
    user_type_account = (await get_token(request)).get('type_account')
    if user_type_account not in ['owner', 'admin']:
        return HTTPException(
            status_code=status.HTTP_304_NOT_MODIFIED,
            detail='Вы не админ')
    return True


IsAdminDep = Annotated[bool, Depends(is_admin)]


# @admin_router.delete('delete/user/comment')
# async def delete_comment(is_admin: IsAdminDep, comment: int, session: SessionDep):
