import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os import getenv
from dotenv import load_dotenv
from loguru import logger
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Загружаем .env файл из разных возможных мест
# В Docker контейнере .env будет в /app/.env (если смонтирован через docker-compose)
# При локальном запуске - в корне проекта или backend/
project_root = Path(__file__).resolve().parent.parent.parent.parent
backend_dir = Path(__file__).resolve().parent.parent.parent
current_dir = Path.cwd()
app_dir = Path('/app')  # Docker рабочая директория

# Список возможных путей к .env файлу
env_paths = [
    app_dir / '.env',        # Docker: /app/.env
    project_root / '.env',   # Локально: корень проекта
    backend_dir / '.env',    # backend/.env
    current_dir / '.env',    # Текущая рабочая директория
    Path('.env'),            # Относительный путь
]

# Пытаемся загрузить .env из разных мест
loaded = False
for env_path in env_paths:
    try:
        resolved_path = env_path.resolve()
        if resolved_path.exists() and resolved_path.is_file():
            logger.info(f"Loading .env from: {resolved_path}")
            load_dotenv(dotenv_path=resolved_path, override=True)
            loaded = True
            break
    except Exception as e:
        logger.debug(f"Failed to load .env from {env_path}: {e}")

# Также пробуем стандартный load_dotenv() (работает с env_file в docker-compose)
if not loaded:
    logger.info(f"Trying standard load_dotenv() from: {current_dir}")
    load_dotenv(override=True)

# SMTP настройки
SMTP_HOST = getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(getenv('SMTP_PORT', '587'))
SMTP_USER = getenv('SMTP_USER', '')
SMTP_PASSWORD = getenv('SMTP_PASSWORD', '')
SMTP_FROM_EMAIL = getenv('SMTP_FROM_EMAIL', SMTP_USER)
FRONTEND_URL = getenv('FRONTEND_URL', 'http://localhost:3000')

# Отладочная информация (не логируем пароль)
logger.debug(f"SMTP settings loaded: HOST={SMTP_HOST}, PORT={SMTP_PORT}, USER={'set' if SMTP_USER else 'not set'}, FROM={SMTP_FROM_EMAIL}")


def generate_verification_token() -> str:
    """Генерирует безопасный токен для подтверждения email"""
    return secrets.token_urlsafe(32)


def get_verification_token_expires() -> datetime:
    """Возвращает время истечения токена (2 минуты)"""
    return datetime.now(timezone.utc) + timedelta(minutes=2)


async def send_verification_email(email: str, username: str, token: str) -> bool:
    """Отправляет письмо с подтверждением email"""
    
    # Проверяем, что SMTP настройки заполнены (не пустые строки)
    if not SMTP_USER or not SMTP_PASSWORD or SMTP_USER.strip() == '' or SMTP_PASSWORD.strip() == '':
        logger.error(f"SMTP credentials not configured. SMTP_USER={'set' if SMTP_USER else 'not set'}, SMTP_PASSWORD={'set' if SMTP_PASSWORD else 'not set'}")
        logger.error("Please configure SMTP_USER and SMTP_PASSWORD in .env file")
        return False
    
    logger.info(f"Attempting to send email via {SMTP_HOST}:{SMTP_PORT} from {SMTP_FROM_EMAIL}")
    
    try:
        # Создаем сообщение
        message = MIMEMultipart("alternative")
        message["Subject"] = "Подтверждение email - Yumivo"
        message["From"] = SMTP_FROM_EMAIL
        message["To"] = email
        
        # Создаем ссылку для подтверждения
        verification_url = f"{FRONTEND_URL}/verify-email?token={token}"
        
        # Текст письма
        text = f"""
Здравствуйте, {username}!

Спасибо за регистрацию на Yumivo!

Для завершения регистрации и подтверждения вашего email адреса, пожалуйста, перейдите по следующей ссылке:

{verification_url}

Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.

Ссылка действительна в течение 2 минут.

С уважением,
Команда Yumivo
"""
        
        # HTML версия письма
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background-color: #f9f9f9;
            padding: 30px;
            border-radius: 10px;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .button:hover {{
            background-color: #45a049;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Здравствуйте, {username}!</h2>
        <p>Спасибо за регистрацию на Yumivo!</p>
        <p>Для завершения регистрации и подтверждения вашего email адреса, пожалуйста, нажмите на кнопку ниже:</p>
        <a href="{verification_url}" class="button">Подтвердить email</a>
        <p>Или скопируйте и вставьте следующую ссылку в браузер:</p>
        <p style="word-break: break-all; color: #666;">{verification_url}</p>
        <p style="color: #999; font-size: 12px;">Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.</p>
        <p style="color: #999; font-size: 12px;">Ссылка действительна в течение 2 минут.</p>
        <p>С уважением,<br>Команда Yumivo</p>
    </div>
</body>
</html>
"""
        
        # Добавляем части письма
        part1 = MIMEText(text, "plain", "utf-8")
        part2 = MIMEText(html, "html", "utf-8")
        
        message.attach(part1)
        message.attach(part2)
        
        # Отправляем письмо
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        
        logger.info(f"Verification email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {str(e)}", exc_info=True)
        logger.error(f"SMTP settings: HOST={SMTP_HOST}, PORT={SMTP_PORT}, USER={'set' if SMTP_USER else 'not set'}, FROM={SMTP_FROM_EMAIL}")
        return False



