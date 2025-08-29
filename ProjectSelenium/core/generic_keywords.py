from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.utils import Utils
import os, re, pytest
from core.yaml_reader import YAMLReader



class GenericKeywords:
    def __init__(self, driver):
        self.driver = driver

    @staticmethod
    def parse_locator(locator_type, locator_value):
        mapping = {
            "id": By.ID,
            "name": By.NAME,
            "xpath": By.XPATH,
            "css": By.CSS_SELECTOR
        }
        return mapping[locator_type.lower()], locator_value

    # ================== ACTIONS ==================
    def navigate(self, url):
        print(f"[ACTION] Navigate to {url}")
        self.driver.get(url)

    def click(self, locator, timeout, run_dir=None):
        locator_type, locator_value = locator
        locator_type, locator_value = self.parse_locator(locator_type, locator_value)
        print(f"[ACTION] Click on {locator}")
        WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((locator_type, locator_value))
        ).click()
        Utils.capture_screenshot(self.driver, run_dir)

    def type(self, locator, text, timeout, run_dir=None):
        locator_type, locator_value = locator
        locator_type, locator_value = self.parse_locator(locator_type, locator_value)
        print(f"[ACTION] Type '{text}' into {locator}")
        elem = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((locator_type, locator_value))
        )
        elem.clear()
        elem.send_keys(text)
        Utils.capture_screenshot(self.driver, run_dir)

    def assert_text(self, locator, expected_text, timeout, run_dir=None):
        locator_type, locator_value = locator
        locator_type, locator_value = self.parse_locator(locator_type, locator_value)
        elem = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((locator_type, locator_value))
        )
        actual = elem.text
        print(f"[ASSERT] Expect: '{expected_text}', Actual: '{actual}'")
        assert actual == expected_text, f"Expected {expected_text}, got {actual}"
        Utils.capture_screenshot(self.driver, run_dir)
    
    def resolve_value(self, value, globaldata: dict):
        """Replace placeholder {global.xxx} dengan value dari globaldata dict"""
        if not isinstance(value, str):
            return value
        
        pattern = r"\{global\.([a-zA-Z0-9_]+)\}"
        
        def replacer(match):
            key = match.group(1)
            return str(globaldata.get(key, f"{{global.{key}}}"))  # fallback kalau key tidak ada
        
        return re.sub(pattern, replacer, value)

    # ================== YAML EXECUTOR ==================
    def execute_testcase(self, testcase, LOCATORS, run_dir=None):
        """Eksekusi semua step dari 1 test case YAML"""
        case_id = testcase.get("CaseID")
        title = testcase.get("Title", "")
        scenario_type = testcase.get("ScenarioType", "")
        print(f"\n=== Running TestCase: {case_id} - {title} ({scenario_type}) ===")
        # jalankan Initiator dulu
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        globaldata_file = os.path.join(BASE_DIR, "..", "datatest", "global_data.yaml")
        globaldata = YAMLReader.read(globaldata_file)["GlobalData"]
        DefaultTimeout = globaldata.get("Timeout")        

        
        for step in testcase["TestSteps"]:
            action = step["Action"].lower()
            locator_name = step.get("Locator")
            test_data = step.get("TestData")
            expected = step.get("Expected")
           
            #membuat folder
            testcase_dir = os.path.join(run_dir, str(testcase["Title"]))
            os.makedirs(testcase_dir, exist_ok=True)
        
            # Ambil nama locator dari step
            locator = None

            # Ambil test data dari step
            test_data = self.resolve_value(test_data, globaldata)
            #print(f"value testdata yang sudah di resolve: {test_data}")

            # Ambil locator dari step
            locator_name = self.resolve_value(locator_name, globaldata)

            # Ambil expected dari step
            expected = self.resolve_value(expected, globaldata)

            if locator_name and LOCATORS["locators"].get(locator_name):                
                l = LOCATORS["locators"].get(locator_name)
                resolved_locator_value = self.resolve_value(l["LocatorValue"], globaldata)
                locator = (l["LocatorType"], resolved_locator_value)

  
            if action == "navigate":
                self.navigate(test_data)
            elif action == "click" and locator:
                self.click(locator, DefaultTimeout, testcase_dir)
            elif action == "type" and locator:
                self.type(locator, test_data, DefaultTimeout, testcase_dir)
            elif action == "assert" and locator:
                self.assert_text(locator, expected, DefaultTimeout, testcase_dir)
            else:
                print(f"[ERROR] Unknown action or missing locator: {action} dan locatornya {locator}")
                pytest.fail(f"[ERROR] Unknown action or missing locator: {action} dan locatornya {locator}")


    