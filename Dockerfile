FROM python:3.10.9-alpine3.17

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN python manage.py collectstatic --no-input
CMD gunicorn project.wsgi