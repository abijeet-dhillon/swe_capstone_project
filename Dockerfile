# syntax=docker/dockerfile:1

FROM python:3.10-alpine
WORKDIR /code
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN apk add --no-cache ffmpeg
COPY . .
CMD ["python", "-m", "src.main"]