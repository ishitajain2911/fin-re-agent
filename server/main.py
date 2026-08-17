from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    health_status ={"status": "ok"}
    return health_status
