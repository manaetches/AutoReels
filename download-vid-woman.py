import requests
from bs4 import BeautifulSoup
import os

input_file = r"C:\xampp\htdocs\autoVideoPosts\reels-dev\video_links.txt"
output_dir = r"D:\reels-dev\mixkit\women"
os.makedirs(output_dir, exist_ok=True)

with open(input_file, "r", encoding="utf-8") as f:
    links = [line.strip() for line in f if line.strip()]

for idx, page_url in enumerate(links, 1):
    print(f"[{idx}/{len(links)}] Fetching: {page_url}")
    try:
        resp = requests.get(page_url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        video_tag = soup.find("video", class_="video-player__viewer")
        if not video_tag or not video_tag.get("src"):
            print("  No video src found.")
            continue
        video_url = video_tag["src"]
        filename = os.path.join(output_dir, os.path.basename(video_url))
        print(f"  Downloading: {video_url} -> {filename}")
        with requests.get(video_url, stream=True, timeout=30) as vid_resp:
            vid_resp.raise_for_status()
            with open(filename, "wb") as out_f:
                for chunk in vid_resp.iter_content(chunk_size=8192):
                    if chunk:
                        out_f.write(chunk)
        print("  Done.")
    except Exception as e:
        print(f"  Error: {e}")