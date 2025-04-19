from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import shutil
import time
import os


BUSQUEDA_BTN_CLS = 'search-button'
EXPORTAR_BTN_ID = 'AJS_DROPDOWN__81'
CSV_CAMPOS_ACTUALES_XPATH = '//*[@id="currentCsvFields"]'
EXPORTAR_POPUP = '<button id="csv-export-dialog-export-button" class="aui-button aui-button-primary" resolved="">Exportar</button>'
GOOGLE_DATA = "C:/Users/A200388696/AppData/Local/Google/Chrome/User Data/Default"


def download_csv():
    chrome_options = Options()
    chrome_options.add_argument(F"user-data-dir={GOOGLE_DATA}")
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=chrome_options)

    driver.get('https://setools.t-systems.es/jira/issues/?filter=33457120')

    elem = driver.find_element(By.CLASS_NAME, BUSQUEDA_BTN_CLS)
    elem.click()

    exportar_elem = driver.find_element(By.ID, EXPORTAR_BTN_ID)
    exportar_elem.click()

    wait = WebDriverWait(driver, 10)
    campos_actuales = wait.until(EC.presence_of_element_located((By.XPATH, CSV_CAMPOS_ACTUALES_XPATH)))
    # campos_actuales = driver.find_element(By.XPATH, CSV_CAMPOS_ACTUALES_XPATH)
    campos_actuales.click()

    exportar_popup = driver.find_element(By.ID, 'csv-export-dialog-export-button')
    exportar_popup.click()

    time.sleep(10)

    driver.quit()

    logger.info("Finished execution of 'download_csv.py'")

def move_csv():
    download_dir = r'C:\Users\A200388696\Downloads'
    target_dir = r'C:\Users\A200388696\Deutsche Telekom AG\AM09 - DATA Recerca i Universitats - Documentos\General\30_Seguimientos\Daily\REU_daily\data'
    prefix = 'REU - SEMANAL'

    # Get all matching files
    matching_files = [
        os.path.join(download_dir, f)
        for f in os.listdir(download_dir)
        if f.startswith(prefix) and os.path.isfile(os.path.join(download_dir, f))
    ]

    # Get the most recently modified one
    if matching_files:
        # Delete all files
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)  # Delete file or link
                    logger.warning(f"Deleting {item_path}")
            except Exception as e:
                logger.error(f"Error deleting {item_path}: {e}")

        latest_file = max(matching_files, key=os.path.getmtime)
        destination = os.path.join(target_dir, os.path.basename(latest_file))
        shutil.move(latest_file, destination)
        logger.info(f"Moved {latest_file} → {destination}")
    else:
        logger.info("No matching files found.")


if __name__ == "__main__":
    download_csv()
    move_csv()