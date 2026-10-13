from pydantic import BaseModel, Field
from typing import Literal, Optional

class SynthesisReport(BaseModel):
    summary: str = Field(description= ("A 2-3 sentence answer to the user's query, grounded strictly in the "
            "fundamentals research and quantitative analysis provided. Do not introduce "
            "facts that are not present in those inputs."))

    key_findings: list[str] = Field(description= ("3-6 concrete factual points about the company's valuation, growth, and "
            "financial health, each drawn directly from the fundamentals research or the "
            "quantitative analysis. One point per string."))
    risks: list[str]= Field(description=("Risks to the company or the investment itself, such as cyclicality, "
            "competition, customer concentration, or demand softness. Do NOT list "
            "limitations of this analysis here."))
    caveats: list[str]= Field(description = ("Limitations of THIS analysis: a specialist report was missing or empty, "
            "financial figures were placeholder rather than real, retrieval was thin, or "
            "the two sources disagreed. Empty list if none apply."))
    confidence: Literal["high", "medium", "low"] = Field(
        description=("Overall confidence in this report. 'high' only if both specialist inputs "
            "were present, used real data, and broadly agreed. 'low' if a specialist was "
            "missing or the data was placeholder. 'medium' otherwise."
    ))
    confidence_reason: str = Field(
        description=("One or two sentences explaining the confidence rating: which specialist " 'inputs were present, whether the figures were real or placeholder, and' 
            "whether the fundamentals and quantitative views agreed with each other."
            ))
    
class RetrievalGrade(BaseModel):
    relevant: bool = Field(description=(
        "Do the retrieved chunks actually contain information that answers the user's query, "
        "as opposed to being topically-nearby but not actually useful (e.g. cover-page "
        "boilerplate when asked about revenue)."
    ))

    reason: str = Field(description=(
        "One or two sentences explaining why it was judged relevant or irrelevant."
    ))

    rewritten_query: Optional[str] = Field(description=(
        "Only meaningful when relevant=False: a sharper, more specific version of the "
        "original query that's more likely to retrieve the right chunks. Should be "
        "None/omitted when relevant=True, so the model doesn't generate a pointless "
        "rewrite when the original result was fine."
    ))

class ResearchRequest(BaseModel):
    ticker:str=Field(description=("The ticker for a stock"))
    query: str=Field(description=("The query from user"))
