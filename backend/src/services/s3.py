from aiobotocore.session import get_session
from fastapi import UploadFile
from contextlib import asynccontextmanager

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

        object_name = f'photo/profile/user_{user_id}.jpg'
        file_context = await user_photo.read()

        async with self.get_client() as client:
            await client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_context,
            )
            return domen_url + f'photo/profile/user_{user_id}.jpg'
            

s3_client = S3Client(
    access_key='287f46f37d90482980a2e453b185163f',
    secret_key='a16f368a0146495dbc86c259d9ef0ebf',
    endpoint_url='https://s3.ru-7.storage.selcloud.ru',
    bucket_name='anigo'
)