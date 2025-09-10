import os, json
from datetime import datetime
from reports.pdf_report import generate_pdf_report
from core.result_tracker import ResultTracker


def normalize_path(path: str) -> str:
    return os.path.normpath(path) if path else ""


def collect_results(exitstatus: int = None, run_root: str = None):
    """Dipanggil di setiap worker: simpan snapshot lokal (snapshot_PID.json)."""
    tracker = ResultTracker()
    snapshot = tracker.get_snapshot()

    status_map = {
        0: "ALL PASSED",
        1: "FAILED",
        2: "INTERRUPTED",
        3: "INTERNAL ERROR",
        4: "USAGE ERROR"
    }
    snapshot["meta"]["exitstatus"] = status_map.get(exitstatus, "UNKNOWN")

    if run_root:
        worker_file = os.path.join(run_root, f"snapshot_{os.getpid()}.json")
        print(f"[DEBUG] Worker {os.getpid()} simpan snapshot: {worker_file}")
        with open(worker_file, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
    else:
        print("[WARN] collect_results tanpa run_root")

    # Normalisasi path gambar
    for case in snapshot.get("cases", []):
        for step in case.get("steps", []):
            step["image"] = normalize_path(step.get("image"))

    return snapshot


def merge_worker_snapshots(run_root):
    """Master menggabungkan semua snapshot worker, hitung ulang totals."""
    merged = {"cases": [], "meta": {}, "totals": {"passed": 0, "failed": 0, "skipped": 0}}

    for f in os.listdir(run_root):
        if f.startswith("snapshot_") and f.endswith(".json"):
            worker_path = os.path.join(run_root, f)
            try:
                with open(worker_path, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    merged["cases"].extend(data.get("cases", []))
                    merged["meta"].update(data.get("meta", {}))
                    print(f"[DEBUG] Merged snapshot file: {worker_path}")
            except Exception as e:
                print(f"[WARN] Gagal baca snapshot {worker_path}: {e}")

    # === hitung ulang totals dari semua cases ===
    for case in merged["cases"]:
        for step in case.get("steps", []):
            status = step.get("status", "").lower()
            if status == "passed":
                merged["totals"]["passed"] += 1
            elif status == "failed":
                merged["totals"]["failed"] += 1
            elif status == "skipped":
                merged["totals"]["skipped"] += 1

    return merged


def generate_report(exitstatus: int = None, run_root: str = None):
    """Dipanggil sekali oleh master untuk merge dan generate PDF."""
    if run_root and os.path.isdir(run_root):
        snapshot = merge_worker_snapshots(run_root)
    else:
        snapshot = collect_results(exitstatus, run_root)

    if not snapshot or not snapshot.get("cases"):
        print("[WARN] Snapshot kosong, PDF tidak dibuat.")
        return

    output_dir = os.path.join("reports", "pdf")
    os.makedirs(output_dir, exist_ok=True)
    output_pdf = os.path.join(output_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

    try:
        generate_pdf_report(output_pdf, snapshot)
        print(f"[INFO] PDF report generated: {output_pdf}")
    except Exception as e:
        print(f"[ERROR] Gagal generate PDF: {e}")

    # Debug print hasil case
    for c in snapshot.get("cases", []):
        print(f"[CASE] {c['title']} ({c['case_id']} - {c['scenario_type']})")
        for s in c.get("steps", []):
            print(f"    [STEP] {s['step_id']}: {s['title']} - Status: {s['status']} - Image: {s.get('image','N/A')}")
