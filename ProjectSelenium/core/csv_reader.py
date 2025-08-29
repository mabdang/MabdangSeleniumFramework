import csv
from collections import defaultdict

class CSVReader:
    @staticmethod
    def read_testcases(filepath):
        cases = defaultdict(lambda: {"TestSteps": []})
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row["CaseID"]
                case = cases[cid]
                case["CaseID"] = row["CaseID"]
                case["Title"] = row["Title"]
                case["ScenarioType"] = row["ScenarioType"]
                case["Run"] = row["Run"].strip().lower() in ("true","1","yes")
                case["TestSteps"].append({
                    "StepID": row["StepID"],
                    "Action": row["Action"],
                    "Locator": row.get("Locator",""),
                    "TestData": row.get("TestData",""),
                    "Expected": row.get("Expected","")
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
                    "Description": row.get("Description", "").strip(),
                }

        result = {
            #"project_name": "ProjectSelenium",  # samakan dengan YAML
            "locators": locators
        }

        #print(f"[DEBUG] read_locators OK: {len(locators)} locator dimuat dari {filepath}")
        return result


