import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm

# 1. Начальная ссылка на архив
BASE_WAYBACK_URL = "https://web.archive.org/web/20041212122127/http://www.parlam.kz/"

# 2. Расширения нужных файлов
DOCUMENT_EXTENSIONS = [
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".rar", ".7z", ".rtf", ".txt"
]

# 3. Папка сохранения
SAVE_FOLDER = "downloaded_files"
os.makedirs(SAVE_FOLDER, exist_ok=True)

# 4. Получаем все внутренние ссылки на сайте
def get_internal_links(url):
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        links = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(url, href)
            if "web.archive.org" in full_url and "parlam.kz" in full_url:
                links.add(full_url.split("#")[0])
        return list(links)
    except Exception as e:
        print(f"Ошибка при получении ссылок: {e}")
        return []

# 5. Проверка на нужное расширение
def is_document(url):
    return any(url.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS)

# 6. Скачивание файла
def download_file(url):
    try:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        save_path = os.path.join(SAVE_FOLDER, filename)

        if not os.path.exists(save_path):
            response = requests.get(url, stream=True, timeout=15)
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✔ Скачан: {filename}")
        else:
            print(f"⏩ Уже есть: {filename}")
    except Exception as e:
        print(f"Ошибка при скачивании {url}: {e}")

# 7. Основной цикл
def crawl_and_download(start_url):
    visited = set()
    to_visit = [start_url]

    while to_visit:
        current = to_visit.pop(0)
        if current in visited:
            continue
        visited.add(current)

        print(f"🔍 Проверка страницы: {current}")
        try:
            r = requests.get(current, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")

            # Найти документы и скачать
            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = urljoin(current, href)
                if is_document(full_url):
                    download_file(full_url)

                # Добавим внутренние ссылки для обхода
                if "parlam.kz" in full_url and full_url not in visited and full_url.startswith("https://web.archive.org"):
                    to_visit.append(full_url)
        except Exception as e:
            print(f"❌ Ошибка: {e}")

# 🚀 Запуск
if __name__ == "__main__":
    crawl_and_download(BASE_WAYBACK_URL)
