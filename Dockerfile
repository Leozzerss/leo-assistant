FROM python:3.13-slim

WORKDIR /app

COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

COPY . .

ENV PORT=8000
ENV LEO_WEATHER_LOCATION="Lezhë, Albania"

EXPOSE 8000

CMD ["python", "-m", "web.server"]
