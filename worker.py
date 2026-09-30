import redis
from celery import Celery
from pathlib import Path 
from dotenv import load_dotenv
import os
from app.utils.resume_cache import process_resume


load_dotenv()
REDIS_URL=os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ValueError("FATAL ERROR:REDIS_URL NOT FOUND IN .ENV")


# Configurpe celery app to th cloud broker

celery_app = Celery("ats_tasks", broker=REDIS_URL, backend=REDIS_URL)


# 3. Add production reliability settings for cloud latency
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',  # Set to your local time
)

@celery_app.task(bind=True, name="process_resume")
def process_resume_task(self, file_path: str):
    """Background worker that runs the LLM pipeline."""
    path_obj = Path(file_path)
    
    try:
        resume_data = process_resume(path_obj)
        return {"status": "success", "candidate": resume_data.model_dump()}
    
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        if path_obj.exists():
            path_obj.unlink()




