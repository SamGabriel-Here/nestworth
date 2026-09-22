FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    CUDA_VISIBLE_DEVICES=-1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir -e .

COPY artifacts/ artifacts/
COPY data/housing_clean.csv data/housing_clean.csv
COPY main.py .

EXPOSE 7860
CMD ["python", "-u", "main.py"]
