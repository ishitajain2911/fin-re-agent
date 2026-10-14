from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from server.mcp_server.rag import get_ticker_collection, search_chunks,keyword_search_chunks,filter_chunks_by_metadata
from server.mcp_server.rag import retrieve_with_grading
mcp = FastMCP(
    "fin-research-tools",
    port=8001,
    transport_security=TransportSecuritySettings(
        allowed_hosts=["127.0.0.1:*", "localhost:*", "decorator-simply-seventy.ngrok-free.dev"]
    ),
)


@mcp.tool()
def semantic_search_filings(ticker: str, query: str) -> str:
    """Search SEC filings for a given ticker and query"""
    collection=get_ticker_collection(ticker)
    if collection.count() ==0:
        return f"No filings ingested for {ticker.upper()} yet."

    results = retrieve_with_grading(collection, query, search_chunks)
    return str(results)

@mcp.tool()
def keyword_search_filings(ticker: str, term: str) -> str:
    ''' Search SEC filings for a given ticker, using a specific term, rather than meaning-based search'''
    collection=get_ticker_collection(ticker)
    if collection.count() ==0:
        return f"No filings ingested for {ticker.upper()} yet."
    
    results = keyword_search_chunks(collection, term)
    return str(results)

@mcp.tool()
def filter_filings_by_metadata(ticker: str, form_type: str) -> str:
    " this filters by document TYPE (10-K vs 10-Q),not by meaning or exact wording - contrast with the other two tools"
    collection=get_ticker_collection(ticker)
    if collection.count() ==0:
        return f"No filings ingested for {ticker.upper()} yet."
    
    result = filter_chunks_by_metadata(collection,form_type)
    return str(result)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")