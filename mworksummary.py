import os
import time
import csv
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Папка для сохранения
SAVE_DIR = 'mazhilis_documents'
os.makedirs(SAVE_DIR, exist_ok=True)

# Настройки Selenium
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

# Запуск браузера
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 20)

# Главная страница
BASE_URL = 'https://mazhilis.parlam.kz/kk'

def download_file(url, path):
    try:
        response = requests.get(url, timeout=30, verify=False)
        response.raise_for_status()
        with open(path, 'wb') as f:
            f.write(response.content)
        print(f"Скачан: {path}")
    except Exception as e:
        print(f"Ошибка при скачивании {url}: {e}")

def scrape_mazhilis():
    driver.get(BASE_URL)
    time.sleep(3)

    # Собираем все ссылки сайта
    all_links = set()
    elems = driver.find_elements(By.TAG_NAME, "a")
    for elem in elems:
        href = elem.get_attribute("href")
        if href and href.startswith("https://mazhilis.parlam.kz/kk"):
            all_links.add(href.split('#')[0])  # убираем якоря

    print(f"Найдено {len(all_links)} уникальных ссылок")

    # Список для CSV
    csv_data = []

    for link in sorted(all_links):
        try:
            print(f"\nОбрабатываем страницу: {link}")
            driver.get(link)
            time.sleep(2)

            # Сохраняем html страницы
            page_source = driver.page_source
            page_filename = os.path.join(SAVE_DIR, link.replace('https://mazhilis.parlam.kz/kk/', '').replace('/', '_') + '.html')
            with open(page_filename, 'w', encoding='utf-8') as f:
                f.write(page_source)

            # Ищем документы
            docs = driver.find_elements(By.CSS_SELECTOR, "a[href$='.pdf'], a[href$='.doc'], a[href$='.docx']")

            print(f"Найдено документов для скачивания: {len(docs)}")

            for doc in docs:
                file_url = doc.get_attribute("href")
                if not file_url:
                    continue
                filename = os.path.basename(file_url.split('?')[0])
                save_path = os.path.join(SAVE_DIR, filename)
                download_file(file_url, save_path)

                csv_data.append({
                    'page_url': link,
                    'file_name': filename,
                    'file_url': file_url
                })

        except Exception as e:
            print(f"Ошибка обработки страницы {link}: {e}")

    # Сохраняем CSV с данными
    csv_path = os.path.join(SAVE_DIR, 'documents_data.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['page_url', 'file_name', 'file_url'])
        writer.writeheader()
        writer.writerows(csv_data)

    print(f"\nДанные сохранены в {csv_path}")

if __name__ == "__main__":
    scrape_mazhilis()
    driver.quit()
