FROM python:3.10.9-alpine3.17

WORKDIR /app
COPY . .

RUN apk update
RUN apk add make automake gcc g++ subversion python3-dev

RUN pip install -r requirements.txt
RUN python manage.py collectstatic --no-input
CMD gunicorn project.wsgi