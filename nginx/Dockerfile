FROM nginx:alpine

# Копируем конфигурацию
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Создаем директории для логов и certbot
RUN mkdir -p /var/www/certbot /var/log/nginx

# Устанавливаем certbot для получения SSL сертификатов
RUN apk add --no-cache certbot certbot-nginx

# Открываем порты
EXPOSE 80 443

# Команда запуска
CMD ["nginx", "-g", "daemon off;"]

