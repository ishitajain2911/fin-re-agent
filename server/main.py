
from fastapi import FastAPI
from server.graph import graph
from server.schemas import ResearchRequest
app = FastAPI()





@app.get("/health")
def health():
    health_status ={"status": "ok"}
    return health_status

@app.post("/research")
def research(request: ResearchRequest):
    result = graph.invoke({
        "ticker": request.ticker,
        "query": request.query,
    })
    return result["final_report"]

