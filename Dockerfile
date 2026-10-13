FROM python:3.11-slim

WORKDIR /app

# install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy application code
COPY . .

# SQLite DB lives in /app/data -> mounted from the Docker volume "library_data"
RUN mkdir -p /app/data
ENV LIBRARY_DB=/app/data/library.db

EXPOSE 5000
CMD ["python", "app.py"]
