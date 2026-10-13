from server.mcp_server.rag import get_ticker_collection, get_cik_for_ticker, get_recent_filing, fetch_filing_document
from server.mcp_server.rag import chunk_text, clean_html,embed_chunks,store_chunks


def ingest(tickers: list[str]) -> None:


    for ticker in tickers:
        collection= get_ticker_collection(ticker)
        if collection.count() > 0:
            print(f"{ticker}: skipped, already ingested")
            continue
        cik= get_cik_for_ticker(ticker)
        accession_number, primary_document, form_type, filing_date = get_recent_filing(cik)
        filing_doc= fetch_filing_document(cik, accession_number, primary_document)
        text= clean_html(filing_doc)
        chunks = chunk_text(text)
        print(f"{ticker}: embedding {len(chunks)} chunks...")
        embeddings=embed_chunks(chunks)
        store_chunks(ticker, chunks, embeddings, form_type, filing_date)
        print(f"{ticker}: stored {len(chunks)} chunks")


       

if __name__ == "__main__":
    ingest(["MU"])
