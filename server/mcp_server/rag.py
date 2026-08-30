from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import voyageai
import chromadb
import time
import httpx

load_dotenv()

def clean_html(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    ix_header = soup.find("ix:header")
    if ix_header:
        ix_header.decompose()
    text = soup.get_text(separator="\n")
    return text


def chunk_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_text(text)
    return chunks


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    client = voyageai.Client()
    batch_size = 5

    all_embeddings = []

    for i in range(0, len(chunks), batch_size):         
        batch = chunks[i:batch_size + i]                   

        result = client.embed(batch, model="voyage-3", input_type="document")
        all_embeddings.extend(result.embeddings)       

        is_last_batch =  i+ batch_size >= len(chunks)                     
        if not is_last_batch:
            time.sleep(25)

    return all_embeddings


def store_chunks(chunks: list[str], embeddings: list[list[float]]) -> None:
    client = chromadb.Client()  
    collection = client.create_collection("filings")
    ids = [str(index) for index, chunk in enumerate(chunks)]
    collection.add(ids=ids, embeddings=embeddings, documents=chunks)
    return collection

def search_chunks(collection, query: str, n_results: int = 3):
    client = voyageai.Client()
    result = client.embed([query], model = "voyage-3", input_type= "query")
    query_embedding = result.embeddings[0]  # just the one vector, not a list of one
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    return results


def get_cik_for_ticker(ticker: str) -> str:
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": "Ishita ishitajain2931@gmail.com"} 
    response = httpx.get(url, headers=headers)
    response_json=response.json()
    for entry in response_json.values():
        if entry["ticker"]==ticker.upper():
            return str(entry["cik_str"]).zfill(10)
        

def get_recent_filing(cik: str) -> dict:
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {"User-Agent": "Ishita ishitajain2931@gmail.com"}
    response = httpx.get(url, headers=headers)
    data = response.json()

    filings = data["filings"]["recent"]

    for index, form in enumerate(filings["form"]):
        if form in ("10-K","10-Q"):
            return filings["accessionNumber"][index], filings["primaryDocument"][index]



def fetch_filing_document(cik: str, accession_number: str, primary_document: str) -> str:
    cik = int(cik)
    accession_number = accession_number.replace("-","")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{primary_document}"
    headers = {"User-Agent": "Ishita ishitajain2931@gmail.com"}
    response = httpx.get(url, headers=headers)
    return response.text

