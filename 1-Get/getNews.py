import os

import requests
from bs4 import BeautifulSoup


def scrape_category_articles(base_url, categories, output_dir):
    for category in categories:
        category_url = f"{base_url}{category}"
        soup = make_soup(category_url)

        if soup:
            articles = soup.find_all("div", class_="PagePromo")
            for article in articles:
                link = article.find("a", href=True)
                if link:
                    scrape_article(link["href"], category, output_dir)
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
    response = requests.get(url)
    return (
        BeautifulSoup(response.text, "html.parser")
        if response.status_code == 200
        else None
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
            file_content = f"{title.text.strip()}\n\n"
            if authors:
                file_content += f"{authors.text.strip()}\n\n"
            file_content += "\n\n".join(
                paragraph.text for paragraph in article_body.find_all("p")
            )
            file.write(file_content)
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
