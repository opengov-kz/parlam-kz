import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm

# Базовая ссылка архива 2007
BASE_URL = "https://web.archive.org/web/20070815000000/http://www.parlam.kz/"
WAYBACK_PREFIX = "https://web.archive.org"

# Папки для сохранения
SAVE_HTML = "saved_2007/html"
SAVE_DOCS = "saved_2007/docs"
os.makedirs(SAVE_HTML, exist_ok=True)
os.makedirs(SAVE_DOCS, exist_ok=True)

# Целевые типы файлов
DOCUMENT_EXTENSIONS = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".rtf", ".zip", ".rar", ".txt"]
IGNORED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico", ".css", ".js"]

# Проверка — документ ли
def is_document(url):
    return any(url.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS)

def is_ignored(url):
    return any(url.lower().endswith(ext) for ext in IGNORED_EXTENSIONS)

# Скачивание документов
def download_file(url, folder):
    try:
        name = os.path.basename(urlparse(url).path)
        if not name or '.' not in name:
            return
        path = os.path.join(folder, name)
        if os.path.exists(path):
            return
        r = requests.get(url, stream=True, timeout=15)
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"📄 Файл скачан: {name}")
    except Exception as e:
        print(f"⚠ Ошибка загрузки файла: {url} — {e}")

# Скачивание HTML-страниц
def download_html(url):
    try:
        name = url.replace("/", "_").replace(":", "").replace("?", "")
        name = name[-100:]  # ограничим длину
        path = os.path.join(SAVE_HTML, name + ".html")
        if os.path.exists(path):
            return None
        r = requests.get(url, timeout=15)
        with open(path, "w", encoding="utf-8") as f:
            f.write(r.text)
        print(f"🌐 Страница скачана: {url}")
        return r.text
    except Exception as e:
        print(f"❌ Ошибка HTML: {url} — {e}")
        return None

# Основной обход
def crawl(start_url, sleep_between_requests=1.0):
    visited = set()
    to_visit = [start_url]
    pages = 0
    docs = 0

    while to_visit:
        current = to_visit.pop()
        if current in visited or not current.startswith(WAYBACK_PREFIX):
            continue
        visited.add(current)

        print(f"🔎 Проверка страницы: {current}")
        html = download_html(current)
        if not html:
            continue
        pages += 1
        time.sleep(sleep_between_requests)

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

    print(f"\n✅ Завершено: скачано {pages} страниц и {docs} документов")

# 🚀 Старт
if __name__ == "__main__":
    crawl(BASE_URL)
