# Руководство по настройке VPS сервера для AniGo

## Рекомендация по выбору дистрибутива

### ✅ Рекомендуемые дистрибутивы (в порядке приоритета):

#### 1. **Ubuntu 22.04 LTS** (РЕКОМЕНДУЕТСЯ)
- ✅ Стабильная и хорошо документированная
- ✅ Отличная поддержка Docker
- ✅ Большое сообщество и множество руководств
- ✅ Долгосрочная поддержка до 2027 года
- ✅ Простая установка и настройка

#### 2. **Ubuntu 20.04 LTS**
- ✅ Стабильная версия
- ✅ Поддержка до 2025 года
- ✅ Проверенная временем

#### 3. **Debian 12 (Bookworm)**
- ✅ Очень стабильная
- ✅ Минимальное потребление ресурсов
- ✅ Отличная безопасность
- ⚠️ Может потребоваться больше ручной настройки

#### 4. **Debian 11 (Bullseye)**
- ✅ Стабильная версия
- ✅ Хорошая поддержка Docker

### ❌ НЕ рекомендуется:
- CentOS/Rocky Linux (сложнее с Docker)
- Arch Linux (слишком нестабильная для продакшена)
- Fedora (слишком часто обновляется)

## Минимальные требования к серверу

### Для 50 пользователей:
- **CPU**: 3-4 ядра
- **RAM**: 5-8 GB (рекомендуется 8 GB)
- **Диск**: 40-60 GB SSD (рекомендуется 60 GB)
- **Пропускная способность**: 100 Мбит/с

## Пошаговая установка ПО

### Шаг 1: Подключение к серверу

```bash
# Подключитесь к серверу по SSH
ssh root@your_server_ip
# или
ssh your_username@your_server_ip
```

### Шаг 2: Обновление системы

```bash
# Для Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# Перезагрузка (если требуется)
sudo reboot
```

### Шаг 3: Установка базовых утилит

```bash
# Установка необходимых утилит
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    net-tools \
    ufw \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common \
    apt-transport-https
```

### Шаг 4: Установка Docker

```bash
# Удаление старых версий (если есть)
sudo apt remove -y docker docker-engine docker.io containerd runc

# Установка зависимостей
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Добавление официального GPG ключа Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Для Ubuntu
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Для Debian (если используете Debian)
# echo \
#   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
#   $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Обновление списка пакетов
sudo apt update

# Установка Docker Engine, Docker CLI и Containerd
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Проверка установки
sudo docker --version
sudo docker compose version

# Добавление текущего пользователя в группу docker (чтобы не использовать sudo)
sudo usermod -aG docker $USER

# Применение изменений группы (или переподключитесь)
newgrp docker

# Проверка работы Docker без sudo
docker run hello-world
```

### Шаг 5: Настройка Firewall (UFW)

```bash
# Разрешение SSH (ВАЖНО! Сделайте это первым)
sudo ufw allow 22/tcp

# Разрешение HTTP и HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включение firewall
sudo ufw enable

# Проверка статуса
sudo ufw status
```

### Шаг 6: Установка Git (если не установлен)

```bash
sudo apt install -y git

# Настройка Git (замените на свои данные)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Шаг 7: Установка дополнительных инструментов (опционально)

```bash
# Мониторинг ресурсов
sudo apt install -y htop iotop

# Просмотр логов
sudo apt install -y logrotate

# Автоматические обновления безопасности (рекомендуется)
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Шаг 8: Настройка автоматических обновлений безопасности

```bash
# Редактирование конфигурации
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades

# Убедитесь, что включены обновления безопасности:
# Unattended-Upgrade::Allowed-Origins {
#     "${distro_id}:${distro_codename}-security";
# };

# Включение автоматических обновлений
sudo nano /etc/apt/apt.conf.d/20auto-upgrades

# Добавьте или убедитесь, что есть:
# APT::Periodic::Update-Package-Lists "1";
# APT::Periodic::Unattended-Upgrade "1";
```

### Шаг 9: Настройка часового пояса

```bash
# Установка часового пояса (например, для Москвы)
sudo timedatectl set-timezone Europe/Moscow

# Проверка
timedatectl
```

### Шаг 10: Оптимизация системы (для продакшена)

```bash
# Увеличение лимитов файловых дескрипторов
sudo nano /etc/security/limits.conf

# Добавьте в конец файла:
# * soft nofile 65535
# * hard nofile 65535

# Применение изменений (требует переподключения)
```

## Проверка установки

Выполните следующие команды для проверки:

```bash
# Проверка версии ОС
lsb_release -a

# Проверка Docker
docker --version
docker compose version
docker ps

# Проверка доступного места на диске
df -h

# Проверка памяти
free -h

# Проверка CPU
lscpu

# Проверка открытых портов
sudo netstat -tulpn | grep -E ':(80|443|22)'
```

## Следующие шаги

После установки всего необходимого ПО:

1. **Клонируйте ваш проект**:
   ```bash
   git clone <your-repo-url> AniGo
   cd AniGo
   ```

2. **Настройте переменные окружения** (создайте файл `.env`)

3. **Запустите приложение через Docker Compose**:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

4. **Настройте SSL сертификаты** (см. `DEPLOY.md`)

5. **Настройте бэкапы базы данных**

## Список установленного ПО

### Обязательное ПО:
- ✅ **Docker** (контейнеризация приложения)
- ✅ **Docker Compose** (оркестрация контейнеров)
- ✅ **Git** (управление версиями)
- ✅ **UFW** (файрвол)
- ✅ **Curl/Wget** (загрузка файлов)

### Опциональное ПО:
- ✅ **htop** (мониторинг ресурсов)
- ✅ **vim/nano** (редакторы текста)
- ✅ **unattended-upgrades** (автоматические обновления безопасности)

### ПО, которое будет запущено в Docker:
- ✅ **PostgreSQL 15** (база данных)
- ✅ **Redis** (кэширование, опционально)
- ✅ **Nginx** (reverse proxy и статические файлы)
- ✅ **Certbot** (SSL сертификаты)
- ✅ **Python 3.11** (backend в контейнере)
- ✅ **Node.js** (только для сборки frontend, не нужен на сервере)

## Рекомендации по безопасности

1. **Отключите вход по паролю для SSH** (используйте только ключи):
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Установите: PasswordAuthentication no
   sudo systemctl restart sshd
   ```

2. **Измените стандартный SSH порт** (опционально):
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Измените: Port 2222 (или другой)
   sudo systemctl restart sshd
   # Не забудьте обновить firewall: sudo ufw allow 2222/tcp
   ```

3. **Настройте fail2ban** (защита от брутфорса):
   ```bash
   sudo apt install -y fail2ban
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

4. **Регулярно обновляйте систему**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

## Полезные команды для управления

```bash
# Просмотр использования ресурсов Docker контейнерами
docker stats

# Просмотр логов
docker compose -f docker-compose.prod.yml logs -f

# Перезапуск сервиса
docker compose -f docker-compose.prod.yml restart backend

# Остановка всех контейнеров
docker compose -f docker-compose.prod.yml down

# Очистка неиспользуемых Docker ресурсов
docker system prune -a

# Просмотр использования диска
du -sh /var/lib/docker/*
```

## Поддержка

Если возникли проблемы:
1. Проверьте логи: `docker compose -f docker-compose.prod.yml logs`
2. Проверьте статус контейнеров: `docker compose -f docker-compose.prod.yml ps`
3. Проверьте документацию в `DEPLOY.md` и `VPS_CONFIGURATION_50_USERS.md`
