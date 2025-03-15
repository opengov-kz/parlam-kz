import os
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# URLs официальных страниц
SENATE_URL = "https://senate.parlam.kz/ru-RU/Deputies"
MAZHILIS_URL = "https://www.parlam.kz/ru/mazhilis/deputies"

# Архивные URL-адреса для Wayback Machine
WAYBACK_BASE = "https://web.archive.org/web/{}/{}"
ARCHIVE_DATES = ["20190101", "20200101", "20210101", "20220101", "20230101"]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def get_deputies(url):
    """Парсит страницу с депутатами."""
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Ошибка {response.status_code} при загрузке {url}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    deputies = soup.find_all("div", class_="deputy-card")
    data = []

    for deputy in deputies:
        name = deputy.find("h3").text.strip()
        position = deputy.find("p", class_="position").text.strip()
        committee = deputy.find("p", class_="committee").text.strip() if deputy.find("p",
                                                                                     class_="committee") else "Нет данных"
        data.append({"Имя": name, "Должность": position, "Комитет": committee})

    return data


def save_to_csv(data, filename):
    """Сохраняет данные в CSV."""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"Данные сохранены в {filename}")


def get_archive_data(base_url, archive_dates, filename_prefix):
    """Парсит архивные данные из Wayback Machine."""
    all_data = []

    for date in archive_dates:
        archive_url = WAYBACK_BASE.format(date, base_url)
        print(f"Парсим архивную версию: {archive_url}")
        deputies = get_deputies(archive_url)
        for deputy in deputies:
            deputy["Дата архива"] = date
        all_data.extend(deputies)
        time.sleep(2)  # Пауза между запросами, чтобы избежать блокировки

    save_to_csv(all_data, f"{filename_prefix}_archive.csv")


if __name__ == "__main__":
    # Парсим текущие данные
    senate_data = get_deputies(SENATE_URL)
    mazhilis_data = get_deputies(MAZHILIS_URL)

    # Сохраняем в CSV
    save_to_csv(senate_data, "senate_current.csv")
    save_to_csv(mazhilis_data, "mazhilis_current.csv")

    # Парсим архивные данные
    get_archive_data(SENATE_URL, ARCHIVE_DATES, "senate")
    get_archive_data(MAZHILIS_URL, ARCHIVE_DATES, "mazhilis")