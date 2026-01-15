#!/bin/sh
# ВАЖНО: убираем set -e в начале, чтобы скрипт не падал при проверках
# set -e будет включен только перед запуском Vite

echo "🚀 Запуск frontend контейнера..."

# КРИТИЧЕСКИ ВАЖНО: Проверяем и устанавливаем зависимости ПЕРЕД запуском Vite
# Volume /app/node_modules изолирует node_modules, поэтому зависимости из образа не видны
echo "🔍 Проверка наличия зависимостей в volume..."

# Функция для вычисления хеша файла
get_file_hash() {
    if [ -f "$1" ]; then
        md5sum "$1" 2>/dev/null | cut -d' ' -f1 || md5 -q "$1" 2>/dev/null || echo "unknown"
    else
        echo "missing"
    fi
}

# Получаем хеш текущего package.json
CURRENT_HASH=$(get_file_hash "package.json")
INSTALLED_HASH=""

# Проверяем, есть ли сохранённый хеш
if [ -f "node_modules/.package-hash" ]; then
    INSTALLED_HASH=$(cat node_modules/.package-hash)
fi

# Проверяем, нужно ли установить/обновить зависимости
NEED_INSTALL=false

# КРИТИЧЕСКАЯ ПРОВЕРКА: Проверяем наличие hls.js (даже если node_modules существует)
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-hash" ]; then
    echo "📦 Отсутствуют зависимости или маркер установки"
    NEED_INSTALL=true
elif [ "$CURRENT_HASH" != "$INSTALLED_HASH" ]; then
    echo "📦 Обнаружены изменения в package.json (старый хеш: $INSTALLED_HASH, новый: $CURRENT_HASH)"
    NEED_INSTALL=true
elif [ ! -f "node_modules/hls.js/package.json" ]; then
    echo "📦 hls.js отсутствует в node_modules, требуется установка"
    NEED_INSTALL=true
fi

if [ "$NEED_INSTALL" = "true" ]; then
    echo "📥 Установка/обновление зависимостей..."
    
    # Пытаемся установить с основного registry
    if npm install --fetch-timeout=300000 --fetch-retries=5; then
        echo "✅ Зависимости успешно установлены!"
        # Сохраняем хеш package.json для следующей проверки
        echo "$CURRENT_HASH" > node_modules/.package-hash
        
        # Проверяем, что hls.js установлен
        if [ ! -f "node_modules/hls.js/package.json" ]; then
            echo "⚠️  hls.js не найден, устанавливаем отдельно..."
            npm install hls.js --fetch-timeout=300000 --fetch-retries=5
        fi
    else
        echo "⚠️  Ошибка при установке с основного registry, пробуем альтернативный..."
        npm config set registry https://registry.npmmirror.com
        if npm install --fetch-timeout=300000 --fetch-retries=5; then
            echo "✅ Зависимости установлены через альтернативный registry!"
            npm config set registry https://registry.npmjs.org
            echo "$CURRENT_HASH" > node_modules/.package-hash
            
            # Проверяем, что hls.js установлен
            if [ ! -f "node_modules/hls.js/package.json" ]; then
                echo "⚠️  hls.js не найден, устанавливаем отдельно..."
                npm install hls.js --fetch-timeout=300000 --fetch-retries=5
            fi
        else
            echo "❌ Не удалось установить зависимости"
            exit 1
        fi
    fi
    
    # Финальная проверка наличия всех критических зависимостей
    echo "🔍 Проверка установленных зависимостей..."
    MISSING_DEPS=""
    [ ! -d "node_modules/react" ] && MISSING_DEPS="$MISSING_DEPS react"
    [ ! -d "node_modules/react-dom" ] && MISSING_DEPS="$MISSING_DEPS react-dom"
    [ ! -d "node_modules/hls.js" ] && MISSING_DEPS="$MISSING_DEPS hls.js"
    [ ! -d "node_modules/vite" ] && MISSING_DEPS="$MISSING_DEPS vite"
    
    if [ -n "$MISSING_DEPS" ]; then
        echo "❌ КРИТИЧЕСКАЯ ОШИБКА: Отсутствуют зависимости:$MISSING_DEPS"
        echo "Попытка установить отсутствующие зависимости..."
        npm install $MISSING_DEPS --fetch-timeout=300000 --fetch-retries=5 || exit 1
    fi
    
    echo "✅ Все зависимости проверены и установлены"
