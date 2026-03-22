# ── Stage 1: Build React frontend ─────────────────────────────────────────
FROM node:20-slim AS builder
WORKDIR /app
COPY frontend/package*.json ./frontend/
RUN npm --prefix frontend install
COPY frontend/ ./frontend/
RUN npm --prefix frontend run build

# ── Stage 2: Python production image ──────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

RUN pip install uv

COPY backend/pyproject.toml .
RUN uv pip install --no-cache-dir --system -r pyproject.toml 2>/dev/null || \
    uv pip install --no-cache-dir --system \
    "fastapi[standard]>=0.115.0" \
    "uvicorn[standard]>=0.29.0" \
    "google-adk>=0.3.0" \
    "google-genai>=1.0.0" \
    "google-cloud-bigquery>=3.20.0" \
    "google-cloud-run>=0.10.0" \
    "google-cloud-aiplatform>=1.60.0" \
    "python-dotenv>=1.0.0" \
    "httpx>=0.27.0"

# Copy backend source
COPY backend/app/ .

# Copy built frontend from Stage 1
# main.py resolves "../../frontend/dist" from /app, which is /frontend/dist
COPY --from=builder /app/frontend/dist /frontend/dist

EXPOSE 8080
CMD ["python", "main.py"]
