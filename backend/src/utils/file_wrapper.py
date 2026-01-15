"""
Утилита для работы с файлами
Используется для совместимости с S3 клиентом
"""


class FileWrapper:
    """
    Обертка для содержимого файла, используемая для загрузки в S3
    
    Attributes:
        _file_content (bytes): Содержимое файла
        filename (str): Имя файла
        content_type (str): MIME тип файла
    """
    
    def __init__(self, file_content: bytes, filename: str, content_type: str):
        self._file_content = file_content
        self.filename = filename
        self.content_type = content_type
    
    async def read(self) -> bytes:
        """Асинхронное чтение содержимого файла"""
        return self._file_content
