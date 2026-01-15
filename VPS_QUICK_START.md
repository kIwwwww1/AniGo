# Быстрый старт: Установка ПО на VPS

## Рекомендуемый дистрибутив

**Ubuntu 22.04 LTS** - лучший выбор для вашего проекта.

Альтернативы:
- Ubuntu 20.04 LTS
- Debian 12 (Bookworm)
- Debian 11 (Bullseye)

## Быстрая установка (автоматическая)

### Вариант 1: Автоматический скрипт (РЕКОМЕНДУЕТСЯ)

```bash
# Скачайте скрипт на сервер
wget https://raw.githubusercontent.com/your-repo/AniGo/main/install-vps-software.sh
# или скопируйте файл install-vps-software.sh на сервер

# Сделайте исполняемым и запустите
chmod +x install-vps-software.sh
sudo bash install-vps-software.sh
```

### Вариант 2: Ручная установка

#### 1. Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. Установка базовых утилит
```bash
sudo apt install -y curl wget git vim nano htop ufw
```

#### 3. Установка Docker
```bash
# Удаление старых версий
sudo apt remove -y docker docker-engine docker.io containerd runc

# Установка зависимостей
sudo apt install -y ca-certificates curl gnupg lsb-release

# Добавление GPG ключа
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Добавление репозитория (для Ubuntu)
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Проверка
docker --version
docker compose version
```

#### 4. Настройка Firewall
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Что будет установлено

### Обязательное ПО:
- ✅ **Docker** + **Docker Compose** - для запуска приложения
- ✅ **Git** - для клонирования проекта
- ✅ **UFW** - файрвол для безопасности
- ✅ **Базовые утилиты** - curl, wget, vim, nano, htop

### Опциональное ПО (включено в скрипт):
- ✅ **fail2ban** - защита от брутфорса SSH
- ✅ **unattended-upgrades** - автоматические обновления безопасности

### ПО в Docker контейнерах (устанавливается автоматически):
- ✅ **PostgreSQL 15** - база данных
- ✅ **Redis** - кэширование (опционально)
- ✅ **Nginx** - reverse proxy
- ✅ **Certbot** - SSL сертификаты
- ✅ **Python 3.11** - backend
- ✅ **Node.js** - только для сборки frontend

## Минимальные требования сервера

Для 50 пользователей:
- **CPU**: 3-4 ядра
- **RAM**: 5-8 GB (рекомендуется 8 GB)
- **Диск**: 40-60 GB SSD (рекомендуется 60 GB)
- **Пропускная способность**: 100 Мбит/с

## После установки ПО

1. **Клонируйте проект**:
   ```bash
   git clone <your-repo-url> AniGo
   cd AniGo
   ```

2. **Создайте файл `.env`** с переменными окружения

3. **Запустите приложение**:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

4. **Настройте SSL** (см. `DEPLOY.md`)

## Проверка установки

```bash
# Проверка Docker
docker --version
docker compose version
docker ps

# Проверка ресурсов
free -h
df -h
htop

# Проверка firewall
sudo ufw status
```

## Полезные команды

```bash
# Просмотр логов
docker compose -f docker-compose.prod.yml logs -f

# Перезапуск сервиса
docker compose -f docker-compose.prod.yml restart backend

# Остановка всех контейнеров
docker compose -f docker-compose.prod.yml down

# Очистка неиспользуемых Docker ресурсов
docker system prune -a
```

## Документация

- **Подробная инструкция**: `VPS_SETUP_GUIDE.md`
- **Развертывание**: `DEPLOY.md`
- **Конфигурация для 50 пользователей**: `VPS_CONFIGURATION_50_USERS.md`

## Поддержка

При возникновении проблем проверьте:
1. Логи: `docker compose -f docker-compose.prod.yml logs`
2. Статус контейнеров: `docker compose -f docker-compose.prod.yml ps`
3. Документацию в проекте
