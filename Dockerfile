FROM python:3.13.0b1-slim-bookworm AS build-stage

WORKDIR /app

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]