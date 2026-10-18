from server.mcp_server.rag import get_cik_for_ticker
import httpx 
from datetime import date


def print_annual(concepts: dict, name: str) -> None:
    """Print every annual (~1 year) 10-K entry for one XBRL concept."""
    if name not in concepts:                      # concept missing → say so and stop
        print(f"{name}: not reported")
        return
    print(f"\n=== {name} ===")
    for entry in concepts[name]["units"]["USD"]:
        if entry["form"] != "10-K":
            continue
        days = (date.fromisoformat(entry["end"])- date.fromisoformat((entry["start"]))).days
        if days >= 350 and days <=380:
            print(f" End: {entry["end"]} ${entry["val"] / 1_000_000:,.0f}M filed {entry["filed"]}  fy {entry["fy"]}")
                        


cik = get_cik_for_ticker("MU")
url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
headers = {"User-Agent": "Ishita ishitajain2931@gmail.com"}
concepts = httpx.get(url, headers=headers).json()["facts"]["us-gaap"]

for name in [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "CostOfGoodsAndServicesSold",
    "GrossProfit",
]:
    print_annual(concepts, name)
       
