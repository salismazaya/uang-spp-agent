FROM python:3.10.13-bullseye

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN python manage.py collectstatic --no-input
CMD gunicorn project.wsgi