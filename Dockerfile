FROM python:3.13-slim-bullseye
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache -r /app/requirements.txt
COPY . /app/
CMD ["python", "-m", "main"]