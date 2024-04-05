import os

import requests
from bs4 import BeautifulSoup


def get_song_lyrics(base_url, periods, songLyrics_folder):
    # Ensure the song lyrics directory exists
    os.makedirs(songLyrics_folder, exist_ok=True)

    for period in periods:
        year, month = period
        url = base_url.format(month, year)
        soup = make_soup(url)

        links_div = soup.find("div", {"data-lyrics-container": "true"})
        if links_div:
            for link in links_div.find_all("a"):
                artist_name, song_name = get_artist_and_song_name(link)
                lyrics = get_lyrics(link.get("href"))

                if lyrics:
                    filename = create_filename(artist_name, song_name)
                    write_lyrics(
                        songLyrics_folder, filename, song_name, artist_name, lyrics
                    )


def make_soup(url):
    response = requests.get(url)
    return BeautifulSoup(response.content, "html.parser")


def get_artist_and_song_name(link):
    song_name = link.text
    artist_name = link.find_previous_sibling(text=True).split(" - ")[0]
    return artist_name, song_name


def get_lyrics(song_url):
    song_soup = make_soup(song_url)
    lyrics_div = song_soup.find("div", {"data-lyrics-container": "true"})
    return lyrics_div.text.strip() if lyrics_div else None


def create_filename(artist_name, song_name):
    # Ensure the filename is valid for most file systems
    return (
        "{} by {}.md".format(song_name, artist_name)
        .replace("/", "-")
        .replace("\\", "-")
    )


def write_lyrics(folder, filename, song_name, artist_name, lyrics):
    filepath = os.path.join(folder, filename)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(f"{song_name} by {artist_name}\n\n{lyrics}")


if __name__ == "__main__":
    base_url = "https://genius.com/Genius-{}-{}-singles-release-calendar-annotated"
    periods = [
        ("2024", "january"),
        ("2024", "february"),
        ("2024", "march"),
        ("2023", "july"),
        ("2023", "august"),
        ("2023", "september"),
        ("2023", "october"),
        ("2023", "november"),
        ("2023", "december"),
    ]
    songLyrics_folder = "a_files/song_lyrics"
    get_song_lyrics(base_url, periods, songLyrics_folder)

    print("Scraping complete!")
