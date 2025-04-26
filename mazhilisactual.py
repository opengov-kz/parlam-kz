import os
import asyncio
import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# Папки
DATA_DIR = 'data_mazhilis'
DOCS_DIR = os.path.join(DATA_DIR, 'documents')

os.makedirs(DOCS_DIR, exist_ok=True)

# Базовая страница
BASE_URL = 'https://mazhilis.parlam.kz/'

# Документы
DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']

pages_data = []
documents_links = []
visited_urls = set()

def start_browser():
    options = Options()
    # Видимый браузер
    # options.add_argument("--headless")  # отключено для видимости
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(5)
    return driver

def click_and_scrape_site(start_url):
    driver = start_browser()
    driver.get(start_url)

    try:
        print("Ищем кнопку 'Құжаттар'...")
        # Кликаем на пункт меню "Құжаттар"
        doc_button = driver.find_element(By.LINK_TEXT, "Құжаттар")
        doc_button.click()
        print("Кликнули на 'Құжаттар'!")
        time.sleep(3)  # подождать загрузку новой страницы
    except Exception as e:
        print(f"Не удалось найти или кликнуть на 'Құжаттар': {e}")
        driver.quit()
        return

    queue = [driver.current_url]

    while queue:
        current_url = queue.pop(0)
        if current_url in visited_urls:
            continue

        try:
            driver.get(current_url)
            time.sleep(2)
            page_source = driver.page_source
        except Exception as e:
            print(f"Ошибка при загрузке {current_url}: {e}")
            continue

        visited_urls.add(current_url)

        soup = BeautifulSoup(page_source, 'html.parser')
        title = soup.title.string.strip() if soup.title else 'No Title'

        pages_data.append({
            'url': current_url,
            'title': title
        })

        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href'].strip()
            if href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
                continue

            full_url = urljoin(current_url, href)
            parsed_url = urlparse(full_url)
            full_url = parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path

            if not is_valid_url(full_url):
                continue

            if is_document(full_url):
                if full_url not in documents_links:
                    documents_links.append(full_url)
            elif full_url.startswith(BASE_URL) and full_url not in visited_urls:
                queue.append(full_url)

    driver.quit()

def is_valid_url(url):
    return url.startswith('http')

def is_document(url):
    return any(url.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS)

async def download_document(session, url):
    try:
        filename = os.path.basename(urlparse(url).path)
        filepath = os.path.join(DOCS_DIR, filename)

        async with session.get(url) as resp:
            if resp.status == 200:
                with open(filepath, 'wb') as f:
                    f.write(await resp.read())
    except Exception as e:
        print(f"Ошибка при скачивании {url}: {e}")

async def download_all_documents():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in tqdm(documents_links, desc="Скачивание документов"):
            tasks.append(download_document(session, url))
        await asyncio.gather(*tasks)

def save_pages_to_csv():
    df = pd.DataFrame(pages_data)
    df.to_csv(os.path.join(DATA_DIR, 'pages_data.csv'), index=False, encoding='utf-8-sig')

if __name__ == '__main__':
    print("Начинаем сканирование сайта mazhilis.parlam.kz через Selenium...")
    click_and_scrape_site(BASE_URL)

    print(f"Найдено {len(pages_data)} страниц и {len(documents_links)} документов.")

    print("Сохраняем страницы в CSV...")
    save_pages_to_csv()

    print("Скачиваем документы...")
    asyncio.run(download_all_documents())

    print("Готово!")
