from server.graph import synthesis_node

FUND_MU = (
    "Per the FY2026 10-K, revenue was $133,188M vs $37,378M in FY2025. "
    "Cost of goods sold was $25,684M and gross profit $107,504M. "
    "Growth was driven by DRAM and NAND price increases."
)
QUANT_MU = "YoY revenue growth: 256.33% (FY2026 $133,188M vs FY2025 $37,378M)."
QUANT_CONTRADICT = "YoY revenue growth: 33.77% (FY2026 $50,000M vs FY2025 $37,378M)."

def run(rag, quant):
    state = {"ticker": "MU", "query": "revenue growth",
             "rag_result": rag, "quant_result": quant}
    report = synthesis_node(state)["final_report"]
    print(f"  confidence={report.confidence} | reason={report.confidence_reason}")
    print(f"  caveats={report.caveats}")
    return report

print("1. Agree")
r = run(FUND_MU, QUANT_MU)
assert r.confidence != "low", "matching sources should not be low"

print("2. Contradict")
r = run(FUND_MU, QUANT_CONTRADICT)
assert r.confidence!="high", "a direct contradiction must not be high"
caveats_text = " ".join(r.caveats)
assert "50,000" in caveats_text, "the mismatch should be named in the caveats"

print("3. Missing quant")
r = run(FUND_MU, None)
assert r.confidence== "low"
assert "Confidence limited" in r.confidence_reason, "reason should explain what was missing"

print("4. Unusual but consistent")
r = run(FUND_MU, QUANT_MU)
caveats_text = " ".join(r.caveats).lower()
assert "extraction" not in caveats_text, "large growth should not be flagged as a data error"

print("All 4 passed")