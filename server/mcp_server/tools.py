from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from server.mcp_server.rag import clean_html, chunk_text, embed_chunks, search_chunks, store_chunks
from server.mcp_server.rag import get_cik_for_ticker, get_recent_filing, fetch_filing_document
    
mcp = FastMCP(
    "fin-research-tools",
    transport_security=TransportSecuritySettings(
        allowed_hosts=["127.0.0.1:*", "localhost:*", "decorator-simply-seventy.ngrok-free.dev"]
    ),
)

cache_collection = {}
@mcp.tool()
def search_filings(ticker: str, query: str) -> str:
    """Search SEC filings for a given ticker and query"""

    if ticker not in cache_collection:
        cik = get_cik_for_ticker(ticker)
        accession_number, primary_document = get_recent_filing(cik)
        document=fetch_filing_document(cik, accession_number, primary_document)
        cleaned = clean_html(document)
        chunks=chunk_text(cleaned)
        embeddings = embed_chunks(chunks)
        collection=store_chunks(chunks, embeddings)
        cache_collection[ticker]= collection

    collection = cache_collection[ticker]
    results = search_chunks(collection, query)
    return str(results)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")