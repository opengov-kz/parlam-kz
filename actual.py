import os
import csv
import asyncio
import aiohttp
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm

# Папки для сохранения данных
DATA_DIR = 'data'
DOCS_DIR = os.path.join(DATA_DIR, 'documents')

os.makedirs(DOCS_DIR, exist_ok=True)

# Только один сайт пока
BASE_URL = 'https://parlam.kz/'

# Расширения документов
DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']

pages_data = []
documents_links = []

visited_urls = set()

def is_valid_url(url):
    return url.startswith('http')

def is_document(url):
    return any(url.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS)

def scrape_site(start_url):
    queue = [start_url]

    while queue:
        current_url = queue.pop(0)
        if current_url in visited_urls:
            continue

        try:
            response = requests.get(current_url, timeout=10, verify=False)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Ошибка при загрузке {current_url}: {e}")
            continue

        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            # Это не HTML, пропускаем
            continue

        visited_urls.add(current_url)

        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else 'No Title'

        pages_data.append({
            'url': current_url,
            'title': title
        })

        # Сканируем ссылки
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            full_url = urljoin(current_url, href)
            parsed_url = urlparse(full_url)

            full_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path

            if not is_valid_url(full_url):
                continue

            if is_document(full_url):
                documents_links.append(full_url)
            elif full_url.startswith(BASE_URL) and full_url not in visited_urls:
                queue.append(full_url)

async def download_document(session, url):
    try:
        filename = os.path.basename(urlparse(url).path)
        filepath = os.path.join(DOCS_DIR, filename)

        async with session.get(url, ssl=False) as resp:
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
    print("Начинаем сканирование сайта parlam.kz ...")
    scrape_site(BASE_URL)

    print(f"Найдено {len(pages_data)} страниц и {len(documents_links)} документов.")

    print("Сохраняем страницы в CSV...")
    save_pages_to_csv()

    print("Скачиваем документы...")
    asyncio.run(download_all_documents())

    print("Готово!")
