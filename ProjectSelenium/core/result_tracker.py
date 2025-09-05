# core/result_tracker.py
from collections import defaultdict

class ResultTracker:
    """
    Singleton sederhana untuk menyimpan hasil eksekusi:
    - per test case
    - per step (judul, deskripsi, path capture, status)
    - agregat total untuk summary
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResultTracker, cls).__new__(cls)
            cls._instance._reset()
        return cls._instance

    def _reset(self):
        # 🆕 UPDATE: default meta sekarang kosong, akan di-set dari GenericKeywords
        self.meta = {
            "project_name": None,
            "website": None,
            "author": None,
            "tools": None
        }
        self.cases = []     # list of {case_id, title, scenario_type, steps: [...]}
        self._case_index = {}  # map CaseID -> index di self.cases
        self.totals = defaultdict(int)  # passed, failed, warning, done, total

    # -------------------- Meta & Header --------------------
    def set_meta(self, project_name: str = None, website: str = None, author: str = None, tools: str = None):
        """
        🆕 UPDATE: tambahkan tools dan semua field bisa None
        """
        if project_name:
            self.meta["project_name"] = project_name
        if website:
            self.meta["website"] = website
        if author:
            self.meta["author"] = author
        if tools:
            self.meta["tools"] = tools

        # 🆕 LOG
        print(f"[TRACKER] Meta set: {self.meta}")

    # -------------------- Case Lifecycle --------------------
    def start_test_case(self, case_id: str, title: str, scenario_type: str):
        if case_id not in self._case_index:
            self._case_index[case_id] = len(self.cases)
            self.cases.append({
                "case_id": case_id,
                "title": title,
                "scenario_type": scenario_type,
                "steps": []
            })
            # 🆕 LOG
            print(f"[TRACKER] Start TestCase: {case_id} - {title} ({scenario_type})")

    def log_step(self, case_id: str, step_id, step_title: str, step_desc: str, image_path: str, status: str, error: str = ""):
        """
        🆕 UPDATE: otomatis update totals dan log console
        """
        idx = self._case_index.get(case_id)
        if idx is None:
            print(f"[TRACKER][WARN] CaseID '{case_id}' not found.")
            return

        step_record = {
            "step_id": step_id,
            "title": step_title or "Untitled Step",
            "description": step_desc or "",
            "image": image_path or "",
            "status": status,
            "error": error or ""
        }
        self.cases[idx]["steps"].append(step_record)

        # update totals
        self.totals["total"] += 1
        self.totals["done"] += 1
        if status == "passed":
            self.totals["passed"] += 1
        elif status == "failed":
            self.totals["failed"] += 1
        else:
            self.totals["warning"] += 1

        # 🆕 LOG
        print(f"[TRACKER] Logged step: Case={case_id} Step={step_id} Status={status} Image={image_path}")

    def end_test_case(self, case_id: str):
        # 🆕 placeholder kalau kelak butuh finalize per case
        print(f"[TRACKER] End TestCase: {case_id}")

    # -------------------- Snapshot for PDF --------------------
    def get_snapshot(self):
        """
        🆕 UPDATE: fungsi publik untuk langsung dipakai generate_pdf_report()
        """
        # pastikan semua field meta tidak None agar PDF generator aman
        meta_copy = {k: v or "" for k, v in self.meta.items()}
        snapshot = {
            "meta": meta_copy,
            "cases": self.cases,
            "totals": dict(self.totals)
        }

        # 🆕 LOG summary
        print(f"[TRACKER] Snapshot ready: {len(snapshot['cases'])} cases, totals={snapshot['totals']}")
        return snapshot

    def reset(self):
        """
        🆕 UPDATE: reset tracker sepenuhnya
        """
        self._reset()
        print("[TRACKER] Tracker reset.")
