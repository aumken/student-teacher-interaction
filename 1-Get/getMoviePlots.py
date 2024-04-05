import os
import shutil

import requests
from bs4 import BeautifulSoup


def fetch_movie_plots(base_url, periods, output_dir, small_plots_dir):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(small_plots_dir, exist_ok=True)

    for year, section_ids in periods:
        for section_id in section_ids:
            url = base_url.format(year)
            soup = make_soup(url)
            section = soup.find("span", id=section_id).find_next("table")

            for row in section.find("tbody").find_all("tr"):
                cells = row.find_all("td")
                if cells:
                    link = cells[0].find("a") or cells[1].find("a")
                    if link and "href" in link.attrs:
                        movie_title = link.text.strip()
                        fetch_and_save_plot(
                            link["href"], movie_title, output_dir, small_plots_dir
                        )


def make_soup(url):
    response = requests.get(url)
    return BeautifulSoup(response.content, "html.parser")


def fetch_and_save_plot(relative_url, movie_title, output_dir, small_plots_dir):
    movie_url = f"https://en.wikipedia.org{relative_url}"
    movie_soup = make_soup(movie_url)

    try:
        plot_text = extract_plot_text(movie_soup)
        if plot_text:
            save_plot_text(plot_text, movie_title, output_dir, small_plots_dir)
    except Exception as e:
        print(f"No plot found for {movie_title}.")


def extract_plot_text(soup):
    plot_section = soup.find("span", id="Plot").find_next("p")
    plot_text = plot_section.text
    for sibling in plot_section.find_next_siblings():
        if sibling.name == "p":
            plot_text += "\n\n" + sibling.text
        elif sibling.name == "h2":
            break
    return plot_text.strip()


def save_plot_text(plot_text, movie_title, output_dir, small_plots_dir):
    final_dir = small_plots_dir if len(plot_text) < 1500 else output_dir
    filename = f"{movie_title}.md".replace("/", "-")
    file_path = os.path.join(final_dir, filename)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(f"{movie_title}\n\n{plot_text}")


if __name__ == "__main__":
    base_url = "https://en.wikipedia.org/wiki/List_of_American_films_of_{}"
    periods = [
        ("2024", ["January–March"]),
        ("2023", ["July–September", "October–December"]),
    ]
    output_dir = "a_files/movie_plots"
    small_plots_dir = "a_files/movie_plots_small"
    fetch_movie_plots(base_url, periods, output_dir, small_plots_dir)

    print("Scraping complete!")
