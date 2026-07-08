FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    CUDA_VISIBLE_DEVICES=-1

WORKDIR /app

COPY web/requirements.txt web/requirements.txt
RUN pip install --no-cache-dir -r web/requirements.txt

COPY models/ models/
COPY data/housing_clean.csv data/housing_clean.csv
COPY reports/model_comparison.csv reports/model_comparison.csv
COPY web/ web/

EXPOSE 7860
CMD ["python", "-u", "-c", "import web.server, uvicorn; uvicorn.run(web.server.app, host='0.0.0.0', port=7860, log_level='info')"]
