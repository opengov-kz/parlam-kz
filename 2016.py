import os
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Архивная версия сайта
BASE_URL = "https://web.archive.org/web/20161110000000/http://www.parlam.kz/"
WAYBACK_PREFIX = "https://web.archive.org"

# Папки
SAVE_HTML = "saved_2016/html"
SAVE_DOCS = "saved_2016/docs"
VISITED_FILE = "visited_2016.json"
MAX_PAGES_PER_RUN = 100  # можно увеличить или уменьшить
SLEEP_DELAY = 1.0

DOCUMENT_EXTENSIONS = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".rtf", ".zip", ".rar", ".7z", ".txt", ".css"]
IGNORED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico", ".js"]

# Создание папок
os.makedirs(SAVE_HTML, exist_ok=True)
os.makedirs(SAVE_DOCS, exist_ok=True)

# Проверка, является ли ссылка документом
def is_document(url):
    return any(url.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS)

# Проверка, является ли ссылка ненужным ресурсом
def is_ignored(url):
    return any(url.lower().endswith(ext) for ext in IGNORED_EXTENSIONS)

# Загрузка HTML страницы
def download_html(url):
    try:
        filename = url.replace("/", "_").replace(":", "").replace("?", "")[-100:]
        path = os.path.join(SAVE_HTML, filename + ".html")
        if os.path.exists(path):
            return None
        r = requests.get(url, timeout=15)
        with open(path, "w", encoding="utf-8") as f:
            f.write(r.text)
        print(f"HTML сохранен: {url}")
        return r.text
    except Exception as e:
        print(f"Ошибка при загрузке HTML: {url} — {e}")
        return None

# Загрузка документа
def download_file(url):
    try:
        name = os.path.basename(urlparse(url).path)
        if not name or '.' not in name:
            return
        path = os.path.join(SAVE_DOCS, name)
        if os.path.exists(path):
            return
        r = requests.get(url, stream=True, timeout=15)
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Документ сохранен: {name}")
    except Exception as e:
        print(f"Ошибка при загрузке файла: {url} — {e}")

# Основной обход страниц
def crawl(start_url):
    visited = set()
    to_visit = [start_url]
    pages = 0
    docs = 0

    if os.path.exists(VISITED_FILE):
        with open(VISITED_FILE, "r") as f:
            visited = set(json.load(f))

    while to_visit and pages < MAX_PAGES_PER_RUN:
        current = to_visit.pop(0)
        if current in visited or not current.startswith(WAYBACK_PREFIX):
            continue
        visited.add(current)

        print(f"Обработка: {current}")
        html = download_html(current)
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

    print(f"\nГотово: скачано {pages} страниц и {docs} документов.")
    print("Повтори запуск скрипта, чтобы продолжить загрузку оставшихся страниц.")

# Запуск
if __name__ == "__main__":
    crawl(BASE_URL)
