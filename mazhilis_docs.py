import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
import pandas as pd

BASE_DOMAINS = [
    "https://mazhilis.parlam.kz/",
    "https://senate.parlam.kz/",
    "https://parlam.kz/"
]

DOC_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
IGNORED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']
visited = set()
data = []

SAVE_DIR = "downloaded"
os.makedirs(SAVE_DIR, exist_ok=True)

def is_valid_link(href, domain):
    if not href:
        return False
    href = href.split('#')[0]
    if any(href.lower().endswith(ext) for ext in IGNORED_EXTENSIONS):
        return False
    return href.startswith(domain) or href.startswith('/')

def save_file(url, content, file_path):
    with open(file_path, 'wb') as f:
        f.write(content)

def download_file(url):
    local_filename = urlparse(url).path.split('/')[-1]
    save_path = os.path.join(SAVE_DIR, local_filename)
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            save_file(url, r.content, save_path)
            return save_path
    except Exception as e:
        print(f"❌ Не удалось скачать {url}: {e}")
    return None

def crawl(url, base_domain):
    if url in visited or any(ext in url.lower() for ext in IGNORED_EXTENSIONS):
        return
    visited.add(url)
    try:
        r = requests.get(url, timeout=10)
    except Exception as e:
        print(f"⛔ Ошибка загрузки {url}: {e}")
        return

    if r.status_code != 200:
        return

    parsed_url = urlparse(url)
    ext = os.path.splitext(parsed_url.path)[1]

    if ext.lower() in DOC_EXTENSIONS:
        file_path = download_file(url)
        if file_path:
            data.append({"url": url, "type": "document", "local_path": file_path})
        return

    # Сохраняем HTML
    filename = parsed_url.path.strip('/').replace('/', '_') or 'index'
    if not filename.endswith('.html'):
        filename += '.html'
    file_path = os.path.join(SAVE_DIR, filename)
    with open(file_path, 'wb') as f:
        f.write(r.content)
    data.append({"url": url, "type": "html", "local_path": file_path})

    soup = BeautifulSoup(r.text, 'html.parser')
    links = [urljoin(url, a.get('href')) for a in soup.find_all('a', href=True)]
    for link in links:
        if is_valid_link(link, base_domain):
            crawl(link, base_domain)

# 🔄 Запуск
for domain in BASE_DOMAINS:
    print(f"🔎 Начинаем обход: {domain}")
    crawl(domain, domain)

# 💾 Сохраняем в CSV
df = pd.DataFrame(data)
df.to_csv("parlam_documents.csv", index=False)
print(f"\n✅ Всего файлов: {len(data)}\n📄 CSV сохранён: parlam_documents.csv")
