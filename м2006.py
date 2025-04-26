import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

BASE_URL = "https://web.archive.org/web/20060918000000/http://mazhilis.parlam.kz/"
output_dir = "mazhilis_2006_archive"
visited = set()
delay = 1.0

# Расширения файлов для скачивания как "файлы" (не HTML)
FILE_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".csv", ".rtf", ".xml", ".json",
    ".zip", ".rar", ".7z", ".tar", ".gz",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
    ".css", ".js", ".woff", ".woff2", ".ttf", ".eot",
    ".mp3", ".wav", ".mp4", ".avi", ".mov", ".webm"
}

def sanitize_path(url):
    parsed = urlparse(url)
    path = parsed.path
    if path.endswith("/"):
        path += "index.html"
    elif not os.path.splitext(path)[1]:
        path += ".html"
    safe_path = path.replace(":", "_").replace("?", "_")
    return os.path.join(output_dir, safe_path.lstrip("/"))

def save_html(url, path):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(path, "w", encoding='utf-8') as f:
            f.write(response.text)
    except Exception as e:
        print(f"Ошибка при скачивании {url}: {e}")

def save_file(url, path):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(path, "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"Ошибка при скачивании файла {url}: {e}")

def should_download(full_url):
    return full_url.startswith("https://web.archive.org/web/20060918000000/http://mazhilis.parlam.kz")

def extract_links(soup, base_url):
    tags_attrs = {
        'a': 'href',
        'link': 'href',
        'script': 'src',
        'img': 'src',
        'iframe': 'src',
        'source': 'src',
    }
    links = set()
    for tag, attr in tags_attrs.items():
        for element in soup.find_all(tag):
            href = element.get(attr)
            if href:
                full_url = urljoin(base_url, href)
                if should_download(full_url):
                    links.add(full_url)
    return links

def crawl(url):
    if url in visited:
        return
    print(f"Скачиваем {url}")
    visited.add(url)

    local_path = sanitize_path(url)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    save_html(url, local_path)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Ошибка при обработке {url}: {e}")
        return

    links = extract_links(soup, url)

    for link in links:
        if link in visited:
            continue
        ext = os.path.splitext(link)[1].lower()
        file_path = sanitize_path(link)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if ext in FILE_EXTENSIONS:
            save_file(link, file_path)
        else:
            crawl(link)
            time.sleep(delay)

if __name__ == "__main__":
    os.makedirs(output_dir, exist_ok=True)
    crawl(BASE_URL)
    print("Загрузка завершена.")
