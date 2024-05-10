import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import lxml
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def scrape_category_articles(base_url, categories, output_dir):
    with ThreadPoolExecutor() as executor:
        futures = []
        for category in categories:
            category_url = f"{base_url}{category}"
            futures.append(
                executor.submit(
                    scrape_articles_for_category, category_url, category, output_dir
                )
            )

        for future in as_completed(futures):
            future.result()


def scrape_articles_for_category(category_url, category, output_dir):
    soup = make_soup(category_url)
    if soup:
        articles = soup.find_all("div", class_="PagePromo")
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    scrape_article,
                    article.find("a", href=True)["href"],
                    category,
                    output_dir,
                )
                for article in articles
            ]
            for future in as_completed(futures):
                future.result()
    else:
        print(f"Failed to retrieve {category_url}")


def scrape_article(article_url, category, output_dir):
    soup = make_soup(article_url)
    if soup:
        title, authors, article_body = find_article_elements(soup)
        if title and article_body:
            filename = sanitize_filename(title.text) + ".md"
            save_article(filename, title, authors, article_body, category, output_dir)
        else:
            print(f"Failed to find all required elements in {article_url}")
    else:
        print(f"Failed to retrieve {article_url}")


def make_soup(url):
    retry_strategy = Retry(
        total=5,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    response = http.get(url)
    return (
        BeautifulSoup(response.content, "lxml") if response.status_code == 200 else None
    )


def find_article_elements(soup):
    title = soup.find("h1", class_="Page-headline")
    authors = soup.find("div", class_="Page-authors")
    article_body = soup.find("div", class_="RichTextStoryBody RichTextBody")
    return title, authors, article_body


def sanitize_filename(title):
    return "".join(c for c in title.strip() if c.isalnum() or c in (" ", "-")).rstrip()


def save_article(filename, title, authors, article_body, category, output_dir):
    category_path = os.path.join(output_dir, category)
    os.makedirs(category_path, exist_ok=True)
    filepath = os.path.join(category_path, filename)
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as file:
            file_content = [title.text.strip(), "\n\n"]
            if authors:
                file_content.extend([authors.text.strip(), "\n\n"])
            file_content.extend(
                [
                    "\n\n".join(
                        paragraph.text
                        for paragraph in article_body.find_all("p", recursive=False)
                    )
                ]
            )
            file.write("".join(file_content))
    else:
        print(f"Article already saved: {filename}")


if __name__ == "__main__":
    url = "https://apnews.com/"
    categories = [
        "world-news",
        "us-news",
        "politics",
        "sports",
        "entertainment",
        "business",
        "science",
        "oddities",
    ]
    output_dir = "a_files/news_articles"
    scrape_category_articles(url, categories, output_dir)
    print("Scraping complete!")
