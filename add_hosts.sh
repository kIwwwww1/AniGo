#!/bin/bash

# Скрипт для добавления yumivo.ru в /etc/hosts

if grep -q "yumivo.ru" /etc/hosts; then
    echo "✅ Строки для yumivo.ru уже есть в /etc/hosts"
    grep "yumivo.ru" /etc/hosts
else
    echo "Добавляю строки в /etc/hosts..."
    echo "127.0.0.1    yumivo.ru" | sudo tee -a /etc/hosts
    echo "127.0.0.1    www.yumivo.ru" | sudo tee -a /etc/hosts
    echo "✅ Строки добавлены в /etc/hosts"
fi

echo ""
echo "Текущее содержимое /etc/hosts (строки с yumivo.ru):"
grep "yumivo.ru" /etc/hosts || echo "Не найдено"
