# Foodgram

**Фудграм** — это сайт, который собирает рецепты пользователей и позволяет исследовать новые кулинарные возможности. Вы можете следить за своими любимыми поварами, выкладывать свои рецепты и сохранять чужие!

## Как запустить проект

### 1. Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone https://github.com/yandex-praktikum/foodgram.git
cd foodgram

cd foodgram
Cоздать и активировать виртуальное окружение:

python3 -m venv env
Если у вас Linux/macOS

source env/bin/activate
Если у вас windows

source env/scripts/activate
python3 -m pip install --upgrade pip
Установить зависимости из файла requirements.txt:

pip install -r requirements.txt
Выполнить миграции:

python3 manage.py migrate
Запустить проект:

python3 manage.py runserver
```