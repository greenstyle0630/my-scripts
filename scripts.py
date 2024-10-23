import os
import requests
from bs4 import BeautifulSoup
import re

def scrape_scripts(link):
    folder_name = ""
    title = ""

    # 提取电视剧名称和季数或电影名称
    title_match = re.search(r'tv-show=([\w-]+)', link)
    movie_match = re.search(r'movie=([\w-]+)', link)

    if title_match:
        title = title_match.group(1).replace('-', '_').title()
        season_match = re.search(r'season=(\d+)', link)  # 获取季数
        if season_match:
            season_number = int(season_match.group(1))
            folder_name = f"{title}_第{season_number}季"
        else:
            folder_name = title  # 没有季数的情况下使用标题
    elif movie_match:
        title = movie_match.group(1).replace('-', '_').title()
        folder_name = title
    else:
        print("链接格式不正确，请提供有效的电视剧或电影链接。")
        return

    # 创建文件夹
    current_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(current_dir, folder_name)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # 尝试抓取剧本内容
    if 'episode_scripts' in link:  # 如果是剧集链接
        scrape_episodes_from_season(link, folder_path, title)
    else:  # 如果是季或电影链接
        try:
            response = requests.get(link)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 找到所有的集链接
            episode_links = []
            if title_match:  # 处理电视剧
                for episode in soup.find_all('a', href=re.compile(r'view_episode_scripts\.php\?tv-show=')):
                    episode_links.append(episode['href'])

                if not episode_links:
                    print("没有找到该季的剧集链接。")
                    return

                # 抓取每一集的剧本
                for episode_url in episode_links:
                    episode_url = f"https://www.springfieldspringfield.co.uk/{episode_url}"
                    print(f"正在抓取：{episode_url}")
                    scrape_episode(episode_url, folder_path, title)

            elif movie_match:  # 处理电影
                # 电影链接直接抓取
                scrape_episode(link, folder_path, title)

            else:
                print("没有找到剧本内容：可能该剧集不存在。")

        except requests.exceptions.HTTPError as e:
            print(f"抓取页面失败：{link}，错误信息：{e}")
            return

def scrape_episodes_from_season(season_link, folder_path, title):
    try:
        response = requests.get(season_link)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 找到所有的集链接
        episode_links = []
        for episode in soup.find_all('a', href=re.compile(r'view_episode_scripts\.php\?tv-show=')):
            episode_links.append(episode['href'])

        if not episode_links:
            print("没有找到该季的剧集链接。")
            return

        # 抓取每一集的剧本
        for episode_url in episode_links:
            episode_url = f"https://www.springfieldspringfield.co.uk/{episode_url}"
            print(f"正在抓取：{episode_url}")
            scrape_episode(episode_url, folder_path, title)

    except requests.exceptions.HTTPError as e:
        print(f"抓取季页面失败：{season_link}，错误信息：{e}")

def scrape_episode(episode_url, folder_path, title):
    try:
        response = requests.get(episode_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        script = soup.find('div', class_='scrolling-script-container')

        if script:
            script_text = script.get_text(separator="\n")
            filename = os.path.join(folder_path, f"{title}.txt") if 'movie=' in episode_url else os.path.join(folder_path, f"{os.path.basename(episode_url)}.txt")
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(script_text)
            print(f"成功保存：{filename}")

        else:
            print(f"没有找到剧本内容：{episode_url}，可能该集不存在。")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"集页面不存在：{episode_url}，可能已经抓取完所有集。")
        else:
            print(f"抓取集页面失败：{episode_url}，错误信息：{e}")

if __name__ == "__main__":
    user_link = input("请输入电视剧集或电影链接：")
    scrape_scripts(user_link)
