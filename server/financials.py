import httpx
from server.mcp_server.rag import get_cik_for_ticker
from datetime import date
from typing import Optional

def get_annual_revenue(ticker: str) -> Optional[dict]:
    cik = get_cik_for_ticker(ticker)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    headers = {"User-Agent": "Ishita ishitajain2931@gmail.com"} 
    response = httpx.get(url, headers=headers)
    data= response.json()
    concepts = data['facts']['us-gaap']

    for name in ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"]:
        if name not in concepts: 
            continue
   
        entries = concepts[name]["units"]["USD"]
        list_of_entries =[]
        for entry in entries:
            if entry['form']=="10-K":
                days= (date.fromisoformat((entry["end"]))- date.fromisoformat((entry["start"]))).days
                if days >= 350 and days <=380:
                    list_of_entries.append(entry)

        by_end = {}
    
    
        for an_entry in list_of_entries:
            by_end[an_entry["end"]]=an_entry
        annual = sorted(by_end.values(), key=lambda e: e["end"])

        if len(annual)< 2:
            continue
        if (date.today() - date.fromisoformat(annual[-1]["end"])).days > 730:
            continue

        return {"current_revenue": annual[-1]["val"],"prior_revenue": annual[-2]["val"],"current_period_end": annual[-1]["end"], "prior_period_end": annual[-2]["end"],}
    return None


if __name__ == "__main__":
    result = get_annual_revenue("MU")
    print(result)
    assert result is not None

    current_end = date.fromisoformat(result["current_period_end"])
    prior_end = date.fromisoformat(result["prior_period_end"])

    assert current_end > prior_end, "current period should be after prior"
    gap = (current_end - prior_end).days
    assert 350<= gap<=380, f"periods should be ~1 year apart, got {gap} days"
    assert (date.today() - current_end).days <= 730, "latest data is stale"
    assert result["current_revenue"] > 0 and result["prior_revenue"] > 0, "revenues should be positive"

    for t in ["MSFT", "TSLA", "CB", "SNDK"]:
        print(t, get_annual_revenue(t))

        
   