#!/bin/bash
# Скрипт для принудительной установки hls.js в Docker контейнере

echo "🔧 Исправление проблемы с hls.js в Docker контейнере..."

# Проверяем, запущен ли контейнер
if ! docker-compose ps frontend | grep -q "Up"; then
    echo "❌ Контейнер frontend не запущен. Запустите его сначала:"
    echo "   docker-compose up -d frontend"
    exit 1
fi

echo "📦 Удаление маркера установки для принудительной переустановки..."
docker-compose exec frontend rm -f node_modules/.package-hash 2>/dev/null || true

echo "📥 Установка hls.js..."
docker-compose exec frontend npm install hls.js --fetch-timeout=300000 --fetch-retries=5

if [ $? -eq 0 ]; then
    echo "✅ hls.js успешно установлен!"
    
    echo "🔍 Проверка установки..."
    docker-compose exec frontend ls -la node_modules/hls.js/package.json
    
    if [ $? -eq 0 ]; then
        echo "✅ hls.js найден в node_modules!"
        echo ""
        echo "🔄 Перезапуск контейнера для применения изменений..."
        docker-compose restart frontend
        echo ""
        echo "✅ Готово! Проверьте логи:"
        echo "   docker-compose logs -f frontend"
    else
        echo "❌ hls.js всё ещё не найден. Попробуйте полную переустановку:"
        echo "   docker-compose exec frontend npm install --fetch-timeout=300000 --fetch-retries=5"
    fi
else
    echo "❌ Ошибка при установке hls.js"
    echo "Попробуйте использовать альтернативный registry:"
    echo "   docker-compose exec frontend sh -c 'npm config set registry https://registry.npmmirror.com && npm install hls.js && npm config set registry https://registry.npmjs.org'"
    exit 1
fi
