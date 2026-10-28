# backend_api.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from celery.result import AsyncResult
from worker import process_resume_task
from app.utils.uploads import MAX_UPLOAD_BYTES, safe_upload_path

app = FastAPI(title="Manalot Talent Scout API", version="1.0")

@app.post("/api/v1/extract-resume/async")
async def process_resume_async(file: UploadFile = File(...)):
    """Accepts the file and instantly hands it off to the Celery worker."""
    if not file.filename.lower().endswith(".pdf"):
        
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_path = safe_upload_path(file.filename)

    size = 0
    with temp_path.open("wb") as buffer:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                break
            buffer.write(chunk)
    if size > MAX_UPLOAD_BYTES:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=413, detail="File too large (max 10 MB).")

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