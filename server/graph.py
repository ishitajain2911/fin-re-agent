from typing import TypedDict, Optional
from dotenv import load_dotenv
import anthropic
from fastapi import FastAPI
app = FastAPI()
from server.quant import calculate_pe_ratio, calculate_revenue_growth
from langgraph.graph import StateGraph, START, END


load_dotenv()
client = anthropic.Anthropic()



class ResearchState(TypedDict):
    ticker: str
    query: str
    rag_result : Optional[str]
    final_report: Optional[str]
    next_step: Optional[str]
    quant_result:Optional[str]


def supervisor_node(state: ResearchState) -> dict:
    return {"next_step": "fundamentals_node"}


def route_after_supervisor(state: ResearchState) -> str:
    next_step = state["next_step"]
    return next_step

def fundamentals_node(state: ResearchState) -> dict:
    prompt=  f" ticker: {state['ticker']} , query: {state['query']}"  # instead of the hardcoded f-string in main.py

    response = client.beta.messages.tool_runner(
    max_tokens=500,
    model="claude-sonnet-5",
    messages=[{"role": "user", "content": prompt}],
    tools=[{"type": "mcp_toolset", "mcp_server_name": "fin-research-tools"}],
    mcp_servers=[{
        "type": "url",
        "url": "https://decorator-simply-seventy.ngrok-free.dev/mcp",
        "name": "fin-research-tools",
    }],
    betas=["mcp-client-2025-11-20"],
)

    final_message = None
    for message in response:
        final_message = message

    for block in final_message.content:
        if block.type == "text":
            return {"rag_result": block.text}


def quant_node(state: ResearchState) -> dict:


    prompt = f"""You are a quantitative equity analyst.

    Ticker: {state['ticker']}
    Question: {state['query']}

    Financial data:
    - Current share price: $95.00
    - TTM earnings per share: $4.50
    - Most recent full-year revenue: $25,000 million
    - Prior full-year revenue: $15,500 million

    Use your tools to compute the metrics relevant to the question, then briefly
    interpret what they say about the company."""    

    response = client.beta.messages.tool_runner(
        max_tokens=500,
        model="claude-sonnet-5",
        messages=[{"role": "user", "content": prompt}],
        tools=[calculate_pe_ratio,calculate_revenue_growth],
    )



    final_message = None
    for message in response:
        final_message = message

    for block in final_message.content:
        if block.type == "text":
            return {"quant_result": block.text}



builder = StateGraph(ResearchState)
builder.add_node("fundamentals_node", fundamentals_node)
builder.add_node('supervisor_node', supervisor_node)
builder.add_node('quant_node',quant_node)
builder.add_edge(START, "supervisor_node")
builder.add_edge("fundamentals_node", "quant_node")
builder.add_conditional_edges("supervisor_node", route_after_supervisor)
builder.add_edge("quant_node", END)

graph = builder.compile()

if __name__ == "__main__":
    graph = builder.compile()
    result = graph.invoke({"ticker": "MU", "query": "latest 10-K filing", "rag_result": None, "final_report": None})
    print(result)
