# Как получить ID аниме на странице и создать комментарий

## На фронтенде (React)

### 1. Получение ID аниме из URL

На странице просмотра (`WatchPage.jsx`) ID аниме уже получается из URL через `useParams()`:

```jsx
import { useParams } from 'react-router-dom'

function WatchPage() {
  const { animeId } = useParams()  // ← ID аниме из URL /watch/:animeId
  
  // animeId - это строка, если нужно число:
  const animeIdNumber = parseInt(animeId, 10)
  
  // Теперь можно использовать animeId для создания комментария
}
```

### 2. Пример создания комментария

```jsx
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { userAPI } from '../services/api'

function WatchPage() {
  const { animeId } = useParams()  // Получаем ID из URL
  const [commentText, setCommentText] = useState('')
  
  const handleCreateComment = async () => {
    try {
      // animeId уже есть из URL, просто передаем его в API
      const response = await userAPI.createComment(
        parseInt(animeId, 10),  // Преобразуем в число
        commentText
      )
      console.log('Комментарий создан:', response)
      setCommentText('')  // Очищаем поле
    } catch (error) {
      console.error('Ошибка создания комментария:', error)
    }
  }
  
  return (
    <div>
      <textarea
        value={commentText}
        onChange={(e) => setCommentText(e.target.value)}
        placeholder="Напишите комментарий..."
      />
      <button onClick={handleCreateComment}>
        Отправить комментарий
      </button>
    </div>
  )
}
```

## На бэкенде (FastAPI)

### 1. Структура функции `create_comment`

```python
async def create_comment(comment_data: CreateUserComment, user_id: int, session: AsyncSession):
    '''Создать комментарий к аниме
    
    Args:
        comment_data: Данные комментария (text и anime_id)
        user_id: ID пользователя из токена (получается автоматически)
        session: Сессия базы данных
    '''
    new_comment = CommentModel(
        user_id=user_id,              # Из токена
        anime_id=comment_data.anime_id,  # Из запроса фронтенда
        text=comment_data.text        # Из запроса фронтенда
    )
    
    session.add(new_comment)
    await session.commit()
    return new_comment
```

### 2. API Endpoint

```python
@user_router.post('/create/comment')
async def create_user_comment(
    comment_data: CreateUserComment,  # Содержит text и anime_id
    request: Request,                 # Для получения токена
    session: SessionDep
):
    # Получаем user_id из токена
    token_data = await get_token(request)
    user_id = int(token_data.get('sub'))
    
    # Создаем комментарий
    comment = await create_comment(comment_data, user_id, session)
    return {'message': 'Комментарий создан', 'comment_id': comment.id}
```

## Схема данных

### CreateUserComment (Pydantic)
```python
class CreateUserComment(BaseModel):
    text: str = Field(min_length=1, max_length=150)
    anime_id: int  # ← ID аниме передается с фронтенда
```

## Поток данных

1. **Фронтенд**: Пользователь на странице `/watch/123` (где 123 - ID аниме)
2. **Фронтенд**: `useParams()` получает `animeId = "123"`
3. **Фронтенд**: При отправке комментария вызывается:
   ```js
   userAPI.createComment(123, "Текст комментария")
   ```
4. **Бэкенд**: Endpoint получает `{anime_id: 123, text: "Текст комментария"}`
5. **Бэкенд**: `get_token(request)` получает `user_id` из токена
6. **Бэкенд**: Создается комментарий с `user_id`, `anime_id` и `text`

## Важно

- **anime_id** передается с фронтенда в теле запроса
- **user_id** получается автоматически из токена аутентификации
- ID аниме всегда доступен на странице через `useParams()` из URL

