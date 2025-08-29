from selenium.webdriver.common.by import By
import os
from datetime import datetime
import random

class Utils:
    @staticmethod
    def parse_locator(locator_type, locator_value):
        mapping = {
            "id": By.ID,
            "name": By.NAME,
            "xpath": By.XPATH,
            "css": By.CSS_SELECTOR
        }
        return mapping[locator_type.lower()], locator_value

    @staticmethod
    def capture_screenshot(driver, capture_dir):
            """
            Ambil screenshot halaman saat ini dengan format nama:
            <project_name>_YYYY-MM-DD_HH-MM-SS_<random_number>.png
            """
            project_name="ProjectSelenium"
            # Base folder untuk capture, default ke reports/capture
            os.makedirs(capture_dir, exist_ok=True)  # pastikan folder ada


            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            rand_num = random.randint(1000, 9999)
            filename = f"{project_name}_{timestamp}_{rand_num}.png"

            path = os.path.join(capture_dir, filename)
            driver.save_screenshot(path)
            #print(f"[INFO] Screenshot saved: {path}")
            return path
    
    def delete_all_cookies(driver):
        """
        Menghapus semua cookies pada browser saat ini.
        Gunanya untuk memastikan session baru bersih sebelum menjalankan test case.
        """
        driver.delete_all_cookies()
        #print("[INFO] All browser cookies have been deleted.")

