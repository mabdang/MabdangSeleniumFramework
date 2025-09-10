import pytest, os, datetime, webbrowser   # [UPDATE-1] tambah import webbrowser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService   # [UPDATE-2] firefox support
from selenium.webdriver.edge.service import Service as EdgeService         # [UPDATE-3] edge support
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager                   # [UPDATE-4]
from webdriver_manager.microsoft import EdgeChromiumDriverManager          # [UPDATE-5]
from core.yaml_reader import YAMLReader

RUN_ROOT_KEY = pytest.StashKey[str]()   # [FIX] stash key buat run_root

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


# ============================================================
# Selenium Driver
# ==========================================================
@pytest.fixture
def driver():
    # [UPDATE-6] Deteksi browser default user    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    globaldata = YAMLReader.read(os.path.join(BASE_DIR, "datatest", "global_data.yaml"))["GlobalData"]
    config_browser = globaldata.get("Browser", "").lower()
    try:
        default_browser = webbrowser.get().name.lower()
    except Exception:
        default_browser = ""
    if config_browser:
        default_browser = config_browser
    print(f"[INFO] Default browser terdeteksi: {default_browser}")

    headless = globaldata.get("Headless")
    base_url = globaldata.get("baseURL")

    driver = None
    print(f"[INFO] Menggunakan Headless: {headless}")

    if "chrome" in default_browser:
        service = ChromeService(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
            options.add_argument(f"--window-size={globaldata.get('WindowSize','1920,1080')}")
        else:
            options.add_argument("--start-maximized")
        driver = webdriver.Chrome(service=service, options=options)
        print("[INFO] Menggunakan Chrome WebDriver")

    elif "firefox" in default_browser or "mozilla" in default_browser:
        service = FirefoxService(GeckoDriverManager().install())
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument("--headless")
            w, h = globaldata.get("WindowSize","1920,1080").split(",")
            options.add_argument(f"--width={w}")
            options.add_argument(f"--height={h}")
        else:
            options.add_argument("--width=1920")
            options.add_argument("--height=1080")
        driver = webdriver.Firefox(service=service, options=options)
        print("[INFO] Menggunakan Firefox WebDriver")

    elif "edge" in default_browser:
        service = EdgeService(EdgeChromiumDriverManager().install())
        options = webdriver.EdgeOptions()
        if headless:
            options.add_argument("--headless=new")
        else:
            options.add_argument("--start-maximized")
        driver = webdriver.Edge(service=service, options=options)
        
        print("[INFO] Menggunakan Edge WebDriver")

    else:
        # [UPDATE-7] fallback ke Chrome jika browser tidak dikenali
        print("[WARNING] Browser default tidak dikenali, fallback ke Chrome")
        service = ChromeService(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(service=service, options=options)

    # --- setting umum ---
    driver.implicitly_wait(globaldata.get("Timeout"))

    # --- navigate ke baseURL dari config ---
    driver.get(base_url)
    print(f"[INFO] Navigasi ke {base_url}")

    # --- assert basic cek ---
    assert base_url.split("//")[1].split("/")[0] in driver.current_url, \
        f"[ERROR] Base URL salah, expected {base_url}, got {driver.current_url}"
    
    yield driver   # ini yang dikembalikan ke test

    # Teardown
    driver.quit()

# ============================================================
# Fixture: run_dir (Single Folder untuk semua worker)
# ============================================================
@pytest.fixture(scope="session")
def run_dir(request):
    """
    Fixture yang dikonsumsi test.
    Hanya return run_root yang sudah dibuat di pytest_configure.
    """
    run_root = request.config.stash.get(RUN_ROOT_KEY, None)
    if not run_root:
        raise RuntimeError("run_root belum dibuat oleh pytest_configure!")
    print(f"[INFO] Semua output run akan disimpan di: {run_root}")
    return run_root
# ============================================================
# Single run_root (master membuat, worker memakai)
# ============================================================
def pytest_configure(config):
    """
    Dipanggil pada semua proses pytest (master dan worker).
    - Jika master (tidak ada config.workerinput) => buat run_root dan simpan di config._store
    - Jika worker => baca run_root dari config.workerinput dan simpan ke config._store
    """
    # Worker proses: ambil run_root dari workerinput (set oleh pytest_configure_node)
    if not hasattr(config, "workerinput"):  # Master only
        project_root = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(project_root, "reports", "capture")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_root = os.path.join(reports_dir, f"run_{timestamp}")
        os.makedirs(run_root, exist_ok=True)

        config._store[RUN_ROOT_KEY] = run_root
        print(f"[DEBUG] (master) created run_root: {run_root}")
    else:
        run_root = config.workerinput.get("run_root")
        if run_root:
            config._store[RUN_ROOT_KEY] = run_root
            print(f"[DEBUG] (worker) using run_root: {run_root}")


def pytest_configure_node(node):
    """
    Dipanggil di master untuk setiap worker node yang dibuat.
    Kita share run_root (master) -> node.workerinput sehingga worker tahu folder yang sama.
    """
    run_root = node.config._store.get(RUN_ROOT_KEY, None)
    if run_root:
        node.workerinput["run_root"] = run_root
        print(f"[DEBUG] (node) sharing run_root to worker: {run_root}")     

# ============================================================
# Save snapshot from worker after each test (teardown)
# ============================================================
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_teardown(item, nextitem):
    """
    Setelah tiap test teardown:
    - Worker menyimpan snapshot ke run_root dengan nama snapshot_<pid>.json
    - Kita panggil report_generator.collect_results(run_root=...)
    """
    outcome = yield

    # Pastikan run_root ada dan kita di worker
    run_root = item.config._store.get(RUN_ROOT_KEY, None)
    # juga coba dari workerinput (backward)

    if run_root and hasattr(item.config, "workerinput"):
        # hanya jalankan di worker
        from reports import report_generator
        try:
            report_generator.collect_results(exitstatus=None, run_root=run_root)
        except Exception as e:
            print(f"[ERROR] collect_results gagal di worker: {e}")

# ============================================================
# Master: merge + generate PDF saat session selesai
# ============================================================
def pytest_sessionfinish(session, exitstatus):
    """Hanya dijalankan di master (tidak di worker)."""
    if hasattr(session.config, "workerinput"):
        # worker; abaikan
        return

    run_root = session.config._store.get(RUN_ROOT_KEY, None)
    if not run_root:
        print("[WARN] Tidak ada run_root di pytest_sessionfinish; tidak generate report.")
        return

    print(f"[DEBUG] Master akan merge snapshot dari: {run_root}")
    # debug listing folder sebelum merge
    try:
        files = os.listdir(run_root)
        print(f"[DEBUG] run_root listing ({run_root}) -> {len(files)} entries:")
        for f in files:
            full = os.path.join(run_root, f)
            try:
                size = os.path.getsize(full)
            except OSError:
                size = "n/a"
            print(f"    - {f}  (size={size})")
    except Exception as e:
        print(f"[WARN] Gagal listing run_root: {e}")

    # panggil generator
    import reports.report_generator as report_gen
    report_gen.generate_report(exitstatus=exitstatus, run_root=run_root)
    print("[DEBUG] generate_report dipanggil oleh master.")


