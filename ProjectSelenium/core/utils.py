# core/utils.py
from selenium.webdriver.common.by import By
import os
from datetime import datetime
import random

class Utils:

    @staticmethod
    def capture_screenshot(driver, capture_dir, step_title=None, step_desc=None, case_id=None):  # 🆕 UPDATE
        """
        Ambil screenshot halaman saat ini dengan format nama:
        <project_name>_YYYY-MM-DD_HH-MM-SS_<random_number>.png
        Return dict {title, desc, file, case_id} untuk PDF
        """
        project_name = "ProjectSelenium"
        os.makedirs(capture_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        rand_num = random.randint(1000, 9999)
        filename = f"{project_name}_{timestamp}_{rand_num}.png"
        path = os.path.join(capture_dir, filename)

        driver.save_screenshot(path)

        return {
            "title": step_title or "Untitled Step",  # 🆕 UPDATE
            "desc": step_desc or "",                 # 🆕 UPDATE
            "file": path,                             # 🆕 UPDATE
            "case_id": case_id or ""                  # 🆕 UPDATE
        }

    @staticmethod
    def delete_all_cookies(driver):
        driver.delete_all_cookies()
