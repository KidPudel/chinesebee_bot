FROM python:3.13.0b1-bookworm AS build-stage

WORKDIR /app

COPY requirements.txt ./

RUN pip install -r --no-cache-dir requirements.txt

COPY . .

CMD ["python", "main.py"]