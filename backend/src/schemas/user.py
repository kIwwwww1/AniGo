from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Literal
from datetime import datetime

AccountTypes = Literal['base', 'premium', 'admin', 'owner']

class UserName(BaseModel):
    username: str = Field(min_length=3, max_length=15)

class UserEmail(UserName):
    email: EmailStr

class LoginUser(UserName):
    password: str = Field(min_length=8)

class CreateNewUser(LoginUser, UserEmail):
    password: str = Field(min_length=8)

class UserTypeAccount(BaseModel):
    type_account: AccountTypes
    
class ChangeUserPassword(BaseModel):
    old_password: str = Field(min_length=8)
    one_new_password: str = Field(min_length=8)
    two_new_password: str = Field(min_length=8)


class CreateUserComment(BaseModel):
    text: str = Field(min_length=1, max_length=100)
    anime_id: int

class CreateUserRating(BaseModel):
    rating: int = Field(ge=1, le=10)
    anime_id: int = Field(gt=0)
    
    @field_validator('rating', mode='before')
    @classmethod
    def validate_rating(cls, v):
        """Конвертируем rating в целое число, если это возможно"""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError('rating должен быть целым числом от 1 до 10')
        if isinstance(v, float):
            if v.is_integer():
                return int(v)
            raise ValueError('rating должен быть целым числом, не дробным')
        return v
    
    @field_validator('anime_id', mode='before')
    @classmethod
    def validate_anime_id(cls, v):
        """Конвертируем anime_id в целое число, если это возможно"""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError('anime_id должен быть целым числом')
        if isinstance(v, float):
            if v.is_integer():
                return int(v)
            raise ValueError('anime_id должен быть целым числом, не дробным')
        return v

class CreateUserFavorite(BaseModel):
    anime_id: int = Field(gt=0)
    
    @field_validator('anime_id', mode='before')
    @classmethod
    def validate_anime_id(cls, v):
        """Конвертируем anime_id в целое число, если это возможно"""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError('anime_id должен быть целым числом')
        if isinstance(v, float):
            if v.is_integer():
                return int(v)
            raise ValueError('anime_id должен быть целым числом, не дробным')
        return v

class CreateBestUserAnime(BaseModel):
    anime_id: int = Field(gt=0)
    place: int = Field(ge=1, le=3)  # Место от 1 до 3
    
    @field_validator('anime_id', mode='before')
    @classmethod
    def validate_anime_id(cls, v):
        """Конвертируем anime_id в целое число, если это возможно"""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError('anime_id должен быть целым числом')
        if isinstance(v, float):
            if v.is_integer():
                return int(v)
            raise ValueError('anime_id должен быть целым числом, не дробным')
        return v
    
    @field_validator('place', mode='before')
    @classmethod
    def validate_place(cls, v):
        """Конвертируем place в целое число, если это возможно"""
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError('place должен быть целым числом от 1 до 3')
        if isinstance(v, float):
            if v.is_integer():
                return int(v)
            raise ValueError('place должен быть целым числом, не дробным')
        return v


# Схемы для настроек профиля
class UserProfileSettingsBase(BaseModel):
    username_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description='Hex цвет имени пользователя')
    avatar_border_color: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description='Hex цвет обводки аватарки')
    theme_color_1: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description='Hex цвет первой темы')
    theme_color_2: str | None = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description='Hex цвет второй темы')
    gradient_direction: str | None = Field(None, max_length=20, description='Направление градиента')
    is_premium_profile: bool | None = Field(None, description='Премиум оформление профиля')


class UserProfileSettingsUpdate(UserProfileSettingsBase):
    """Схема для обновления настроек профиля (все поля опциональны)"""
    pass


class UserProfileSettingsResponse(UserProfileSettingsBase):
    """Схема для ответа с настройками профиля"""
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True