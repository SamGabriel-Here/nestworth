# Deploying the web app to Hugging Face Spaces

The custom frontend (`web/static/`) is served by a FastAPI backend (`web/server.py`)
that runs the trained model. The repo root has a `Dockerfile` that builds it.

## Run locally

```bash
pip install -r web/requirements.txt
uvicorn web.server:app --reload --port 7860
# open http://localhost:7860
```

## Deploy on Hugging Face Spaces (Docker)

1. Create a Space at https://huggingface.co/new-space
   - **SDK:** Docker (blank template)
   - **Name:** `nestworth`

2. A Space is a git repo. Clone it locally:

   ```bash
   git clone https://huggingface.co/spaces/<your-username>/nestworth hf-nestworth
   ```

3. Copy these into the Space repo (everything the Dockerfile needs):

   ```
   Dockerfile
   web/
   models/
   data/housing_clean.csv
   reports/model_comparison.csv
   ```

4. Create a `README.md` in the Space repo with this front-matter (Spaces read it
   to configure the container):

   ```
   ---
   title: NestWorth
   emoji: 🏠
   colorFrom: green
   colorTo: gray
   sdk: docker
   app_port: 7860
   pinned: false
   ---

   Home price estimates for Indian metro cities. FastAPI + a hand-built frontend.
   ```

5. Push:

   ```bash
   cd hf-nestworth
   git add . && git commit -m "NestWorth" && git push
   ```

Hugging Face builds the Docker image (first build takes a few minutes — watch the
**Logs** tab) and serves it at `https://huggingface.co/spaces/<your-username>/nestworth`.
