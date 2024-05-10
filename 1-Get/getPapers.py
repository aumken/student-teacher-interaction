import os
from concurrent.futures import ThreadPoolExecutor

import lxml
import requests
from bs4 import BeautifulSoup


def ensure_directory_exists(folder):
    """Ensure the target folder exists, creating it if necessary."""
    os.makedirs(folder, exist_ok=True)


def download_pdf(url, filename, folder):
    """Download a PDF file and save it to the specified folder."""
    full_path = os.path.join(folder, filename)
    response = requests.get(url, stream=True)
    with open(full_path, "wb") as fd:
        for chunk in response.iter_content(chunk_size=8192):
            fd.write(chunk)
    print(f"{filename} downloaded successfully.")


def scrape_arxiv(categories, max_papers=25):
    """Scrape and download PDFs from arXiv for the given categories."""
    base_url = "https://arxiv.org/list/"
    session = requests.Session()

    with ThreadPoolExecutor() as executor:
        futures = []
        for category in categories:
            url = f"{base_url}{category}/new"
            soup = make_soup(session, url)
            folder = f"a_files/academic_papers/{category}"
            ensure_directory_exists(folder)

            for link in soup.find_all("a", string="pdf", href=True)[:max_papers]:
                pdf_url = "https://arxiv.org" + link["href"]
                filename = f'{link["href"].split("/")[-1]}.pdf'
                futures.append(executor.submit(download_pdf, pdf_url, filename, folder))

        for future in futures:
            future.result()


def make_soup(session, url):
    """Return a BeautifulSoup object for the given URL."""
    response = session.get(url)
    return BeautifulSoup(response.content, "lxml")


if __name__ == "__main__":
    categories = ["cs", "econ", "eess", "math", "physics", "q-bio", "q-fin", "stat"]
    scrape_arxiv(categories)
