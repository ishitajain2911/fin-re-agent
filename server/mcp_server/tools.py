from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from server.mcp_server.rag import clean_html, chunk_text, embed_chunks, search_chunks, store_chunks
from server.mcp_server.rag import get_cik_for_ticker, get_recent_filing, fetch_filing_document, keyword_search_chunks,filter_chunks_by_metadata
    
mcp = FastMCP(
    "fin-research-tools",
    transport_security=TransportSecuritySettings(
        allowed_hosts=["127.0.0.1:*", "localhost:*", "decorator-simply-seventy.ngrok-free.dev"]
    ),
)

cache_collection = {}
@mcp.tool()
def semantic_search_filings(ticker: str, query: str) -> str:
    """Search SEC filings for a given ticker and query"""

    if ticker not in cache_collection:
        cik = get_cik_for_ticker(ticker)
        accession_number, primary_document,form_type,filing_date = get_recent_filing(cik)
        document=fetch_filing_document(cik, accession_number, primary_document)
        cleaned = clean_html(document)
        chunks=chunk_text(cleaned)
        embeddings = embed_chunks(chunks)
        collection=store_chunks(chunks, embeddings,form_type, filing_date)
        cache_collection[ticker]= collection

    collection = cache_collection[ticker]
    results = search_chunks(collection, query)
    return str(results)

@mcp.tool()
def keyword_search_filings(ticker: str, term: str) -> str:
    ''' Search SEC filings for a given ticker, using a specific term, rather than meaning-based search'''

    if ticker not in cache_collection:
        cik = get_cik_for_ticker(ticker)
        accession_number, primary_document,form_type,filing_date = get_recent_filing(cik)
        document=fetch_filing_document(cik, accession_number, primary_document)
        cleaned = clean_html(document)
        chunks=chunk_text(cleaned)
        embeddings = embed_chunks(chunks)
        collection=store_chunks(chunks, embeddings,form_type,filing_date)
        cache_collection[ticker]= collection
    
    collection = cache_collection[ticker]
    results = keyword_search_chunks(collection, term)
    return str(results)

@mcp.tool()
def filter_filings_by_metadata(ticker: str, form_type: str) -> str:
    " this filters by document TYPE (10-K vs 10-Q),not by meaning or exact wording - contrast with the other two tools"
    if ticker not in cache_collection:
        cik = get_cik_for_ticker(ticker)
        accession_number, primary_document,fetched_form_type,filing_date = get_recent_filing(cik)
        document=fetch_filing_document(cik, accession_number, primary_document)
        cleaned = clean_html(document)
        chunks=chunk_text(cleaned)
        embeddings = embed_chunks(chunks)
        collection=store_chunks(chunks, embeddings,fetched_form_type,filing_date)
        cache_collection[ticker]= collection
    collection = cache_collection[ticker]
    result = filter_chunks_by_metadata(collection,form_type)
    return str(result)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")