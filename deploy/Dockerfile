# Backend image (also still builds the Streamlit UI — the `streamlit` compose
# service was retired in the 2026-09-04 cutover but frontend/ is kept in the
# repo and image for rollback; see deploy/docker-compose.yml.
# Base is multi-arch: x86 locally, ARM64 on Graviton (t4g) — pip resolves wheels.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/cache/huggingface

WORKDIR /app

# curl for healthchecks
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# CPU-only torch: the default linux wheel bundles CUDA (~3 GB) that a CPU
# container never uses. CPU wheels are ~10x smaller and much faster to pull.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY frontend/ frontend/
COPY run.py .

# Bake the embedding + cross-encoder models into the image so the first
# request isn't cold (adds ~400 MB; still well under t4g.small's 20 GB disk).
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('BAAI/bge-small-en-v1.5'); CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

EXPOSE 8000 8501
