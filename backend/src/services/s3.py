from aiobotocore.session import get_session
from fastapi import UploadFile
from contextlib import asynccontextmanager
from loguru import logger
import os
from dotenv import load_dotenv

load_dotenv()

domen_url = os.getenv('S3_DOMEN_URL', 'https://40ae02b4-dcfc-4ffc-a604-1112971df1d8.selstorage.ru')

class S3Client:
    def __init__(
            self, access_key: str,
            secret_key: str, 
            endpoint_url: str,
            bucket_name: str):
        
        self.config = {
            'aws_access_key_id': access_key,
            'aws_secret_access_key': secret_key,
            'endpoint_url': endpoint_url,
        }
        self.bucket_name = bucket_name
        self.session = get_session()


    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client
            
    async def upload_user_photo(self, user_photo: UploadFile, user_id: int):
        """Загружает фото пользователя в S3 хранилище"""
        import time
        # Добавляем timestamp к имени файла для обхода кеша браузера
        timestamp = int(time.time() * 1000)  # миллисекунды для уникальности
        object_name = f'photo/profile/user_{user_id}_{timestamp}.jpg'
        logger.info(f"Начало загрузки фото для пользователя {user_id}, объект: {object_name}")
        
        # Читаем содержимое файла
        # Если это уже bytes, используем как есть, иначе читаем из UploadFile
        if hasattr(user_photo, '_file_content'):
            # Если передан FileWrapper с уже прочитанным содержимым
            file_context = user_photo._file_content
            logger.info(f"Используется FileWrapper, размер файла: {len(file_context)} байт")
        else:
            # Читаем из UploadFile
            file_context = await user_photo.read()
            logger.info(f"Прочитано из UploadFile, размер файла: {len(file_context)} байт")
            # Сбрасываем указатель файла на начало для возможного повторного чтения
            if hasattr(user_photo, 'seek'):
                await user_photo.seek(0)

        if not file_context or len(file_context) == 0:
            logger.error(f"Ошибка: файл пустой для пользователя {user_id}")
            raise ValueError(f"Файл пустой, невозможно загрузить в S3")

        async with self.get_client() as client:
            # Удаляем старые аватары пользователя (опционально, можно закомментировать если не нужно)
            try:
                # Ищем все файлы аватаров для этого пользователя
                prefix = f'photo/profile/user_{user_id}_'
                list_response = await client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
                # Удаляем все найденные старые аватары
                if 'Contents' in list_response:
                    for obj in list_response['Contents']:
                        if obj['Key'] != object_name:  # Не удаляем новый файл
                            await client.delete_object(
                                Bucket=self.bucket_name,
                                Key=obj['Key']
                            )
                            logger.info(f"Удален старый аватар: {obj['Key']}")
            except Exception as e:
                logger.warning(f"Не удалось удалить старые аватары: {e}")
            
            logger.info(f"Загрузка файла в S3 bucket: {self.bucket_name}, key: {object_name}")
            await client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_context,
                ContentType='image/jpeg'  # Указываем тип контента
            )
            photo_url = domen_url + f'/photo/profile/user_{user_id}_{timestamp}.jpg'
            logger.info(f"Фото успешно загружено в S3, URL: {photo_url}")
            return photo_url
    
    async def upload_background_image(self, background_image: UploadFile, user_id: int):
        """Загружает фоновое изображение под аватаркой в S3 хранилище"""
        import time
        # Добавляем timestamp к имени файла для обхода кеша браузера
        timestamp = int(time.time() * 1000)  # миллисекунды для уникальности
        object_name = f'photo/background/user_{user_id}_{timestamp}.jpg'
        logger.info(f"Начало загрузки фонового изображения для пользователя {user_id}, объект: {object_name}")
        
        # Читаем содержимое файла
        if hasattr(background_image, '_file_content'):
            file_context = background_image._file_content
            logger.info(f"Используется FileWrapper, размер файла: {len(file_context)} байт")
        else:
            file_context = await background_image.read()
            logger.info(f"Прочитано из UploadFile, размер файла: {len(file_context)} байт")
            if hasattr(background_image, 'seek'):
                await background_image.seek(0)

        if not file_context or len(file_context) == 0:
            logger.error(f"Ошибка: файл пустой для пользователя {user_id}")
            raise ValueError(f"Файл пустой, невозможно загрузить в S3")

        async with self.get_client() as client:
            # Удаляем старые фоновые изображения пользователя
            try:
                prefix = f'photo/background/user_{user_id}_'
                list_response = await client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
                if 'Contents' in list_response:
                    for obj in list_response['Contents']:
                        if obj['Key'] != object_name:
                            await client.delete_object(
                                Bucket=self.bucket_name,
                                Key=obj['Key']
                            )
                            logger.info(f"Удалено старое фоновое изображение: {obj['Key']}")
            except Exception as e:
                logger.warning(f"Не удалось удалить старые фоновые изображения: {e}")
            
            logger.info(f"Загрузка файла в S3 bucket: {self.bucket_name}, key: {object_name}")
            await client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_context,
                ContentType='image/jpeg'
            )
            
            # Проверяем, что файл действительно загружен
            try:
                head_response = await client.head_object(
                    Bucket=self.bucket_name,
                    Key=object_name
                )
                logger.info(f"✅ Файл подтвержден в S3, размер: {head_response.get('ContentLength', 0)} байт")
            except Exception as e:
                logger.error(f"❌ Ошибка проверки файла в S3: {e}")
                raise ValueError(f"Файл не был загружен в S3: {e}")
            
            background_url = domen_url + f'/photo/background/user_{user_id}_{timestamp}.jpg'
            logger.info(f"Фоновое изображение успешно загружено в S3, URL: {background_url}")
            return background_url
    
    async def delete_background_image(self, user_id: int):
        """Удаляет все фоновые изображения пользователя из S3 хранилища"""
        async with self.get_client() as client:
            try:
                prefix = f'photo/background/user_{user_id}_'
                list_response = await client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
                if 'Contents' in list_response:
                    for obj in list_response['Contents']:
                        await client.delete_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        logger.info(f"Удалено фоновое изображение из S3: {obj['Key']}")
                logger.info(f"Все фоновые изображения удалены для пользователя {user_id}")
            except Exception as e:
                logger.warning(f"Не удалось удалить фоновые изображения из S3: {e}")
                raise ValueError(f"Ошибка при удалении фонового изображения из S3: {e}")
            

s3_client = S3Client(
    access_key=os.getenv('S3_ACCESS_KEY', ''),
    secret_key=os.getenv('S3_SECRET_KEY', ''),
    endpoint_url=os.getenv('S3_ENDPOINT_URL', 'https://s3.ru-7.storage.selcloud.ru'),
    bucket_name=os.getenv('S3_BUCKET_NAME', 'anigo')
)