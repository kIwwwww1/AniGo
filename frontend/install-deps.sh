#!/bin/sh
# Скрипт для установки зависимостей в Docker контейнере

echo "Установка зависимостей npm с увеличенными таймаутами..."
npm install --fetch-timeout=300000 --fetch-retries=5 --prefer-offline=false

if [ $? -eq 0 ]; then
    echo "✅ Зависимости успешно установлены!"
    exit 0
else
    echo "❌ Ошибка при установке зависимостей"
    echo "Попытка использовать альтернативный registry..."
    
    # Попробовать использовать альтернативный registry
    npm config set registry https://registry.npmmirror.com
    npm install --fetch-timeout=300000 --fetch-retries=5
    
    if [ $? -eq 0 ]; then
        echo "✅ Зависимости установлены через альтернативный registry!"
        # Вернуть оригинальный registry
        npm config set registry https://registry.npmjs.org
        exit 0
    else
        echo "❌ Не удалось установить зависимости"
        exit 1
    fi
fi
