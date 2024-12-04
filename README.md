# Foodgram

![GitHub Workflow Status](https://github.com/Jlanceth/foodgram/actions/workflows/main.yml/badge.svg)

**Фудграм** — это сайт, который собирает рецепты пользователей и позволяет исследовать новые кулинарные возможности. Вы можете следить за своими любимыми поварами, выкладывать свои рецепты и сохранять чужие!

## Развернутый проект

- [Foodgram](https://foodgra.redirectme.net/)

## Установка

1. Клонируйте себе репозиторий: git clone git@github.com:Reez0n/foodgram.git
2. Заполните файл .env
3. Перейдите в папку infra/
4. Запустите сборку и docker-compose
```bash
docker-compose up -d --build
```

### Запуск на сервере

1. Убедитесь, что `.env` настроен и доступен на сервере.
2. Скопируйте файл `docker-compose.production.yml` на сервер.
3. Подключитесь к серверу и выполните:
    ```bash
    docker-compose -f docker-compose.production.yml up -d
    ```
4. Запустите команды для миграций и сбора статики:
    ```bash
    docker-compose -f docker-compose.production.yml exec backend python manage.py migrate
    docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
    docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
    ```
5. Проект будет доступен по IP-адресу или домену сервера.

## Используемые технологии

- **Backend**: Python 3.9, Django, Django REST Framework
- **Frontend**: React
- **База данных**: PostgreSQL
- **Веб-сервер**: Nginx
- **Контейнеризация**: Docker, Docker Compose
