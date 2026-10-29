```mermaid
zenuml
title FLOW-06 Poll task status
@Actor Client as "Streamlit UI or API client"
@Boundary API as "FastAPI (backend.py)"
@Control Celery as "Celery app (worker.py)"
@Database Redis as "Redis result backend (REDIS_URL)"

// `GET /api/v1/task/{task_id}` with header X-API-Key, polled every 2 s by FLOW-02
Client->API.get_task_status(task_id) {
  if("MANALOT_API_KEY unset") {
    @return API->Client: 503 API key not configured
  }
  if("X-API-Key missing or wrong") {
    @return API->Client: 401 invalid or missing API key
  }
  result = Celery.AsyncResult(task_id) {
    meta = Redis.get(celeryTaskMeta)
    if("no meta stored") {
      // unknown or expired ids look the same as queued ones
      return PENDING
    }
    return "state, result, info"
  }
  if("state is PENDING, STARTED or RETRY") {
    @return API->Client: status Processing...
  }
  if(state == SUCCESS) {
    @return API->Client: status Completed, result
  }
  // FAILURE (worker errors propagate) or REVOKED; error is str(task.info)
  return "status Failed, error"
}
```
