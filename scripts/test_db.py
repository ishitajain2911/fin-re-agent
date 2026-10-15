from server.db import init_db, save_report, get_cached_report
from server.schemas import SynthesisReport

init_db()

fake = SynthesisReport(
    summary="Test summary",
    key_findings=["finding 1", "finding 2"],
    risks=["risk 1"],
    caveats=[],
    confidence="low",
    confidence_reason="Fake report for testing the database.",
)

save_report("TEST", "revenue growth", fake)

loaded = get_cached_report("TEST", "revenue growth")
print("loaded:", loaded)
print("same as saved:", loaded == fake)
print("miss:", get_cached_report("TEST", "something else"))