FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY web/requirements.txt web/requirements.txt
RUN pip install --no-cache-dir -r web/requirements.txt

COPY models/ models/
COPY data/housing_clean.csv data/housing_clean.csv
COPY reports/model_comparison.csv reports/model_comparison.csv
COPY web/ web/

EXPOSE 7860
CMD ["uvicorn", "web.server:app", "--host", "0.0.0.0", "--port", "7860"]
