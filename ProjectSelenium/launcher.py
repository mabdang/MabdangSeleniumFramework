import os, sys, pytest
from core.generic_keywords import GenericKeywords
from core.data_loader import DataLoader  # DataLoader generik

if __name__ == "__main__":
    # Gunakan pytest-html agar report tersimpan di folder Log/
    sys.exit(pytest.main([
        "launcher.py",      # Jalankan sendiri
        "-s", "-v",
        "--capture=tee-sys",
        "--html=reports/latest_report.html",
        "--self-contained-html"
    ]))

def test_feature(driver, run_dir, feature_name):
    """
    Eksekusi testcases untuk feature tertentu.
    File testcases dan locators bisa YAML, CSV, atau XLSX.
    """
    if not feature_name:
        pytest.skip("[SKIPPED] Argumen --feature_name wajib diisi, contoh: pytest launcher.py --feature_name=login -s")

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(BASE_DIR, "datatest", feature_name)

    # --- Load testcases dan locators pakai DataLoader ---
    try:
        testcases = DataLoader.load_testcases(folder)
    except FileNotFoundError as e:
        pytest.skip(f"[SKIPPED] {str(e)}")

    try:
        LOCATORS = DataLoader.load_locators(folder)
    except FileNotFoundError as e:
        pytest.skip(f"[SKIPPED] {str(e)}")

    # --- Validasi wajib ada keduanya ---
    if not testcases or not LOCATORS:
        pytest.skip(f"[SKIPPED] File testcases/locators tidak lengkap di {folder}")

    # --- Jalankan testcases ---
    executor = GenericKeywords(driver)
    results = []
    for testcase in testcases["test_cases"]:
        if not testcase.get("Run", True):
            print(f"[SKIPPED] {testcase['CaseID']} - {testcase['Title']}")
            results.append((testcase['CaseID'], "SKIPPED"))
            continue

        try:
            executor.execute_testcase(testcase, LOCATORS, run_dir)
            results.append((testcase['CaseID'], "PASS"))
        except Exception as e:
            print(f"[ERROR] {testcase['CaseID']} - {testcase['Title']} gagal dijalankan: {e}")
            results.append((testcase['CaseID'], "FAIL"))
        continue

    


