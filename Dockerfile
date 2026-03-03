FROM python:3.11-slim

WORKDIR /app
COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

RUN python manage.py collectstatic --noinput

EXPOSE 8000


RUN pip install gunicorn

CMD ["gunicorn", "library_system.wsgi:application", "--bind", "0.0.0.0:8000"]