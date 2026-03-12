FROM python:3.12-slim AS base

# System deps for pdfplumber + OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpoppler-cpp-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM deps AS runner
# Non-root user
RUN useradd --system --uid 1001 --create-home appuser

COPY --chown=appuser:appuser . .

# Copy core/ modules from additional build context
COPY --from=core --chown=appuser:appuser / /app/core/

RUN mkdir -p /app/uploads && chown appuser:appuser /app/uploads && \
    chmod +x /app/entrypoint.sh

USER appuser

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
