from typing import TypedDict, Optional
from dotenv import load_dotenv
import anthropic
from server.quant import calculate_pe_ratio, calculate_revenue_growth
from langgraph.graph import StateGraph, START, END
from server.schemas import SynthesisReport
from server.financials import get_annual_revenue
from datetime import date



load_dotenv()
client = anthropic.Anthropic()



class ResearchState(TypedDict):
    ticker: str
    query: str
    financials: Optional[dict]
    rag_result : Optional[str]
    final_report: Optional[SynthesisReport]
    next_step: Optional[str]
    quant_result:Optional[str]


def supervisor_node(state: ResearchState) -> dict:
    return {"next_step": "fundamentals_node"}


def route_after_supervisor(state: ResearchState) -> str:
    next_step = state["next_step"]
    return next_step

def fundamentals_node(state: ResearchState) -> dict:
    prompt=  f" ticker: {state['ticker']} , query: {state['query']}"  # instead of the hardcoded f string in main.py
    try:
        response = client.beta.messages.tool_runner(
        max_tokens=1000,
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
    
        return {"rag_result":None}
    except Exception as e:
        print(f"fundamentals node failed: {e}")
        return{"rag_result":None}

        
def financial_data_node(state: ResearchState) -> dict:
    ticker= state["ticker"]
    annual_revenue = get_annual_revenue(ticker)

    return{"financials": annual_revenue}

   
def quant_node(state: ResearchState) -> dict:
    financials = state.get("financials")
    if financials is None:
        return {"quant_result":None}

    current_m = financials["current_revenue"] / 1_000_000.
    prior_m = financials["prior_revenue"] / 1_000_000.

    prompt = f"""You are a quantitative equity analyst.

    Ticker: {state['ticker']}
    Today's date: {date.today()}
    Question: {state['query']}
    Financial data (annual revenue, in millions of USD):
    - Fiscal year ended {financials["current_period_end"]}: ${current_m:,.0f} million
    - Fiscal year ended {financials["prior_period_end"]}: ${prior_m:,.0f} million




    Use your tools to compute the metrics relevant to the question, then keep it to a few sentences when you
    interpret what they say about the company.
    Only annual revenue is available, and if the question needs valuation figures like P/E, say they are unavailable and don't estimate them.
    Interpret only what the two revenue figures show, and don't speculate about causes or industry conditions.
    Both figures are full fiscal years, already verified as ~1-year periods. 52/53-week years are normal, so don't question comparability based on the end dates.
    A large growth rate is a finding to report, not evidence of a data problem.
    Filings dated before today are real reported data, not projections."""    

    response = client.beta.messages.tool_runner(
        max_tokens=1000,
        model="claude-sonnet-5",
        messages=[{"role": "user", "content": prompt}],
        tools=[calculate_revenue_growth],
    )



    final_message = None
    for message in response:
        final_message = message

    for block in final_message.content:
        if block.type == "text":
            return {"quant_result": block.text}




def synthesis_node(state: ResearchState) -> dict:
    ticker = state["ticker"]
    query = state["query"]
    rag = state.get("rag_result")     
    quant = state.get("quant_result") 

    if rag is None:
        fundamentals_section = " fundamental specialist did not run"
    else:
        fundamentals_section = f"fundamental setion: \n{rag}"

    if quant is None:
        quant_section = "quant specialist did not run"
    else:
        quant_section  = f"quant specialist: \n{quant}"

    user_content = f""" Ticker: {ticker}
    Query:{query}
    {fundamentals_section}
    
    {quant_section}
    """


    system_prompt = (
        "You are an equity research analyst. Your job is to combine two specialist "
        "reports — a fundamentals report and a quantitative report — into a single "
        "coherent analysis for the given ticker.\n\n"
        "Rules:\n"
        "- Use ONLY the information in the two sections provided in the user message. "
        "Do not add outside knowledge about the company, do not invent figures, and do "
        "not fill gaps from memory. If the sections do not support a claim, leave it out.\n"
        "- Where the two reports disagree, or where one is missing or thin, say so "
        "explicitly in the caveats and let the summary reflect that uncertainty rather "
        "than smoothing it over.\n"
        "- Populate each field from the evidence. An empty list is fine when there is "
        "nothing to report — do not pad.\n"
        "- The summary must answer the user's actual question, not give a generic "
        "company overview.\n"
        "- Only flag an inconsistency if periods don't match (quarter vs year) or related figures don't reconcile beyond rounding (revenue − COGS ≠ gross profit).\n"
        "- Unusual growth or margin changes are findings, not errors — report them in key_findings.\n"
        "- Some companies (e.g. insurers and banks) don't report COGS or gross profit at all. A missing figure isn't an inconsistency.\n"

    )


    # --- 6. the structured call  ---
    response = client.messages.parse(
        model="claude-opus-5",
        max_tokens=16000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
        output_format=SynthesisReport,
    )
    report = response.parsed_output   # validated SynthesisReport instance

    sources_agree = False

    if rag is None or quant is None:
        level = "low"
    elif sources_agree:
        level = "high"
    else:
        level = "medium"

    reasons = []

    if rag is None:
        reasons.append("fundamentals specialist did not run")
    if quant is None:
        reasons.append("quant specialist did not run")

    if reasons:
        reason = f"Confidence limited : {';'.join(reasons)}"
    else:
        reason = "Both specialists ran with real data"

    
    report.confidence = level
    report.confidence_reason = reason
    
    return {"final_report": report}



builder = StateGraph(ResearchState)
builder.add_node("fundamentals_node", fundamentals_node)
builder.add_node('supervisor_node', supervisor_node)
builder.add_node('financial_data_node',financial_data_node)
builder.add_node('quant_node',quant_node)
builder.add_node("synthesis_node", synthesis_node)


builder.add_edge(START, "supervisor_node")
builder.add_edge("fundamentals_node", "financial_data_node")
builder.add_conditional_edges("supervisor_node", route_after_supervisor)
builder.add_edge("financial_data_node", "quant_node")
builder.add_edge("quant_node", "synthesis_node")
builder.add_edge("synthesis_node",END)

graph = builder.compile()

if __name__ == "__main__":
    query = "How fast is revenue growing year over year?"

    # 1. Real EDGAR fetch through the node
    fin_update = financial_data_node({"ticker": "MU", "query": query})
    print("1. financial_data_node:", fin_update)

    # 2. quant_node with the real financials
    quant_state = {"ticker": "MU", "query": query, "financials": fin_update["financials"]}
    print("\n2. quant_node (growth question):")
    print(quant_node(quant_state))

    # 3. A valuation question: should say P/E is unavailable, not estimate it
    valuation_state = {**quant_state, "query": "Is MU's valuation reasonable?"}
    print("\n3. quant_node (valuation question):")
    print(quant_node(valuation_state))

    # 4. Failure path: no financials -> {"quant_result": None}, no API call
    print("\n4. quant_node (no financials):")
    print(quant_node({"ticker": "MU", "query": query, "financials": None}))
