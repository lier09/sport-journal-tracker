FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_BROWSER_READING_STATE=1
ENV VITE_BROWSER_READING_STATE=${VITE_BROWSER_READING_STATE}
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0
COPY requirements-web.txt ./requirements-web.txt
RUN pip install --no-cache-dir -r requirements-web.txt
COPY api.py ./api.py
COPY src/ ./src/
COPY config/ ./config/
COPY data/journal_tracker.db ./data/journal_tracker.db
COPY --from=frontend /app/frontend/dist ./frontend/dist
EXPOSE 10000
CMD ["python", "api.py"]
