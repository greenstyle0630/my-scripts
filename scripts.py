import os
import requests
from bs4 import BeautifulSoup
import re

def scrape_scripts(link):
    folder_name = ""
    title = ""

    title_match = re.search(r'tv-show=([\w-]+)', link)
    movie_match = re.search(r'movie=([\w-]+)', link)

    if title_match:
        title = title_match.group(1).replace('-', '_').title()
        season_match = re.search(r'season=(\d+)', link)
        if season_match:
            season_number = int(season_match.group(1))
            folder_name = f"{title}_Season_{season_number}"
        else:
            folder_name = title
    elif movie_match:
        title = movie_match.group(1).replace('-', '_').title()
        folder_name = title
    else:
        print("Invalid link format. Please provide a valid TV show or movie link.")
        return

    current_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(current_dir, folder_name)
    combined_script_path = os.path.join(folder_path, f"{title}_Complete_Script.txt")

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    with requests.Session() as session:
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        if 'episode_scripts' in link:
            scrape_episodes_from_season(session, link, folder_path, title, combined_script_path)
        else:
            try:
                response = session.get(link, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                episode_links = []
                if title_match:
                    for episode in soup.find_all('a', href=re.compile(r'view_episode_scripts\.php\?tv-show=')):
                        episode_links.append(episode['href'])

                    if not episode_links:
                        print("No episode links found for this season.")
                        return

                    for episode_number, episode_url in enumerate(episode_links, 1):
                        episode_url = f"https://www.springfieldspringfield.co.uk/{episode_url}"
                        print(f"Fetching: {episode_url}")
                        scrape_episode(session, episode_url, combined_script_path, title, episode_number)

                elif movie_match:
                    scrape_episode(session, link, combined_script_path, title, None)
                else:
                    print("No scripts found: the show or movie may not exist.")

            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch page: {link}, Error: {e}")

def scrape_episodes_from_season(session, season_link, folder_path, title, combined_script_path):
    try:
        response = session.get(season_link, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        episode_links = []
        for episode in soup.find_all('a', href=re.compile(r'view_episode_scripts\.php\?tv-show=')):
            episode_links.append(episode['href'])

        if not episode_links:
            print("No episode links found for this season.")
            return

        for episode_number, episode_url in enumerate(episode_links, 1):
            episode_url = f"https://www.springfieldspringfield.co.uk/{episode_url}"
            print(f"Fetching: {episode_url}")
            scrape_episode(session, episode_url, combined_script_path, title, episode_number)

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch season page: {season_link}, Error: {e}")

def scrape_episode(session, episode_url, combined_script_path, title, episode_number):
    try:
        response = session.get(episode_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        script = soup.find('div', class_='scrolling-script-container')
        episode_title = soup.find('h3')

        if script:
            script_text = script.get_text(separator="\n").strip()
            cleaned_script_lines = [
                line.lstrip() for line in script_text.split("\n")
            ]
            cleaned_script_text = "\n".join(cleaned_script_lines)

            episode_title_text = episode_title.get_text(strip=True) if episode_title else f"Episode {episode_number}"

            with open(combined_script_path, 'a', encoding='utf-8') as file:
                file.write(f"\n\n{'='*50}\n")
                file.write(f"{episode_title_text}\n")
                file.write(f"{'='*50}\n")
                file.write(cleaned_script_text)
                print(f"Successfully saved to combined file: {combined_script_path}")
        else:
            print(f"No script found: {episode_url}, this episode may not exist.")

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch episode page: {episode_url}, Error: {e}")

if __name__ == "__main__":
    user_link = input("Enter the link for the TV show or movie: ")
    scrape_scripts(user_link)
