import os
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

BASE_URL = "https://web.archive.org/web/20200505000000/http://www.parlam.kz/"
WAYBACK_PREFIX = "https://web.archive.org"

SAVE_DOCS = "parlam_2020_files"
VISITED_FILE = "visited_2020.json"
MAX_PAGES_PER_RUN = 100
SLEEP_DELAY = 1.0

DOCUMENT_EXTENSIONS = [
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".rtf", ".zip", ".rar", ".7z", ".txt", ".csv"
]
IGNORED_EXTENSIONS = [
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico", ".css", ".js"
]

os.makedirs(SAVE_DOCS, exist_ok=True)

def is_document(url):
    return any(url.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS)

def is_ignored(url):
    return any(url.lower().endswith(ext) for ext in IGNORED_EXTENSIONS)

def download_file(url):
    try:
        filename = os.path.basename(urlparse(url).path)
        if not filename or '.' not in filename:
            return
        path = os.path.join(SAVE_DOCS, filename)
        if os.path.exists(path):
            return
        response = requests.get(url, stream=True, timeout=15)
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Файл сохранён: {filename}")
    except Exception as e:
        print(f"Ошибка при скачивании {url}: {e}")

def fetch_html(url):
    try:
        response = requests.get(url, timeout=15)
        return response.text
    except Exception as e:
        print(f"Ошибка при получении страницы {url}: {e}")
        return None

def crawl(start_url):
    visited = set()
    to_visit = [start_url]
    docs = 0
    pages = 0

    if os.path.exists(VISITED_FILE):
        with open(VISITED_FILE, "r") as f:
            visited = set(json.load(f))

    while to_visit and pages < MAX_PAGES_PER_RUN:
        current = to_visit.pop(0)
        if current in visited or not current.startswith(WAYBACK_PREFIX):
            continue
        visited.add(current)
        print(f"Обработка: {current}")
        html = fetch_html(current)
        if not html:
            continue
        pages += 1
        time.sleep(SLEEP_DELAY)

        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(current, href)

            if is_ignored(full_url):
                continue
            if is_document(full_url):
                download_file(full_url)
                docs += 1
            elif "parlam.kz" in full_url and full_url.startswith(WAYBACK_PREFIX):
                if full_url not in visited and full_url not in to_visit:
                    to_visit.append(full_url)

    with open(VISITED_FILE, "w") as f:
        json.dump(list(visited), f)

    print(f"\nГотово: обработано {pages} страниц, скачано {docs} файлов.")
    print("Запусти скрипт снова, чтобы продолжить обход.")

if __name__ == "__main__":
    crawl(BASE_URL)
