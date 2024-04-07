import os

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
        for chunk in response.iter_content(chunk_size=128):
            fd.write(chunk)
    print(f"{filename} downloaded successfully.")


def scrape_arxiv(categories, max_papers=2):
    """Scrape and download PDFs from arXiv for the given categories."""
    base_url = "https://arxiv.org/list/"

    for category in categories:
        url = f"{base_url}{category}/new"
        soup = make_soup(url)
        folder = f"a_files/academic_papers/{category}"
        ensure_directory_exists(folder)

        papers_downloaded = 0

        for link in soup.find_all("a", string="pdf", href=True):
            if papers_downloaded >= max_papers:
                break
            pdf_url = (
                f'https://arxiv.org{link["href"]}'
                if not link["href"].startswith("http")
                else link["href"]
            )
            filename = f'{link["href"].split("/")[-1]}.pdf'
            print(f"Downloading {filename} from {pdf_url}")
            download_pdf(pdf_url, filename, folder)
            papers_downloaded += 1


def make_soup(url):
    """Return a BeautifulSoup object for the given URL."""
    response = requests.get(url)
    return BeautifulSoup(response.text, "html.parser")


if __name__ == "__main__":
    categories = ["cs", "econ", "eess", "math", "physics", "q-bio", "q-fin", "stat"]
    scrape_arxiv(categories)
