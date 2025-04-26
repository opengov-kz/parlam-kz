import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm

#   Ссылка на архив 2012 года
BASE_URL = "https://web.archive.org/web/20100422000000/http://mazhilis.parlam.kz/"
WAYBACK_PREFIX = "https://web.archive.org"

# Папки для сохранения
SAVE_HTML = "saved_2010/html"
SAVE_DOCS = "saved_2010/docs"
os.makedirs(SAVE_HTML, exist_ok=True)
os.makedirs(SAVE_DOCS, exist_ok=True)

# Целевые документы
DOCUMENT_EXTENSIONS = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".rtf", ".zip", ".rar", ".7z", ".txt"]
IGNORED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico", ".css", ".js"]

def is_document(url):
    return any(url.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS)

def is_ignored(url):
    return any(url.lower().endswith(ext) for ext in IGNORED_EXTENSIONS)

def download_file(url, folder):
    try:
        filename = os.path.basename(urlparse(url).path)
        if not filename or '.' not in filename:
            return
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            return
        r = requests.get(url, stream=True, timeout=15)
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Скачан файл: {filename}")
    except Exception as e:
        print(f"Ошибка скачивания файла {url}: {e}")

def download_html(url):
    try:
        filename = url.replace("/", "_").replace(":", "").replace("?", "")[-100:]
        path = os.path.join(SAVE_HTML, filename + ".html")
        if os.path.exists(path):
            return None
        r = requests.get(url, timeout=15)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(r.text)
        print(f"Скачана страница: {url}")
        return r.text
    except Exception as e:
        print(f"Ошибка HTML: {url} — {e}")
        return None

def crawl(start_url, sleep_delay=1.0):
    visited = set()
    to_visit = [start_url]
    pages = 0
    docs = 0

    while to_visit:
        current = to_visit.pop()
        if current in visited or not current.startswith(WAYBACK_PREFIX):
            continue
        visited.add(current)

        print(f" Обработка: {current}")
        html = download_html(current)
        if not html:
            continue
        pages += 1
        time.sleep(sleep_delay)

        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(current, href)

            if is_ignored(full_url):
                continue
            if is_document(full_url):
                download_file(full_url, SAVE_DOCS)
                docs += 1
            elif "parlam.kz" in full_url and full_url not in visited and full_url.startswith(WAYBACK_PREFIX):
                to_visit.append(full_url)

    print(f"\nГотово: скачано {pages} страниц и {docs} документов")

#  Запуск
if __name__ == "__main__":
    crawl(BASE_URL)
