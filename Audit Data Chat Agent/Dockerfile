# Builds the React frontend, then serves it (as static files) plus the FastAPI
# API from a single Python container — see api_server.py's mount at the bottom.

FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app

COPY requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

COPY src/ ./src/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

ENV PORT=8787
EXPOSE 8787
CMD ["sh", "-c", "uvicorn api_server:app --host 0.0.0.0 --port ${PORT} --app-dir src"]