else
    echo "✅ Зависимости уже установлены и актуальны (хеш: $CURRENT_HASH)"
    
    # Даже если хеш совпадает, проверяем наличие критических зависимостей
    if [ ! -f "node_modules/hls.js/package.json" ]; then
        echo "⚠️  hls.js отсутствует, устанавливаем..."
        npm install hls.js --fetch-timeout=300000 --fetch-retries=5
    fi
fi

# ФИНАЛЬНАЯ ПРОВЕРКА перед запуском Vite
echo "🔍 Финальная проверка критических зависимостей..."
CRITICAL_DEPS_MISSING=false

# Проверяем каждую критическую зависимость
if [ ! -d "node_modules/react" ]; then
    echo "❌ react отсутствует"
    CRITICAL_DEPS_MISSING=true
fi

if [ ! -d "node_modules/react-dom" ]; then
    echo "❌ react-dom отсутствует"
    CRITICAL_DEPS_MISSING=true
fi

if [ ! -d "node_modules/hls.js" ]; then
    echo "❌ hls.js отсутствует - КРИТИЧНО!"
    CRITICAL_DEPS_MISSING=true
else
    echo "✅ hls.js найден: $(ls -d node_modules/hls.js 2>/dev/null || echo 'не найден')"
fi

if [ ! -d "node_modules/vite" ]; then
    echo "❌ vite отсутствует"
    CRITICAL_DEPS_MISSING=true
fi

if [ "$CRITICAL_DEPS_MISSING" = "true" ]; then
    echo "❌ КРИТИЧЕСКАЯ ОШИБКА: Отсутствуют критические зависимости!"
    echo "Попытка экстренной установки..."
    
    # Пытаемся установить все зависимости
    if npm install --fetch-timeout=300000 --fetch-retries=5; then
        echo "✅ Зависимости установлены с основного registry"
    else
        echo "⚠️  Пробуем альтернативный registry..."
        npm config set registry https://registry.npmmirror.com
        if npm install --fetch-timeout=300000 --fetch-retries=5; then
            echo "✅ Зависимости установлены через альтернативный registry"
            npm config set registry https://registry.npmjs.org
        else
            echo "❌ Не удалось установить зависимости даже через альтернативный registry"
            exit 1
        fi
    fi
    
    # Повторная проверка hls.js
    if [ ! -d "node_modules/hls.js" ]; then
        echo "❌ hls.js всё ещё отсутствует, устанавливаем отдельно..."
        npm install hls.js --fetch-timeout=300000 --fetch-retries=5 || {
            echo "⚠️  Пробуем альтернативный registry для hls.js..."
            npm config set registry https://registry.npmmirror.com
            npm install hls.js --fetch-timeout=300000 --fetch-retries=5
            npm config set registry https://registry.npmjs.org
        }
        
        # Финальная проверка
        if [ ! -d "node_modules/hls.js" ]; then
            echo "❌ КРИТИЧЕСКАЯ ОШИБКА: hls.js не удалось установить!"
            echo "Проверьте подключение к интернету и доступность npm registry"
            exit 1
        fi
    fi
    
    echo "✅ Все критические зависимости установлены"
    echo "📋 Список установленных зависимостей:"
    ls -d node_modules/hls.js node_modules/react node_modules/react-dom node_modules/vite 2>/dev/null | head -5
fi

# Включаем set -e только перед запуском Vite
set -e

echo "🎬 Запуск Vite dev сервера..."
exec npm run dev -- --host 0.0.0.0
