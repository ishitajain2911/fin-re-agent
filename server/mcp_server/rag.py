from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import voyageai
import chromadb
import time
import httpx
import anthropic
from server.schemas import RetrievalGrade

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


def store_chunks(chunks: list[str], embeddings: list[list[float]],form_type:str,filing_date:str) -> None:
    client = chromadb.Client()  
    collection = client.create_collection("filings")
    ids = [str(index) for index, chunk in enumerate(chunks)]
    chunk_metadata = {"form_type": form_type, "filing_date": filing_date}
    metadatas = [chunk_metadata for _ in chunks] 

    collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
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
            return filings["accessionNumber"][index], filings["primaryDocument"][index],form,filings["filingDate"][index]
        

def fetch_filing_document(cik: str, accession_number: str, primary_document: str) -> str:
    cik = int(cik)
    accession_number = accession_number.replace("-","")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{primary_document}"
    headers = {"User-Agent": "Ishita ishitajain2931@gmail.com"}
    response = httpx.get(url, headers=headers)
    return response.text

def keyword_search_chunks(collection, term: str, n_results: int = 3):
    results = collection.get(where_document ={"$contains":term}, limit= n_results)
    return results


def filter_chunks_by_metadata(collection, form_type: str, n_results: int = 3):
    results = collection.get(where={"form_type": form_type}, limit=n_results)
    return results

client = anthropic.Anthropic()

def grade_retrieval(query: str, retrieved_text: str) -> RetrievalGrade:
    system_prompt = (
     "You are a retrieval-quality grader for a financial research system. Given a "
    "user's search query and a piece of text retrieved for it, your job is to judge "
    "whether that text actually answers or addresses the query.\n\n"
    "Rules:\n"
    "- Be skeptical of matches that are merely topically nearby but don't actually "
    "contain the answer (e.g. cover-page boilerplate or unrelated risk-factor text "
    "when the query asks about revenue).\n"
    "- Judge relevance only — not writing quality, completeness, or tone.\n"
    "- If relevant=False, you MUST provide a rewritten_query: a sharper, more "
    "specific version of the original query more likely to retrieve the right text. "
    "If relevant=True, leave rewritten_query empty."
    )
    user_facing_content= f" query: {query} , retrieved_text: {retrieved_text}"    

    response = client.messages.parse(
    max_tokens=500,
    model="claude-sonnet-5",
    system=system_prompt,
    messages=[{"role": "user", "content": user_facing_content}],
    output_format=RetrievalGrade,
    )
    return response.parsed_output
    

def retrieve_with_grading(collection, query: str, search_fn, max_attempts: int = 2):
    
    for attempt in range(max_attempts):
        results = search_fn(collection,query)
        filtered_result= results["documents"]
        retrieved_text=" ".join(filtered_result)
        grade = grade_retrieval(query,retrieved_text)
        if grade.relevant:
            return results
        else:
            query = grade.rewritten_query

    return results
    

if __name__ == "__main__":
    chroma_client = chromadb.Client()
    test_collection = chroma_client.create_collection("test")
    fake_ids = ["1", "2", "3"]

    fake_documents = [
        "The company recorded a significant impairment charge on goodwill this quarter.",
        "Revenue increased 15% year over year due to strong product demand.",
        "Management reviewed impairment testing procedures during the annual audit.",
    ]
    test_term = "impairment"

    test_collection.add(ids= fake_ids, documents=fake_documents)
    result = keyword_search_chunks(test_collection, test_term)
    print(result["documents"])

    test_metadata_collection= chroma_client.create_collection("test_metadata")

    fake_ids_meta = ["1", "2", "3", "4"]

    fake_documents_meta = [
        "The annual report highlights strong performance across all segments.",
        "Quarterly revenue increased due to seasonal demand.",
        "This year's results reflect continued investment in R&D.",
        "This quarter's results were impacted by supply chain disruptions.",
    ]

    fake_metadatas = [
        {"form_type": "10-K", "filing_date": "2025-01-15"},
        {"form_type": "10-Q", "filing_date": "2025-04-15"},
        {"form_type": "10-K", "filing_date": "2025-01-15"},
        {"form_type": "10-Q", "filing_date": "2025-04-15"},
    ]

    test_form_type = "10-K"

    test_metadata_collection.add(ids=fake_ids_meta,documents=fake_documents_meta,metadatas= fake_metadatas)
    result = filter_chunks_by_metadata(test_metadata_collection,test_form_type)
    print (result["documents"])
    print(result["metadatas"])

    grading_test_collection = chroma_client.create_collection("test_grading")

    fake_ids_grading = ["1", "2", "3"]

    fake_documents_grading = [
        "Total revenue for the quarter grew 18% year over year, driven by strong demand.",
        "Revenue by segment: data center products grew fastest, followed by consumer products.",
        "Gross margin expanded due to favorable product mix and higher revenue per unit.",
    ]

    bad_query = "employee headcount and benefits"

    grading_test_collection.add(ids=fake_ids_grading,documents= fake_documents_grading)
    result = retrieve_with_grading(grading_test_collection,bad_query,keyword_search_chunks ,max_attempts=2)
    print(result["documents"])

    
