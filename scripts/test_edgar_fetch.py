from server.mcp_server.rag import get_cik_for_ticker, get_recent_filing, fetch_filing_document

if __name__ == "__main__":        
    cik = get_cik_for_ticker("MU")
    accession_number, primary_document = get_recent_filing(cik)
    document = fetch_filing_document(cik, accession_number, primary_document)
    print(len(document))
