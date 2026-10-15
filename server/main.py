from fastapi import FastAPI
from server.graph import graph
from server.schemas import ResearchRequest
from server.db import init_db, save_report, get_cached_report,list_reports
app = FastAPI()
init_db()                  # runs once when the server starts; safe thanks to IF NOT EXISTS


@app.get("/health")
def health():
    health_status = {"status": "ok"}
    return health_status


@app.post("/research")
def research(request: ResearchRequest):
    ticker = request.ticker.strip().upper()                        # blank 1: normalise request.ticker
    query = request.query.strip().lower()                         # blank 2: normalise request.query

    cached = get_cached_report(ticker, query)
    if cached is not None:                             # blank 3: when do we return the cached one?
        print(f"cache hit: {ticker} / {query}")
        return cached

    result = graph.invoke({
        "ticker": ticker,
        "query": query,
    })
    report = result["final_report"]

    if report is not None:
        save_report(ticker, query, report)                             # blank 4: save it (3 arguments, in the order db.py expects)
    return report

@app.get("/reports")
def get_reports():
    return list_reports()                          # blank 4
