import pytest, os, datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from reports.report_generator import generate_report

def pytest_addoption(parser):
    """
    Tambahin opsi custom ke pytest.
    Contoh: pytest launcher.py --feature_name=login -s
    """
    parser.addoption(
        "--feature_name",
        action="store",
        default=None,
        help="Nama feature yang akan dijalankan (misalnya: login, request, leave, dll.)"
    )


@pytest.fixture
def feature_name(request):
    """
    Fixture untuk ambil nilai feature_name dari CLI.
    """
    return request.config.getoption("--feature_name")


@pytest.fixture
def driver():
    # Setup
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=options)
    
    yield driver   # ini yang dikembalikan ke test

    # Teardown
    driver.quit()

@pytest.fixture(scope="session")
def run_dir(request):
    """Buat folder baru untuk setiap run"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(project_root, "reports", "capture")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_root = os.path.join(reports_dir, f"run_{timestamp}")
    os.makedirs(run_root, exist_ok=True)

    request.config._store["run_root"] = run_root
    print(f"[INFO] Semua output run akan disimpan di: {run_root}")
    return run_root

def pytest_sessionfinish(session, exitstatus):
    """Generate PDF setelah semua test selesai"""
    run_root = session.config._store.get("run_root", None)
    if run_root:
        generate_report(run_root)
        print(f"[INFO] PDF report generated from run_root: {run_root}")