from anicli_api.source.animevost import Extractor

ex = Extractor()

async def get_anime_by_title(title: str):
    animes = await ex.a_search(title)
    # Преобразуем объекты в словари для сериализации в JSON
    result = []
    for anime in animes:
        try:
            # Получаем все атрибуты объекта через vars()
            anime_dict = vars(anime).copy() if hasattr(anime, '__dict__') else {}
            
            # Убираем приватные атрибуты и методы, преобразуем несериализуемые типы
            serializable_dict = {}
            for k, v in anime_dict.items():
                if k.startswith('_') or callable(v):
                    continue
                # Преобразуем значения для JSON сериализации
                if isinstance(v, (str, int, float, bool, type(None))):
                    serializable_dict[k] = v
                elif isinstance(v, (list, dict)):
                    serializable_dict[k] = v
                else:
                    # Преобразуем сложные объекты в строки
                    serializable_dict[k] = str(v)
            
            # Если словарь пустой, пытаемся получить основные атрибуты
            if not serializable_dict:
                for attr in ['title', 'url', 'poster', 'name', 'id']:
                    if hasattr(anime, attr):
                        value = getattr(anime, attr)
                        if not callable(value):
                            serializable_dict[attr] = str(value) if not isinstance(value, (str, int, float, bool, type(None))) else value
            
            # Если все еще пустой, используем repr
            if not serializable_dict:
                serializable_dict = {'repr': repr(anime)}
                
        except Exception as e:
            # Если произошла ошибка, возвращаем минимальную информацию
            serializable_dict = {'error': f'Failed to serialize: {str(e)}', 'repr': repr(anime)}
        
        result.append(serializable_dict)
    
    return result
