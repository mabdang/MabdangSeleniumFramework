import csv
from collections import defaultdict

class CSVReader:
    @staticmethod
    def read_testcases(filepath):
        cases = defaultdict(lambda: {"TestSteps": []})
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row["CaseID"].strip()
                case = cases[cid]

                # --- Case-level data ---
                case["CaseID"] = cid
                case["CaseTitle"] = row.get("CaseTitle", "").strip()
                case["Title"] = case["CaseTitle"]  # ✅ alias supaya kode lama gak error
                case["ScenarioType"] = row.get("ScenarioType", "").strip()
                case["Run"] = row.get("Run", "").strip().lower() in ("true", "1", "yes")

                # --- Step-level data ---
                case["TestSteps"].append({
                    "StepID": str(len(case["TestSteps"]) + 1),  # auto numbering
                    "Title": row.get("StepTitle", "").strip(),
                    "Description": row.get("Description", "").strip(),
                    "Action": row.get("Action", "").strip(),
                    "Locator": row.get("Locator", "").strip(),
                    "TestData": row.get("TestData", "").strip(),
                    "Expected": row.get("Expected", "").strip(),
                })

        return {"test_cases": list(cases.values())}

    @staticmethod
    def read_locators(filepath):
        locators = {}
        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError(f"[ERROR] Header CSV kosong atau tidak terbaca di {filepath}")

            for row in reader:
                locator_name = row.get("LocatorName", "").strip()
                if not locator_name:
                    continue  # skip baris kosong / tidak ada nama

                locators[locator_name] = {
                    "LocatorType": row.get("LocatorType", "").strip(),
                    "LocatorValue": row.get("LocatorValue", "").strip(),
                    "Description": row.get("Description", "").strip(), # 🆕 pastikan ada deskripsi
                }

        result = {
            #"project_name": "ProjectSelenium",  # samakan dengan YAML
            "locators": locators
        }

        #print(f"[DEBUG] read_locators OK: {len(locators)} locator dimuat dari {filepath}")
        return result
