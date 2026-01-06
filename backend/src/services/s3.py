from aiobotocore.session import get_session
from fastapi import UploadFile
from contextlib import asynccontextmanager
from loguru import logger

domen_url = 'https://40ae02b4-dcfc-4ffc-a604-1112971df1d8.selstorage.ru'

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
            

s3_client = S3Client(
    access_key='287f46f37d90482980a2e453b185163f',
    secret_key='a16f368a0146495dbc86c259d9ef0ebf',
    endpoint_url='https://s3.ru-7.storage.selcloud.ru',
    bucket_name='anigo'
)