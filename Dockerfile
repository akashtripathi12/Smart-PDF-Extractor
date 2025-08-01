# --- Build Stage ---
# This stage installs all build-time dependencies and Python packages.
FROM python:3.11-slim-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"
ENV CUDA_VISIBLE_DEVICES=""

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    # Clean up apt caches immediately after install
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy the Python source code
COPY src/ src/

# Install all Python dependencies
RUN pip install --no-cache-dir \
    pillow==10.1.0 \
    pymupdf==1.23.26 \
    pytesseract==0.3.10

# --- Runtime Stage ---
# This stage uses a much smaller base image and copies only the necessary files.
FROM python:3.11-slim-bookworm AS runner

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"
ENV CUDA_VISIBLE_DEVICES=""

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy installed Python packages from the builder stage and application source code
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /app/src/ /app/src/

# Remove __pycache__ from source code if not compiled
RUN find . -type d -name '__pycache__' -exec rm -rf {} +

# Create and switch to a non-root user for security
RUN useradd -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

CMD ["python", "src/main.py"]