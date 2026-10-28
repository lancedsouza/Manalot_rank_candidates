# FLOW-06 Poll task status

```mermaid
zenuml
    title FLOW-06 Poll task status
    @Actor Client
    @Boundary FastAPI
    @Queue CeleryBackend
    Client->FastAPI.GET /api/v1/task/id {
      state = CeleryBackend.AsyncResult(id).state
      if(PENDING) {
        return "Processing..."
      } else if(SUCCESS) {
        return "Completed" + result
      } else {
        return "Failed" + error
      }
    }
```

Note: an unknown task id is also `PENDING`, so it reports "Processing..." forever. A task whose pipeline raised still ends `SUCCESS` with `{"status": "failed"}` inside `result`, because the worker catches the exception.
