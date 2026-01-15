"""
Утилиты для валидации изображений
"""
from PIL import Image
import io
from fastapi import HTTPException, UploadFile
from typing import Tuple


class ImageValidator:
    """
    Валидатор изображений для проверки размера файла и разрешения
    
    Attributes:
        max_file_size (int): Максимальный размер файла в байтах
        max_width (int): Максимальная ширина изображения
        max_height (int): Максимальная высота изображения
        min_width (int): Минимальная ширина изображения
        min_height (int): Минимальная высота изображения
        exact_width (int): Точная ширина изображения (если указана, проверяется точное совпадение)
        exact_height (int): Точная высота изображения (если указана, проверяется точное совпадение)
    """
    
    def __init__(
        self,
        max_file_size: int,
        max_width: int = None,
        max_height: int = None,
        min_width: int = None,
        min_height: int = None,
        exact_width: int = None,
        exact_height: int = None
    ):
        self.max_file_size = max_file_size
        self.max_width = max_width
        self.max_height = max_height
        self.min_width = min_width
        self.min_height = min_height
        self.exact_width = exact_width
        self.exact_height = exact_height
    
    async def validate(self, photo: UploadFile) -> bytes:
        """
        Валидирует изображение и возвращает его содержимое
        
        Args:
            photo: Загруженный файл
            
        Returns:
            bytes: Содержимое файла
            
        Raises:
            HTTPException: При ошибках валидации
        """
        # Проверяем тип файла
        if not photo.content_type or not photo.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail='Файл должен быть изображением'
            )
        
        # Читаем файл
        file_content = await photo.read()
        file_size = len(file_content)
        
        # Проверяем размер файла
        if file_size > self.max_file_size:
            max_mb = self.max_file_size / 1024 / 1024
            current_mb = file_size / 1024 / 1024
            raise HTTPException(
                status_code=400,
                detail=f'Размер файла не должен превышать {max_mb:.0f} МБ. Текущий размер: {current_mb:.2f} МБ'
            )
        
        # Проверяем размеры изображения
        try:
            image = Image.open(io.BytesIO(file_content))
            width, height = image.size
            
            # Если указаны точные размеры, проверяем точное совпадение
            if self.exact_width is not None and width != self.exact_width:
                raise HTTPException(
                    status_code=400,
                    detail=f'Ширина изображения должна быть точно {self.exact_width} пикселей. Текущая ширина: {width}'
                )
            
            if self.exact_height is not None and height != self.exact_height:
                raise HTTPException(
                    status_code=400,
                    detail=f'Высота изображения должна быть точно {self.exact_height} пикселей. Текущая высота: {height}'
                )
            
            # Если точные размеры не указаны, проверяем min/max
            if self.exact_width is None and self.exact_height is None:
                if self.max_width and width > self.max_width:
                    raise HTTPException(
                        status_code=400,
                        detail=f'Ширина изображения не должна превышать {self.max_width} пикселей. Текущая ширина: {width}'
                    )
                
                if self.max_height and height > self.max_height:
                    raise HTTPException(
                        status_code=400,
                        detail=f'Высота изображения не должна превышать {self.max_height} пикселей. Текущая высота: {height}'
                    )
                
                if self.min_width and width < self.min_width:
                    raise HTTPException(
                        status_code=400,
                        detail=f'Ширина изображения должна быть не менее {self.min_width} пикселей. Текущая ширина: {width}'
                    )
                
                if self.min_height and height < self.min_height:
                    raise HTTPException(
                        status_code=400,
                        detail=f'Высота изображения должна быть не менее {self.min_height} пикселей. Текущая высота: {height}'
                    )
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f'Ошибка при обработке изображения: {str(e)}'
            )
        
        return file_content


# Готовые валидаторы для разных типов изображений
AVATAR_VALIDATOR = ImageValidator(
    max_file_size=2 * 1024 * 1024,  # 2 МБ
    max_width=2000,
    max_height=2000
)

BACKGROUND_IMAGE_VALIDATOR = ImageValidator(
    max_file_size=5 * 1024 * 1024,  # 5 МБ
    exact_width=1200,
    exact_height=350
)
