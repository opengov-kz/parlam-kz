import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm

# Папка для сохранения
WORK_DIR = 'data_mazhilis/work_docs'
os.makedirs(WORK_DIR, exist_ok=True)

def start_browser():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def download_file(url, save_path):
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as e:
        print(f"Ошибка скачивания {url}: {e}")

def parse_work_documents():
    driver = start_browser()
    driver.get("https://mazhilis.parlam.kz/kk/activity/work")
    time.sleep(5)

    files = driver.find_elements(By.CSS_SELECTOR, 'a[href$=".pdf"], a[href$=".doc"], a[href$=".docx"]')
    print(f"Найдено документов: {len(files)}")

    for file_element in tqdm(files, desc="Скачивание документов"):
        try:
            file_url = file_element.get_attribute('href')
            filename = os.path.basename(file_url.split("?")[0])
            save_path = os.path.join(WORK_DIR, filename)
            download_file(file_url, save_path)
        except Exception as e:
            print(f"Ошибка скачивания: {e}")

    driver.quit()
    print("Скачивание завершено!")

if __name__ == "__main__":
    parse_work_documents()
