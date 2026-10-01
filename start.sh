#!/bin/bash

# 1. Start the Celery AI Worker in the background (&)
celery -A worker worker --loglevel=info &

# 2. Start the FastAPI Server in the background on port 8000 (&)
uvicorn backend_api:app --host 0.0.0.0 --port 8000 &

# 3. Start Streamlit on port 7860 (Hugging Face requires port 7860)
streamlit run streamlit_app.py --server.port 7860 --server.address 0.0.0.0
