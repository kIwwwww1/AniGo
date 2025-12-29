from pydantic import BaseModel, EmailStr, Field

class UserName(BaseModel):
    username: str = Field(min_length=3, max_length=15)

class UserEmail(UserName):
    email: EmailStr

class LoginUser(UserName):
    password: str

class CreateNewUser(LoginUser, UserEmail):
    pass

class CreateUserComment(BaseModel):
    text: str = Field(min_length=1, max_length=150)
    anime_id: int

class CreateUserRating(BaseModel):
    rating: int = Field(ge=1, le=10)
    anime_id: int