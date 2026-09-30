# backend_api.py
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from celery.result import AsyncResult
from worker import process_resume_task

app = FastAPI(title="Manalot Talent Scout API", version="1.0")

@app.post("/api/v1/extract-resume/async")
async def process_resume_async(file: UploadFile = File(...)):
    """Accepts the file and instantly hands it off to the Celery worker."""
    if not file.filename.lower().endswith(".pdf"):
        
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / file.filename

    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Dispatch to Redis queue. .delay() is non-blocking!
    task = process_resume_task.delay(str(temp_path))
    
    return {
        "message": "Resume queued for processing.",
        "task_id": task.id
    }

@app.get("/api/v1/task/{task_id}")
async def get_task_status(task_id: str):
    """Allows the Streamlit frontend to check if the background worker is finished."""
    task = AsyncResult(task_id)
    
    if task.state == 'PENDING':
        return {"status": "Processing..."}
    elif task.state == 'SUCCESS':
        return {"status": "Completed", "result": task.result}
    else:
        return {"status": "Failed", "error": str(task.info)}