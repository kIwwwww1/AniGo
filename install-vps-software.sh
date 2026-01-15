#!/bin/bash

# Скрипт автоматической установки ПО для VPS сервера AniGo
# Использование: sudo bash install-vps-software.sh

set -e  # Остановка при ошибке

echo "=========================================="
echo "Установка ПО для VPS сервера AniGo"
echo "=========================================="

# Проверка, что скрипт запущен от root или с sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Пожалуйста, запустите скрипт с sudo: sudo bash install-vps-software.sh"
    exit 1
fi

# Определение дистрибутива
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    echo "Не удалось определить дистрибутив"
    exit 1
fi

echo "Обнаружен дистрибутив: $OS $VER"
echo ""

# Шаг 1: Обновление системы
echo "Шаг 1: Обновление системы..."
apt update && apt upgrade -y
echo "✓ Система обновлена"
echo ""

# Шаг 2: Установка базовых утилит
echo "Шаг 2: Установка базовых утилит..."
apt install -y \
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
    apt-transport-https \
    unattended-upgrades
echo "✓ Базовые утилиты установлены"
echo ""

# Шаг 3: Установка Docker
echo "Шаг 3: Установка Docker..."
# Удаление старых версий
apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Установка зависимостей
apt install -y ca-certificates curl gnupg lsb-release

# Добавление GPG ключа Docker
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Добавление репозитория Docker
if [ "$OS" = "ubuntu" ]; then
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
elif [ "$OS" = "debian" ]; then
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
else
    echo "Дистрибутив $OS не поддерживается автоматически. Установите Docker вручную."
    exit 1
fi

# Обновление списка пакетов
apt update

# Установка Docker
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Проверка установки
docker --version
docker compose version
echo "✓ Docker установлен"
echo ""

# Шаг 4: Настройка пользователя для Docker
echo "Шаг 4: Настройка пользователя для Docker..."
if [ -n "$SUDO_USER" ]; then
    usermod -aG docker $SUDO_USER
    echo "✓ Пользователь $SUDO_USER добавлен в группу docker"
    echo "  ВНИМАНИЕ: Переподключитесь к серверу, чтобы изменения вступили в силу"
else
    echo "⚠ Не удалось определить пользователя. Добавьте его в группу docker вручную:"
    echo "  sudo usermod -aG docker YOUR_USERNAME"
fi
echo ""

# Шаг 5: Настройка Firewall
echo "Шаг 5: Настройка Firewall..."
# Разрешение SSH (ВАЖНО!)
ufw allow 22/tcp
# Разрешение HTTP и HTTPS
ufw allow 80/tcp
ufw allow 443/tcp
# Включение firewall (с подтверждением)
echo "y" | ufw enable
echo "✓ Firewall настроен"
echo ""

# Шаг 6: Настройка часового пояса (Москва)
echo "Шаг 6: Настройка часового пояса..."
timedatectl set-timezone Europe/Moscow
echo "✓ Часовой пояс установлен: $(timedatectl | grep 'Time zone')"
echo ""

# Шаг 7: Настройка автоматических обновлений безопасности
echo "Шаг 7: Настройка автоматических обновлений безопасности..."
# Включение автоматических обновлений
cat > /etc/apt/apt.conf.d/20auto-upgrades << EOF
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
EOF
echo "✓ Автоматические обновления безопасности включены"
echo ""

# Шаг 8: Установка fail2ban (защита от брутфорса)
echo "Шаг 8: Установка fail2ban..."
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban
echo "✓ fail2ban установлен и запущен"
echo ""

# Шаг 9: Оптимизация лимитов файловых дескрипторов
echo "Шаг 9: Оптимизация системных лимитов..."
cat >> /etc/security/limits.conf << EOF

# Увеличение лимитов для Docker и приложений
* soft nofile 65535
* hard nofile 65535
EOF
echo "✓ Лимиты файловых дескрипторов увеличены"
echo "  ВНИМАНИЕ: Переподключитесь к серверу, чтобы изменения вступили в силу"
echo ""

# Финальная проверка
echo "=========================================="
echo "Проверка установки:"
echo "=========================================="
echo "Docker версия:"
docker --version
echo ""
echo "Docker Compose версия:"
docker compose version
echo ""
echo "Статус Firewall:"
ufw status
echo ""
echo "Статус fail2ban:"
systemctl status fail2ban --no-pager | head -3
echo ""
echo "Использование диска:"
df -h / | tail -1
echo ""
echo "Доступная память:"
free -h
echo ""

echo "=========================================="
echo "✓ Установка завершена успешно!"
echo "=========================================="
echo ""
echo "Следующие шаги:"
echo "1. Переподключитесь к серверу (чтобы применить изменения группы docker)"
echo "2. Клонируйте ваш проект: git clone <your-repo-url> AniGo"
echo "3. Перейдите в директорию: cd AniGo"
echo "4. Создайте файл .env с переменными окружения"
echo "5. Запустите приложение: docker compose -f docker-compose.prod.yml up -d --build"
echo ""
echo "Подробная инструкция: см. VPS_SETUP_GUIDE.md"
