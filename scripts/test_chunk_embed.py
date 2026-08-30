from server.mcp_server.rag import clean_html, chunk_text, embed_chunks, search_chunks, store_chunks
from server.mcp_server.rag import get_cik_for_ticker, get_recent_filing, fetch_filing_document
    

if __name__ == "__main__":
    cik = get_cik_for_ticker("MU")
    accession_number, primary_document = get_recent_filing(cik)
    document = fetch_filing_document(cik, accession_number, primary_document)
    cleaned = clean_html(document)
    result = chunk_text(cleaned)
    print(len(result))
    print(result[0])
    embeddings = embed_chunks(result)
    print(len(embeddings))
    print(len(embeddings[0]))

    collection = store_chunks(result, embeddings)
    print("stored successfully")
    results = search_chunks(collection, "What is Micron's revenue?")
    print(results)

    