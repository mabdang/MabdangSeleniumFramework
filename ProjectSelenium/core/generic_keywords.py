# core/generic_keywords.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException
from core.utils import Utils
from core.result_tracker import ResultTracker  # 🆕 UPDATE
from core.yaml_reader import YAMLReader

import os, re, pytest, ast

class GenericKeywords:
    def __init__(self, driver):
        self.driver = driver
        self.tracker = ResultTracker()  # 🆕 UPDATE: init tracker

    @staticmethod
    def parse_locator(locator_type, locator_value):
        mapping = {
            "id": By.ID,
            "name": By.NAME,
            "xpath": By.XPATH,
            "css": By.CSS_SELECTOR,
            "link_text": By.LINK_TEXT,
            "partial_link_text": By.PARTIAL_LINK_TEXT
        }
        return mapping[locator_type.lower()], locator_value

    # ================== ACTIONS ==================
    def navigate(self, url):
        print(f"[ACTION] Navigate to {url}")  # 🆕 LOG
        self.driver.get(url)

    def click(self, locator, timeout, run_dir=None, step_title=None, step_desc=None):
        print(f"[ACTION] Click on {locator}")  # 🆕 LOG
        locator_type, locator_value = self.parse_locator(*locator)
        WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((locator_type, locator_value))
        ).click()
        return Utils.capture_screenshot(self.driver, run_dir, step_title, step_desc)  # 🆕 UPDATE

    def type(self, locator, text, timeout, run_dir=None, step_title=None, step_desc=None):
        print(f"[ACTION] Type '{text}' into {locator}")  # 🆕 LOG
        locator_type, locator_value = self.parse_locator(*locator)
        elem = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((locator_type, locator_value))
        )
        elem.clear()
        elem.send_keys(text)
        return Utils.capture_screenshot(self.driver, run_dir, step_title, step_desc)  # 🆕 UPDATE

    def assert_text(self, locator, expected_text, timeout, run_dir=None, step_title=None, step_desc=None):
        print(f"[ACTION] Assert text '{expected_text}' on {locator}")  # 🆕 LOG
        locator_type, locator_value = self.parse_locator(*locator)
        elem = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((locator_type, locator_value))
        )
        actual = elem.text
        assert actual == expected_text, f"Expected {expected_text}, got {actual}"
        return Utils.capture_screenshot(self.driver, run_dir, step_title, step_desc)  # 🆕 UPDATE

    def select_by_value(self, locator, value, timeout, run_dir=None, step_title=None, step_desc=None):
        print(f"[ACTION] Select '{value}' in {locator}")  # 🆕 LOG
        locator_type, locator_value = self.parse_locator(*locator)
        elem = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((locator_type, locator_value))
        )
        select = Select(elem)
        try:
            select.select_by_value(value)
        except NoSuchElementException:
            select.select_by_visible_text(value)
        return Utils.capture_screenshot(self.driver, run_dir, step_title, step_desc)  # 🆕 UPDATE

    def hover(self, locator, timeout, run_dir=None, step_title=None, step_desc=None):
        print(f"[ACTION] Hover on {locator}")
        locator_type, locator_value = self.parse_locator(*locator)
        elem = WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((locator_type, locator_value))
        )
        ActionChains(self.driver).move_to_element(elem).perform()
        return Utils.capture_screenshot(self.driver, run_dir, step_title, step_desc)

    def js_click(self, locator, timeout, run_dir=None, step_title=None, step_desc=None):
        print(f"[ACTION] JS Click on {locator}")
        locator_type, locator_value = self.parse_locator(*locator)
        elem = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((locator_type, locator_value))
        )
        self.driver.execute_script("arguments[0].click();", elem)
        return Utils.capture_screenshot(self.driver, run_dir, step_title, step_desc)

    def drag_drop(self, source_locator, target_locator, timeout, run_dir=None, step_title=None, step_desc=None):
        print(f"[ACTION] Drag {source_locator} to {target_locator}")
        src_type, src_value = self.parse_locator(*source_locator)
        tgt_type, tgt_value = self.parse_locator(*target_locator)
        source = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((src_type, src_value))
        )
        target = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((tgt_type, tgt_value))
        )
        ActionChains(self.driver).drag_and_drop(source, target).perform()
        return Utils.capture_screenshot(self.driver, run_dir, step_title, step_desc)

    def upload_file(self, locator, file_path, timeout, run_dir=None, step_title=None, step_desc=None):
        print(f"[ACTION] Upload file {file_path} into {locator}")
        locator_type, locator_value = self.parse_locator(*locator)
        elem = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((locator_type, locator_value))
        )
        elem.send_keys(file_path)
        return Utils.capture_screenshot(self.driver, run_dir, step_title, step_desc)

    # ================== VALUE RESOLVER ==================
    def resolve_value(self, value, globaldata: dict, test_data: str = None):
        if not isinstance(value, str):
            return value
        # Replace {global.xxx}
        value = re.sub(
            r"\{global\.([a-zA-Z0-9_]+)\}",
            lambda m: str(globaldata.get(m.group(1), f"{{global.{m.group(1)}}}")),
            value
        )
        # Replace {value} placeholder
        if "{value}" in value and test_data is not None:
            value = value.replace("{value}", str(test_data))
        return value

    # ================== YAML EXECUTOR ==================
    def execute_testcase(self, testcase, LOCATORS, run_dir=None):
        case_id = testcase.get("CaseID")
        title = testcase.get("Title", "")
        scenario_type = testcase.get("ScenarioType", "")
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # 🆕 UPDATE: ambil globaldata & locator dari YAML, tanpa JSON
        globaldata = YAMLReader.read(os.path.join(BASE_DIR, "..", "datatest", "global_data.yaml"))["GlobalData"]
        globallocator = YAMLReader.read(os.path.join(BASE_DIR, "..", "datatest", "global_locators.yaml"))["GlobalLocators"]
        DefaultTimeout = globaldata.get("Timeout")

        # 🆕 UPDATE: set meta tracker langsung
        self.tracker.set_meta(
            project_name=globaldata.get("ProjectName"),
            website=globaldata.get("baseURL", ""),
            author=globaldata.get("Author"),
            tools=globaldata.get("Tools")
        )

        # 🆕 UPDATE: siapkan directory capture per testcase
        testcase_dir = os.path.join(run_dir or "reports/capture", str(testcase["Title"]))
        os.makedirs(testcase_dir, exist_ok=True)

        # 🆕 UPDATE: mulai testcase di tracker
        self.tracker.start_test_case(case_id, title, scenario_type)
        step_id = 0
        for step in testcase.get("TestSteps", []):
            action = step["Action"].lower()
            locator_name = self.resolve_value(step.get("Locator"), globallocator)
            test_data = self.resolve_value(step.get("TestData"), globaldata, step.get("TestData"))
            expected = self.resolve_value(step.get("Expected"), globaldata, test_data)
            step_title = step.get("Title", f"Step - {action}")
            step_desc = step.get("Description", "")
            step_id = step_id + 1

            locator = None
            if locator_name:
                local_dict = LOCATORS.get("locators", LOCATORS)
                local = local_dict.get(locator_name)
                if local:
                    resolved_value = self.resolve_value(local["LocatorValue"], globaldata, test_data)
                    locator = (local["LocatorType"], resolved_value)
                else:
                    resolved_global = self.resolve_value(locator_name, globallocator, test_data)
                    if isinstance(resolved_global, str):
                        resolved_global = ast.literal_eval(resolved_global)
                    locator = (resolved_global["LocatorType"], resolved_global["LocatorValue"])

            # --- execute action + capture + log status ---
            try:
                shot = None
                if action == "navigate":
                    self.navigate(test_data)
                    shot = Utils.capture_screenshot(self.driver, testcase_dir, step_title, step_desc)
                elif action == "click" and locator:
                    shot = self.click(locator, DefaultTimeout, testcase_dir, step_title, step_desc)
                elif action == "type" and locator:
                    shot = self.type(locator, test_data, DefaultTimeout, testcase_dir, step_title, step_desc)
                elif action == "select" and locator:
                    shot = self.select_by_value(locator, test_data, DefaultTimeout, testcase_dir, step_title, step_desc)
                elif action == "assert" and locator:
                    shot = self.assert_text(locator, expected, DefaultTimeout, testcase_dir, step_title, step_desc)
                elif action == "hover" and locator:
                    shot = self.hover(locator, DefaultTimeout, testcase_dir, step_title, step_desc)
                elif action == "js_click" and locator:
                    shot = self.js_click(locator, DefaultTimeout, testcase_dir, step_title, step_desc)
                elif action == "drag_drop":
                    source = locator
                    #target_name = step.get("Target")
                    target_name = test_data
                    target = None
                    if target_name:
                        tgt_local = LOCATORS.get("locators", LOCATORS).get(target_name)
                        if tgt_local:
                            target = (tgt_local["LocatorType"], self.resolve_value(tgt_local["LocatorValue"], globaldata))
                    if source and target:
                        shot = self.drag_drop(source, target, DefaultTimeout, testcase_dir, step_title, step_desc)
                elif action == "upload_file" and locator:
                    shot = self.upload_file(locator, test_data, DefaultTimeout, testcase_dir, step_title, step_desc)                
                else:
                    pytest.fail(f"[ERROR] Unknown action or missing locator: {action}")

                # 🆕 UPDATE: log capture ke tracker
                self.tracker.log_step(
                    case_id=case_id,
                    step_id=step_id,
                    step_title=step_title,
                    step_desc=step_desc,
                    image_path=(shot or {}).get("file", ""),
                    status="passed"
                )
            except Exception as e:
                try:
                    fail_shot = Utils.capture_screenshot(self.driver, testcase_dir, f"{step_title} (FAILED)", step_desc)
                    img_path = fail_shot.get("file", "")
                except Exception:
                    img_path = ""
                self.tracker.log_step(
                    case_id=case_id,
                    step_id=step_id,
                    step_title=step_title,
                    step_desc=step_desc,
                    image_path=img_path,
                    status="failed",
                    error=str(e)
                )
                pytest.fail(f"[EXCEPTION] {e}")

        # 🆕 UPDATE: finalize testcase
        self.tracker.end_test_case(case_id)
