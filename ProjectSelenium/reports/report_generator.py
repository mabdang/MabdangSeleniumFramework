# report_generator.py
import os
from datetime import datetime
from reports.pdf_report import generate_pdf_report
from core.result_tracker import ResultTracker

def collect_results(exitstatus: int = None):
    """
    Ambil snapshot langsung dari ResultTracker tanpa membaca JSON / folder.
    exitstatus: optional status global session.
    """
    tracker = ResultTracker()  # 🆕 pastikan instance sama dengan GenericKeywords
    snapshot = tracker.get_snapshot()  # 🆕 ambil semua meta, cases, totals

    # 🆕 Update exitstatus di meta
    status_map = {
        0: "ALL PASSED",
        1: "FAILED",
        2: "INTERRUPTED",
        3: "INTERNAL ERROR",
        4: "USAGE ERROR"
    }
    snapshot["meta"]["exitstatus"] = status_map.get(exitstatus, "UNKNOWN")

    # 🆕 log info
    print(f"[INFO] Collected snapshot from tracker: {len(snapshot.get('cases', []))} test case(s) found.")
    print(f"[INFO] Meta info: {snapshot.get('meta')}")

    return snapshot  # 🆕 langsung pakai snapshot

def generate_report(exitstatus: int = None):
    """
    Generate PDF report dari snapshot tracker.
    """
    snapshot = collect_results(exitstatus)

    output_dir = os.path.join("reports", "pdf")  # 🆕 default output dir
    os.makedirs(output_dir, exist_ok=True)
    output_pdf = os.path.join(output_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

    generate_pdf_report(output_pdf, snapshot)
    print(f"[INFO] PDF report generated: {output_pdf}")

    # 🆕 optional: log summary per case
    for c in snapshot.get("cases", []):
        print(f"[CASE] {c['title']} ({c['case_id']} - {c['scenario_type']})")
        for s in c.get("steps", []):
            print(f"    [STEP] {s['step_id']}: {s['title']} - Status: {s['status']} - Image: {s.get('image','N/A')}")
