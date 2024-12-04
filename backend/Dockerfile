FROM python:3.9

RUN apt-get update && apt-get install -y \
    fontconfig \
    && apt-get clean

WORKDIR /app

COPY recipes/fonts/ /usr/share/fonts/truetype/

RUN fc-cache -f -v

COPY . .

RUN pip install -r requirements.txt --no-cache-dir

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]